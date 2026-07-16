# Разработка workflow-container

## Содержание
- [1. Назначение и краткая модель](#1-назначение-и-краткая-модель)
  - [1.1. Область действия](#11-область-действия)
  - [1.2. Сквозной путь данных](#12-сквозной-путь-данных)
  - [1.3. Основные термины](#13-основные-термины)
- [2. Архитектура экосистемы](#2-архитектура-экосистемы)
  - [2.1. Владельцы ответственности](#21-владельцы-ответственности)
  - [2.2. Направление зависимостей](#22-направление-зависимостей)
  - [2.3. Исходные контракты и версии](#23-исходные-контракты-и-версии)
  - [2.4. Публичный вход и форма настроек](#24-публичный-вход-и-форма-настроек)
  - [2.5. Миграция публичного входа](#25-миграция-публичного-входа)
- [3. Программная модель](#3-программная-модель)
  - [3.1. Протоколы типов](#31-протоколы-типов)
  - [3.2. Контексты выполнения и состояние Codex](#32-контексты-выполнения-и-состояние-codex)
  - [3.3. Иерархия классов](#33-иерархия-классов)
  - [3.4. Граница DBOS](#34-граница-dbos)
- [4. Файлы и передача данных](#4-файлы-и-передача-данных)
  - [4.1. Дерево экземпляров](#41-дерево-экземпляров)
  - [4.2. Стандартные файлы](#42-стандартные-файлы)
  - [4.3. Межшаговая передача](#43-межшаговая-передача)
  - [4.4. Объявленные артефакты](#44-объявленные-артефакты)
  - [4.5. Инкрементальные данные](#45-инкрементальные-данные)
- [5. Выполнение и восстановление](#5-выполнение-и-восстановление)
  - [5.1. Жизненный цикл workflow](#51-жизненный-цикл-workflow)
  - [5.2. Детерминированный шаг](#52-детерминированный-шаг)
  - [5.3. FSM шага Codex](#53-fsm-шага-codex)
  - [5.4. Маршрутизация prompt](#54-маршрутизация-prompt)
  - [5.5. Результат проверки](#55-результат-проверки)
  - [5.6. Классификация ошибок и повторов](#56-классификация-ошибок-и-повторов)
  - [5.7. Атомарная публикация и восстановление](#57-атомарная-публикация-и-восстановление)
- [6. Разработка конкретного контейнера](#6-разработка-конкретного-контейнера)
  - [6.1. Минимальный стабильный контракт](#61-минимальный-стабильный-контракт)
  - [6.2. Результат workflow](#62-результат-workflow)
  - [6.3. Правила prompt](#63-правила-prompt)
  - [6.4. Механическая и семантическая проверка](#64-механическая-и-семантическая-проверка)
  - [6.5. Полный пример простого workflow](#65-полный-пример-простого-workflow)
  - [6.6. Минимальные требования к коду](#66-минимальные-требования-к-коду)
- [7. Среда выполнения](#7-среда-выполнения)
  - [7.1. Контейнер, секреты и writeback](#71-контейнер-секреты-и-writeback)
  - [7.2. Граница Codex](#72-граница-codex)
  - [7.3. Browser runtime](#73-browser-runtime)
  - [7.4. Материализация внешних артефактов](#74-материализация-внешних-артефактов)
- [8. Проверка реализации](#8-проверка-реализации)
- [Приложение A. Публичные интерфейсы](#приложение-a-публичные-интерфейсы)
- [Приложение B. Структура workflow-container-runtime](#приложение-b-структура-workflow-container-runtime)

## 1. Назначение и краткая модель

### 1.1. Область действия
Этот документ является единым нормативным контрактом разработки workflow-container. Он определяет каноническое устройство исходного кода workflow, публичные типы и классы, устойчивые файлы, передачу данных между шагами, проверку результата, повторы, восстановление и границы контейнера.

Код, данные и фактическое поведение всех связанных проектов должны соответствовать этой модели. Сохранение старого API рядом с каноническим не считается соответствием и допускается только при явно согласованной поэтапной миграции.

Канонический путь документа в установленном plugin: `references/workflow-container-authoring.md`. Конкретный контейнер может ссылаться на него из `AGENTS.md` и проектной документации, но не импортирует `workflow-container-tools` и не требует его CLI во время выполнения.

Первые пять глав объясняют систему в порядке выполнения. Шестая глава показывает, как реализовать конкретный контейнер. Седьмая фиксирует инфраструктурные границы. Приложения содержат точные интерфейсы и физическую структуру общего runtime-пакета.

### 1.2. Сквозной путь данных
Конкретная строгая модель `WorkflowInputT` является единственным владельцем формы публичного входа. Из нее генерируется `input.schema.json`, а UI, input skill, API платформы и контейнер работают с одним полным JSON-объектом без промежуточного settings payload.

Настройка и запуск проходят через следующую цепочку:

```text
WorkflowInputT.model_json_schema()
  -> input.schema.json выбранной WorkflowSourceVersion
  -> полная форма Workflow
  -> Workflow.workflow_input_json
  -> полная редактируемая копия для WorkflowRun
  -> WorkflowRun.workflow_input_json
  -> WorkflowInputT
  -> workflow/input.json
  -> оркестрация в @DBOS.workflow
       -> метод-обертка с @DBOS.step
            -> InputSourceT
            -> WorkflowStepBase.input_build(...)
            -> InputT
            -> step/input.json
            -> действие шага
            -> ResultT
            -> step/result.json
            -> механическая проверка
            -> обязательная семантическая проверка для шага Codex
            -> step/verification.json
       -> успешный ResultT как возврат метода DBOS step
  -> WorkflowResultT
  -> workflow/result.json
  -> workflow/verification.json
  -> граница платформы
```

Здесь есть четыре разных роли:

1. `WorkflowInputT` является публичным входом всего workflow и содержит `request` и полный `config`.
2. `InputSourceT` собирает публичные зависимости конкретного шага в памяти процесса.
3. `InputT` является неизменяемым публичным входом одного шага и записывается в `input.json` этого шага.
4. `ResultT` является публичным выходом шага. Следующий шаг получает его через возврат метода DBOS step, а не читает внутреннее состояние предыдущего шага.

`Workflow.workflow_input_json`, `WorkflowRun.workflow_input_json` и workflow `input.json` являются полными снимками, а не patch или override maps. Schema defaults используются для первоначального заполнения формы, но все значения материализуются до сохранения. Runtime не объединяет слои конфигурации и не добавляет отсутствующие настройки.

Главный файловый инвариант: `input.json` является публичным входом владельца, `result.json` является его публичным выходом, `verification.json` сообщает, принят ли этот выход, `state.json` хранит только внутреннюю FSM и скалярные контрольные точки, а необязательный `state.sqlite3` хранит текущие изменяемые предметные строки и становится публичным только как явно объявленный артефакт.

### 1.3. Основные термины
| Термин | Значение |
| --- | --- |
| Запуск workflow (`Workflow run`) | Один устойчивый вызов конкретного DBOS workflow с одним `WorkflowInputT` и одним `WorkflowResultT`. |
| Настройки workflow (`Workflow config`) | Полный строгий объект `config` внутри `WorkflowInputT`: общая пользовательская инструкция, закрытый `step_map` и конкретные настройки всего workflow. |
| Карта настроек шагов (`step_map`) | Закрытый Pydantic-объект с одним полем для каждого реально настраиваемого шага; произвольным словарем не является. |
| Schema публичного входа (`input.schema.json`) | Версионируемая JSON Schema, сгенерированная из точного `WorkflowInputT` и используемая UI, input skill и платформенной validation boundary. |
| Экземпляр workflow (`Workflow instance`) | Один узел дерева результатов. Корневой и каждый дочерний workflow имеют разные каталоги экземпляров. |
| Шаг workflow (`Workflow step`) | Одна устойчивая граница побочного эффекта, выполняемая методом с `@DBOS.step`. У вызова шага есть один каталог экземпляра и один публичный результат. |
| Шаг Codex (`Codex-backed step`) | Шаг, в котором общий runtime выполняет одну или несколько попыток Codex. |
| Попытка Codex (`Codex attempt`) | Один цикл: действие Codex, построение результата, механическая проверка и семантическая проверка. Действие и проверка являются фазами одной попытки, а не отдельными DBOS steps. |
| Ключ шага (`step_key`) | Стабильный ключ реализации шага и его шаблонов prompt. Ключ действия имеет форму `{object}_{action}`, где `action` является глаголом; ключ проверки равен ключу действия с суффиксом `_verify`. |
| Публичный результат | Строго типизированный объект, записанный в `result.json`. Последующие шаги могут принять его только вместе с успешным `verification.json`. |
| Внутреннее состояние | `state.json` и необъявленный `state.sqlite3` текущего экземпляра. Другие workflow и шаги их не читают. |
| Объявленный артефакт | Созданный или материализованный файл, публичная ссылка на который содержится в текущем `result.json`. |
| Ссылка на артефакт | Путь относительно корня результатов. Физический путь записи и публичная ссылка имеют разные роли. |

Термин `stage` не является вторым названием шага в публичном API. Он допустим только при описании миграции старого API.

## 2. Архитектура экосистемы

### 2.1. Владельцы ответственности
| Проект | Ответственность |
| --- | --- |
| `workflow-control-center` | Платформа выполнения: schema snapshots версий, формы `Workflow` и `WorkflowRun`, их полные `workflow_input_json`, `DataSource`, `DataContainer`, доступные runtime-возможности, состояние запуска, run-local browser control endpoint, финализация и обратная запись входных данных. |
| `workflow-container-contract` | Независимые от среды выполнения модели и загрузчики `workflow.yaml`, `versions.yaml`, ограниченный профиль `input.schema.json`, input validation, определения input migrations, `WorkflowRunStatus`, `McpPlaywrightProfileWritebackPolicy` и общий `WorkflowResult` для границы с платформой. |
| `workflow-container-runtime` | Общая среда выполнения: базовые классы workflow и конфигураций, жизненный цикл, run-local concurrency и browser-profile lease, стандартные пути, атомарная запись JSON, SQLite current state, запуск Codex, рендеринг общих prompt, материализация и общие валидаторы. |
| `browser-vpn-runtime` | Запуск browser/VPN-процессов, run-local MCP profile router, каталоги и атомарные snapshots профилей, stealth, locale, viewport и сетевой namespace браузера. |
| Конкретный workflow-container | Предметные workflow и модели, конкретные шаги, валидаторы, шаблоны prompt и семантика предметных артефактов. |
| `workflow-container-tools` | Инструкции по разработке, семантический аудит, skill создания и миграции `input.json` и необязательный локальный CLI обнаружения соседних проектов. |

`WorkflowResultT` не управляет выходными контейнерами платформы, обратной записью или диагностическими списками. Эти данные принадлежат `workflow-control-center` и не добавляются в предметный результат ради удобства платформы.

### 2.2. Направление зависимостей
Конкретный контейнер зависит от закрепленных версий `workflow-container-contract` и `workflow-container-runtime`. Контейнер может обращаться к готовому browser runtime через переданный MCP URL, но не зависит от внутреннего устройства `browser-vpn-runtime`.

`workflow-container-runtime` не содержит предметных workflow, названий конкретных контейнеров или предметных prompt. `workflow-container-tools` не является зависимостью рабочего контейнера. Локальные копии кода общей среды выполнения, общих фрагментов prompt и генерируемых схем запрещены.

Общая зависимость переносится к нижнему владельцу только тогда, когда она нужна нескольким контейнерам и не содержит предметной семантики. Сам факт появления второго вызова не оправдывает новую общую абстракцию, если поведение не имеет устойчивого самостоятельного контракта.

### 2.3. Исходные контракты и версии
`workflow.yaml` загружается через `WorkflowDefinition.from_path(path)`, а `versions.yaml` через `WorkflowVersionDefinition.from_path(path)` из `workflow-container-contract`. Marketplace и контейнеры используют эти модели напрямую, без локальных зеркал, повторных загрузчиков и промежуточных re-export модулей.

`WorkflowDefinition.input_schema_path` является обязательным безопасным относительным путем к `input.schema.json` внутри workflow source. Абсолютный путь, `..` и выход за source root запрещены. `WorkflowInputSchema.from_path(path)` загружает schema, проверяет утвержденный профиль и валидирует JSON-объекты через один общий error contract.

`versions.yaml` является единственным реестром версии исходного контракта и входящих migration edges. Новая версия контракта обязательна при несовместимом изменении публичного входа workflow, публичного результата или межшагового результата.

Новая версия DBOS workflow обязательна, если изменение несовместимо с восстановлением уже существующего устойчивого запуска. Старые запуски продолжают выполняться старой версией. Поля совместимости, псевдонимы и модели, принимающие одновременно старую и новую форму, внутри новой версии запрещены.

Модели, сгенерированные JSON schemas, input migrations, входные контракты prompt, валидаторы, `workflow.yaml` и `versions.yaml` обновляются одной согласованной правкой.

### 2.4. Публичный вход и форма настроек
Каждый конкретный `WorkflowInputT` наследуется от общего `WorkflowInputBase[RequestT, WorkflowConfigT]` и имеет ровно два корневых поля:

```json
{
  "request": {},
  "config": {
    "instruction": "",
    "step_map": {}
  }
}
```

`request` описывает требуемый предметный результат. `config` описывает способ выполнения и имеет точный конкретный тип `Workflow...Config`, наследующий `WorkflowConfigBase`. `WorkflowConfigBase.instruction` является общей пользовательской инструкцией для всех шагов Codex. Конкретный config добавляет настройки всего workflow и один закрытый типизированный `step_map`.

Каждое поле `step_map` имеет имя, равное `step_key` соответствующего шага, и содержит точный `WorkflowStep...Config`. Шаг без публичных настроек отсутствует в `step_map`; пустые config-объекты ради симметрии запрещены. Обычный шаг Codex использует `WorkflowStepCodexConfigBase`; шаг Codex, экземпляры которого действительно независимы и допускают одновременное выполнение, использует `WorkflowStepCodexConcurrentConfigBase`. Конкретный config шага может добавлять собственные строгие поля.

`input.schema.json` генерируется непосредственно из конкретного `WorkflowInputT`, хранится рядом с `workflow.yaml` и фиксируется в git. Файл использует JSON Schema Draft 2020-12 и ограничивается объектами с `additionalProperties: false`, примитивными типами, типизированными массивами, enum, required/default, стандартными ограничениями, локальными `$defs`/`$ref`, title/description и `x-ui-control: textarea`. Nullable-поле может использовать `anyOf` только для одного точного типа и `{"type": "null"}`. Каждое редактируемое поле имеет понятные человеку `title` и `description`; многострочные инструкции помечаются `x-ui-control: textarea`. Произвольные dictionaries, другие формы `anyOf`, `oneOf` и условные schemas запрещены.

`Marketplace UI` перед построением формы один раз разрешает все локальные `$ref` в полном снимке schema с помощью готовой библиотеки, поддерживающей Draft 2020-12. Собственный код обхода цепочек `$ref` запрещен. Профиль `WorkflowInputSchema` допускает только локальные ациклические ссылки, поэтому UI не загружает внешние schema и не обрабатывает циклы. После разрешения ссылок полный input отдельно проверяется Draft 2020-12 validator.

Контекстные UI-аннотации редактируемого значения принадлежат узлу, который непосредственно объявляет это значение в `properties`. Такой узел может содержать локальный `$ref` вместе с `default`, `title`, `description` и `x-ui-control`; его аннотации имеют приоритет над общими аннотациями конечной schema из `$defs`. Промежуточный узел `$defs`, единственная роль которого состоит в перенаправлении ссылки, содержит только `$ref`. Поэтому длина reference chain не создает дополнительные уровни выбора default или подписей.

Schema `default` является только аннотацией начального значения формы: соответствующее поле concrete Pydantic model остается required. При публикации `WorkflowSourceVersion` marketplace проверяет schema и сохраняет неизменяемый `workflow_input_schema_json`. При создании `Workflow` UI строит форму из этого snapshot, материализует schema defaults и требует заполнить все остальные обязательные значения. `Workflow.workflow_input_json` хранит полный валидный объект.

При создании `WorkflowRun` UI начинает с полной копии `Workflow.workflow_input_json`, позволяет изменить `request` и `config`, повторно валидирует весь объект и сохраняет полный `WorkflowRun.workflow_input_json`. Patch, runtime merge и повторное применение generic defaults запрещены. При смене `WorkflowSourceVersion` текущий input должен быть явно приведен к новой schema до сохранения `Workflow`.

Формы `Workflow` и `WorkflowRun` импортируют и экспортируют только полный `input.json`. Импорт заменяет текущий объект формы и не выполняет merge. Frontend использует готовый Draft 2020-12 validator; backend повторяет validation через `workflow-container-contract`; контейнер окончательно разбирает тот же объект как concrete `WorkflowInputT` до начала DBOS workflow.

Контейнер разбирает внешний JSON через `model_validate_json(...)`, а сериализует JSON через `model_dump(mode="json")` или `model_dump_json(...)`. `model_validate(...)` и обычный конструктор используются только для уже типизированных Python-значений точной внутренней формы. Строгая модель не добавляет скрытые преобразования изменяемых JSON carriers во внутренние неизменяемые carriers только ради поддержки неправильного Python call site.

### 2.5. Миграция публичного входа
`WorkflowVersionDefinition.input_migration_list` загружается из `input_migrations` в `versions.yaml` и содержит `WorkflowInputMigrationDefinition` с `from_version`, `to_version` и безопасным относительным `script_path`. Соответствующий фрагмент файла выглядит так:

```yaml
version: 2.0.0
input_migrations:
  - from_version: 1.0.0
    to_version: 2.0.0
    script_path: migration/input/1.0.0_to_2.0.0.py
```

Переходы идут только к большей SemVer, не образуют циклов и не допускают дублирующий или неоднозначный путь между одной парой версий. Цепочка миграции состоит из последовательных объявленных edges и заканчивается точной версией target schema.

Migration script принадлежит конкретному workflow source и является исполняемым файлом по объявленному `script_path`. Он запускается из корня workflow source, читает один полный JSON object из `stdin`, пишет один полный JSON object в `stdout`, направляет diagnostics в `stderr`, не изменяет исходный файл, не использует сеть или внешнее состояние и детерминированно преобразует только объявленный version edge. Script имеет behavior tests для своей исходной и целевой формы.

Skill `workflow-container-input-create` работает в двух режимах. Для нового `Workflow` он начинает со schema defaults и последовательно запрашивает недостающие и изменяемые значения. Для `WorkflowRun` он начинает с сохраненного полного Workflow input и спрашивает только о желаемых изменениях. В обоих режимах skill задает один вопрос за раз, показывает текущие значения и ограничения, материализует полный объект и записывает файл только после успешной validation.

При миграции skill валидирует исходный input по исходной schema, находит единственную цепочку edges, последовательно запускает scripts, требует JSON object после каждого запуска и валидирует итог по target schema. Ошибка не изменяет исходный файл. Если цепочки нет, migration завершается как недоступная. После этого пользователь может отдельно создать новый target input: skill начинает с target-schema defaults, предлагает значения старого input только для совпадающих JSON paths, требует подтверждения каждого переноса и интерактивно заполняет остальные поля. Такой файл является заново созданным target input, а не результатом необъявленной миграции. Skill не запускает workflow и не изменяет marketplace напрямую; его файл применяется через полный import формы.

## 3. Программная модель

### 3.1. Протоколы типов
В этом документе протокол типа определяет пять свойств: базовый тип, владельца создания, способ хранения, потребителей и обязательные инварианты. Для моделей данных используется номинальный контракт строгой Pydantic-модели. Параллельный `typing.Protocol` с теми же полями не создается.

| Тип | База | Кто создает | Хранение | Кто читает |
| --- | --- | --- | --- | --- |
| `RequestT` | Строгая предметная модель Pydantic v2 | UI, input skill или вызывающий родительский workflow | Поле `request` полного workflow input | Конкретный workflow и его шаги |
| `WorkflowConfigT` | `WorkflowConfigBase` | UI или input skill по schema выбранной версии | Поле `config` полного workflow input | Конкретный workflow, scheduler и настраиваемые шаги |
| `WorkflowStepConfigT` | Точный config base соответствующего типа шага | Конкретный `WorkflowConfigT.step_map` | Одно поле закрытого `step_map` | Concrete workflow, runtime шага, action и verifier |
| `WorkflowInputT` | `WorkflowInputBase[RequestT, WorkflowConfigT]` | UI, input skill или родительский workflow | `workflow_input_json` платформы и `input.json` экземпляра workflow | `@DBOS.workflow`, дочерние workflow и методы-обертки DBOS steps |
| `WorkflowResultT` | `WorkflowResult` | Конкретный workflow после предметной оркестрации | `result.json` экземпляра workflow | Родительский workflow или платформа |
| `InputSourceT` | Строгая модель Pydantic v2 | Метод-обертка DBOS step из корневого входа и нужных успешных результатов | Не записывается отдельным файлом | Только `input_build(...)` текущего шага |
| `InputT` | Строгая модель Pydantic v2 | Конкретный шаг в `input_build(...)` | `input.json` экземпляра шага | Действие, валидатор, семантическая проверка и восстановление текущего шага |
| `ActionOutputT` | Строгая модель Pydantic v2 | Парсер структурированного ответа после действия Codex | Не является публичным файлом | Только `result_from_action_build(...)` текущей попытки |
| `ResultT` | Строгая модель Pydantic v2 | `result_build(...)` или `result_from_action_build(...)` | `result.json` экземпляра шага | Валидатор, семантическая проверка, метод-обертка DBOS step и следующие шаги |
| `WorkflowStepInvocationOutcome[ResultT]` | Строгая неизменяемая модель общей среды выполнения | `WorkflowStepCodexConcurrentBase` после завершения всей группы | Не сохраняется отдельным файлом | Асинхронный workflow, предметный контракт которого допускает частичный результат независимой группы |
| `VerificationDecision` | Строгая модель общей среды выполнения | Общий runtime из исхода механической проверки или semantic verifier | Не сохраняется как самостоятельный файл | Только общий runtime, который связывает решение с текущим результатом |
| `VerificationResult` | `VerificationDecision` с обязательными digest и номером ревизии результата | Общий runtime из `VerificationDecision`, точного текущего результата и его ревизии публикации | `verification.json` того же экземпляра | Механизм восстановления и вызывающий владелец |

Generic-параметры имеют следующие верхние границы:

```python
RequestT = TypeVar("RequestT", bound=BaseModel)
WorkflowConfigT = TypeVar("WorkflowConfigT", bound=WorkflowConfigBase)
WorkflowInputT = TypeVar("WorkflowInputT", bound=WorkflowInputBase)
WorkflowResultT = TypeVar("WorkflowResultT", bound=WorkflowResult)
InputSourceT = TypeVar("InputSourceT", bound=BaseModel)
InputT = TypeVar("InputT", bound=BaseModel)
ActionOutputT = TypeVar("ActionOutputT", bound=BaseModel)
ResultT = TypeVar("ResultT", bound=BaseModel)
WorkflowStepCodexConfigT = TypeVar("WorkflowStepCodexConfigT", bound=WorkflowStepCodexConfigBase)
WorkflowStepCodexConcurrentConfigT = TypeVar(
    "WorkflowStepCodexConcurrentConfigT",
    bound=WorkflowStepCodexConcurrentConfigBase,
)
```

Каждая предметная модель, используемая вместо `BaseModel`, должна включать `strict=True`, `extra="forbid"`, `validate_assignment=True` и `validate_default=True`. Общий `WorkflowResult` является открытой platform-facing базой: он строго проверяет собственные поля и сохраняет дополнительные поля конкретного результата, потому что runtime-neutral платформа не знает предметную модель контейнера. Каждый конкретный `WorkflowResultT` переопределяет `extra="forbid"`, поэтому producer по-прежнему имеет один закрытый точный контракт без второго envelope или adapter.

`InputSourceT` может зависеть от нуля, одного или нескольких более ранних публичных результатов. Если одного существующего объекта достаточно, он используется напрямую. Новая агрегирующая модель нужна только тогда, когда текущему шагу действительно требуется несколько независимых входов.

`InputT` включает существующие устойчивые объекты целиком или ссылки на их артефакты. Если шагу нужны настройки запуска, `InputT` содержит проверенный `workflow_input_path`, а не копию полного workflow config или его subset. Он не раскладывает те же данные в новый набор зеркальных полей. `ActionOutputT` содержит только данные, которыми владеет действие; неизменяемые идентификаторы и детерминированные пути достраиваются Python-кодом при создании `ResultT`.

`WorkflowStepInvocationOutcome[ResultT]` имеет ровно одно состояние: принятый `result` и пустой `validation_feedback_tuple` либо отсутствующий `result` и непустой неизменяемый `validation_feedback_tuple`. Он не хранит объект исключения, не заменяет предметный `ResultT` и не является вторым сохраняемым результатом шага.

### 3.2. Контексты выполнения и состояние Codex
`workflow-container-runtime` определяет строгие модели конфигурации запуска и среды выполнения:

| Модель | Назначение |
| --- | --- |
| `WorkflowConfigBase` | Общая пользовательская `instruction` всего workflow. Конкретный подкласс добавляет настройки workflow и закрытый `step_map`. |
| `WorkflowBrowserConfigBase` | `WorkflowConfigBase` с обязательной политикой обратной записи именованных Playwright-профилей для workflow, которое использует browser runtime. |
| `McpPlaywrightProfileWritebackPolicy` | Runtime-neutral условие выбора именованного профиля и статусов `WorkflowRun`, при которых платформа публикует его в исходный `DataSource`. |
| `WorkflowStepCodexConfigBase` | Полные run-owned `instruction`, model, reasoning, correction attempt limit и логическая конфигурация Playwright-профиля одного шага Codex. |
| `WorkflowStepCodexConcurrentConfigBase` | `WorkflowStepCodexConfigBase` с run-local `concurrency` для действительно независимых экземпляров одного шага. |
| `BrowserRuntimeCapability` | Run-local MCP router URL, immutable исходный snapshot профиля из текущего `DataSource` и platform control URL публикации writeback candidate. |
| `WorkflowRuntimeCapability` | Один строгий составной объект с явными типизированными полями возможностей. Отсутствующая возможность представлена `None`, а не пропущенным ключом универсального словаря. |
| `WorkflowExecutionContext` | Корень результатов, каталог текущего workflow и `WorkflowRuntimeCapability` текущего вызова. |
| `WorkflowStepExecutionContext` | Корень результатов, каталог текущего шага, путь к публичному workflow `input.json` и явно выбранный для этого шага `WorkflowRuntimeCapability`. |
| `CodexRunnerConfig` | Выбранные model и reasoning одного конкретного низкоуровневого вызова Codex. |
| `WorkflowStepCodexRuntimePolicy` | Source-owned политика низкоуровневых повторов и материализации, которая не является пользовательской настройкой запуска. |
| `WorkflowStepCodexState` | Номер текущей попытки и состояние FSM шага Codex. |

Контекст выполнения содержит только расположение экземпляра и `WorkflowRuntimeCapability`. Предметный вход, предыдущие результаты и инструкции prompt в него не входят. Универсальные словари возможностей запрещены: каждая возможность имеет отдельную типизированную модель среды выполнения и явное поле в составном объекте.

`WorkflowExecutionContext.for_step(step_instance_key=..., runtime_capability=...)` детерминированно создает `WorkflowStepExecutionContext` для дочернего шага и устанавливает `workflow_input_path` в result-relative путь текущего workflow `input.json`. Конкретный workflow передает только набор возможностей, объявленный для этого шага. Аналогичный метод общей среды выполнения создает контекст дочернего workflow. Эти операции не выполняют внешний ввод-вывод.

`WorkflowExecutionContext`, `WorkflowStepExecutionContext`, `WorkflowRuntimeCapability`, вложенные модели возможностей, `CodexRunnerConfig`, `WorkflowStepCodexRuntimePolicy` и все публичные config-модели неизменяемы после создания. `WorkflowStepCodexConfigBase` требует model из `gpt-5.6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`, reasoning из `low`, `medium`, `high`, `xhigh`, `max`, явный `correction_attempt_limit >= 0`, явную `instruction` и явные nullable-поля `mcp_playwright_profile` и `mcp_playwright_profile_source`. Пустая instruction является значением, а не отсутствующим полем. `correction_attempt_limit` считает только исправляющие попытки после первой action-попытки. `WorkflowStepCodexConcurrentConfigBase` дополнительно требует `concurrency >= 1`. Конфигурация является единственным владельцем детерминированного списка физических target-профилей: `mcp_playwright_profile_physical_list_get()` возвращает одиночный target, изолированные значения или фиксированные имена lanes, а validation до запуска workflow проверяет сгенерированные имена и отсутствие совпадения source с одним из них.

`CodexRunner` не закрепляет model и reasoning в конструкторе. `WorkflowStepCodexBase` получает exact config текущего вызова от concrete workflow и передает построенный `CodexRunnerConfig` в action и verifier. Оба вызова одной попытки используют одинаковые model и reasoning. Runtime не читает model из Codex user config и не применяет fallback. `correction_attempt_limit` ограничивает общую correction FSM; `WorkflowStepCodexRuntimePolicy.execution_retry_policy` отдельно ограничивает низкоуровневые инфраструктурные повторы одного вызова.

`concurrency` означает максимальное число одновременно выполняемых независимых экземпляров одного конкретного шага внутри текущего workflow run. Оно не управляет correction attempts, другими шагами, другими workflow runs, DBOS worker count или глобальной queue concurrency. Поле допускается только вместе с `WorkflowStepCodexConcurrentBase`; обычный `WorkflowStepCodexBase` его не принимает. Browser-backed scheduler назначает каждому worker lane отдельный физический профиль и ограничивает только одновременное использование одного такого профиля; общий MCP router URL не является ключом сериализации. Точная маршрутизация профилей принадлежит `7.3. Browser runtime`.

`WorkflowStepCodexState` является изменяемым устойчивым состоянием и допускает состояния `ready`, `result_published`, `verification_failed` и `completed`. Конкретный шаг может объявить точную производную модель со своими внутренними скалярными контрольными точками, но не переопределяет поля общей среды выполнения и не копирует предметные строки из SQLite. `state_build(execution_context, step_input)` обязан вернуть объект ровно объявленного `state_model`; подкласс или более широкая модель не принимаются. Общий runtime повторно проверяет точный снимок состояния перед записью и остается единственным владельцем переходов общих FSM-полей.

Общая среда выполнения предоставляет шесть явных сервисов с разными точками подключения:

| Сервис | Единственная ответственность |
| --- | --- |
| `JsonArtifactWriter` | Устойчивая атомарная публикация стандартных JSON-файлов. |
| `SqliteStateStore` | Транзакционное хранение текущих предметных строк в SQLite-таблицах, описанных точными Pydantic-моделями. |
| `ArtifactMaterializer` | Предварительная проверка и атомарное копирование настроенных внешних деревьев артефактов в каталог текущего шага. |
| `PromptRenderer` | Рендеринг одного названного Jinja2 template с защищенным namespace общих runtime-ресурсов. |
| `CodexRunner` | Один низкоуровневый вызов Codex с переданным per-call config, проверкой структурированного ответа и собственной политикой транспортных повторов. |
| `McpPlaywrightProfileRuntime` | Run-local маршрутизация browser profiles, lifecycle lease и вызов platform control endpoint для writeback candidate. |

`WorkflowBase` и `WorkflowStepBase` получают `JsonArtifactWriter`. `WorkflowStepCodexBase` дополнительно получает `ArtifactMaterializer`, `PromptRenderer`, `CodexRunner`, `McpPlaywrightProfileRuntime` и source-owned `WorkflowStepCodexRuntimePolicy`. Run-owned config не хранится в reusable instance field. `SqliteStateStore` получает только конкретный шаг, которому действительно нужно изменяемое предметное состояние; он не является обязательной зависимостью базовых классов. Все reusable services передаются в конструкторы явно и не создаются внутри `run(...)`. Полные сигнатуры находятся в `Приложение A. Публичные интерфейсы`.

### 3.3. Иерархия классов
Иерархия разделяет оркестрацию workflow и семантику одного шага:

```text
WorkflowBase[WorkflowInputT, WorkflowResultT]
  <- конкретный workflow + DBOSConfiguredInstance

WorkflowStepBase[InputSourceT, InputT, ResultT]
  <- WorkflowStepDeterministicBase[InputSourceT, InputT, ResultT]
       <- конкретный детерминированный шаг
  <- WorkflowStepCodexBase[InputSourceT, InputT, WorkflowStepCodexConfigT, ActionOutputT, ResultT]
       <- конкретный шаг Codex
       <- WorkflowStepCodexConcurrentBase[InputSourceT, InputT, WorkflowStepCodexConcurrentConfigT, ActionOutputT, ResultT]
            <- конкретный шаг Codex с независимыми concurrent invocations
```

`WorkflowBase` и `WorkflowStepBase` являются независимыми базовыми абстракциями. Шаг не является разновидностью workflow и не наследуется от `WorkflowBase`.

| Класс | Владеет | Конкретный подкласс реализует |
| --- | --- | --- |
| `WorkflowBase` | Публикация и восстановление стандартных файлов workflow через унаследованные асинхронные `final`-методы с `DBOS.run_step_async` | Асинхронный `run(...)` и, при наличии итоговых предметных инвариантов, `result_validate(...)` |
| `WorkflowStepBase` | Общая публикация `input.json`, `result.json`, `verification.json`, стандартные пути и восстановление | `input_build(...)`, при необходимости `artifact_prepare(...)` и `result_validate(...)` |
| `WorkflowStepDeterministicBase` | Финальный `run(...)` и полный жизненный цикл детерминированного шага | `result_build(...)` |
| `WorkflowStepCodexBase` | Попытки Codex, применение exact run config, механическая граница, семантическая проверка, повторы и FSM | `result_from_action_build(...)`, `step_key`, `config_model`, `action_output_model`, `result_model` и `state_model` |
| `WorkflowStepCodexConcurrentBase` | Детерминированный ограниченный запуск упорядоченного списка независимых вызовов через `DBOS.run_step_async`; `run_list(...)` возвращает только успешную группу, а `run_outcome_list(...)` сохраняет ошибку исчерпанной проверки каждого независимого элемента | Те же предметные hooks, что и `WorkflowStepCodexBase`; отдельный scheduler не реализуется |

Конкретный шаг не переопределяет финальные `run(...)`, `run_list(...)`, `run_outcome_list(...)` или внутреннюю диспетчеризацию жизненного цикла. Базовые классы содержат реальное общее поведение, а не только сигнатуры. Полные сигнатуры приведены в `Приложение A. Публичные интерфейсы`.

### 3.4. Граница DBOS
Точка входа workflow и предметные методы-обертки DBOS steps являются методами экземпляра конкретного класса с `@DBOS.dbos_class`. Класс workflow наследуется от `WorkflowBase` и `DBOSConfiguredInstance`.

Экземпляр DBOS class не хранит данные отдельного запуска. В `self` разрешены только неизменяемые и повторно используемые зависимости: объекты шагов, реестры, валидаторы, структура артефактов, средство рендеринга prompt, `CodexRunner` и другие сервисы. Вход workflow, текущие пути, состояние попытки и результаты передаются явными типизированными аргументами.

Метод с `@DBOS.workflow` выполняет только детерминированную оркестрацию: вызывает DBOS steps в воспроизводимом порядке и принимает решения по входу workflow и сохраненным возвратам шагов. Он не выполняет файловые, сетевые, браузерные или Codex-операции.

`WorkflowBase.input_write_step(...)` и `WorkflowBase.result_write_step(...)` являются асинхронными `final`-методами базового класса, которые внутри ожидают `DBOS.run_step_async`. Каждый concrete workflow реализует асинхронный метод `run(...)` и ожидает оба публикационных метода. Они не несут унаследованный декоратор `@DBOS.step`: DBOS связывает декорированные методы экземпляра с конкретным `@DBOS.dbos_class`, поэтому такой декоратор на базовом методе не является переносимой границей. Единая асинхронная граница поддерживает как последовательные, так и concurrent workflow без переключения между несовместимыми DBOS API.

Конкретный подкласс `WorkflowStepBase` является реализацией семантики без состояния отдельного запуска, а не владельцем метода DBOS. Метод с `@DBOS.step` синхронно вызывает `step.run(...)` и является устойчивой границей побочных эффектов. Все внешние операции внутри `step.run(...)` происходят в рамках этого вызова.

Для `WorkflowStepCodexConcurrentBase` конкретный асинхронный workflow передает упорядоченный список `WorkflowStepInvocation` непосредственно в один из двух унаследованных методов. `run_list(...)` применяется, когда ошибка любого элемента делает непригодной всю группу. `run_outcome_list(...)` применяется только тогда, когда вызовы предметно независимы и workflow может сохранить корректные результаты соседей вместе со структурированной ошибкой конкретного элемента. Агрегирующий метод workflow не получает `@DBOS.step`: устойчивые вызовы каждого элемента создает общий base через `DBOS.run_step_async`.

Оба метода проверяют принадлежность списка одному запуску и уникальность каталогов шагов, применяют одно ограничение параллельности, планируют и ожидают весь список и сохраняют порядок `invocation_list`. Если существует инфраструктурная или программная ошибка, оба метода поднимают первую такую ошибку в порядке списка, даже когда более ранний элемент завершился `StepResultValidationError`. Только при отсутствии других ошибок `run_outcome_list(...)` возвращает `WorkflowStepInvocationOutcome` для каждого `StepResultValidationError`, а `run_list(...)` повторно поднимает первый из них. Успешные вызовы остаются устойчиво сохраненными и при восстановлении не выполняют внешнюю работу повторно.

Автоматические повторы и классификация ошибок принадлежат `5.6. Классификация ошибок и повторов`. Методы-обертки `@DBOS.step` не добавляют третий автоматический retry-слой.

## 4. Файлы и передача данных

### 4.1. Дерево экземпляров
Каждый вызов workflow и шага имеет один детерминированный каталог. Общие функции построения путей являются единственным владельцем физической структуры каталогов.

```text
<result_dir>/
  workflow/
    <workflow_instance_key>/
      input.json
      result.json
      verification.json
      [state.json]
      [state.sqlite3]
      workflow/
        <child_workflow_instance_key>/
          ...
      step/
        <step_instance_key>/
          input.json
          result.json
          verification.json
          [state.json]
          [state.sqlite3]
          [declared artifacts]
```

Квадратные скобки обозначают необязательный физический файл или каталог. Необязательный файл отсутствует, а не заменяется альтернативным именем.

Ключ экземпляра выводится из устойчивого идентификатора workflow или предметного объекта. Позиция в списке, случайное имя и номер попытки не являются идентификатором экземпляра.

Независимо восстанавливаемый объект получает собственный дочерний узел, собственное внутреннее состояние или собственную строку SQLite с предметным ключом. Один общий статус не заменяет результаты независимых объектов.

### 4.2. Стандартные файлы
| Файл | Видимость | Содержание | Владелец записи |
| --- | --- | --- | --- |
| `input.json` | Публичный | Неизменяемый `WorkflowInputT` или `InputT` | Общий жизненный цикл |
| `result.json` | Публичный | Текущий `WorkflowResultT` или `ResultT` | Общий жизненный цикл |
| `verification.json` | Публичный | `VerificationResult`, digest и номер ревизии которого соответствуют текущей публикации `result.json` | Общий жизненный цикл |
| `state.json` | Внутренний | FSM и скалярные контрольные точки текущего владельца | Общий жизненный цикл и средство записи состояния |
| `state.sqlite3` | Внутренний или объявленный | Текущие изменяемые предметные строки, когда владельцу требуется инкрементальное состояние по предметным ключам | `SqliteStateStore` через разрешенную команду проекта или Python-владельца |

Workflow и детерминированный шаг создают `state.json` только при наличии реального возобновляемого состояния. Шаг Codex всегда создает `state.json`, потому что его попытки образуют FSM.

Prompt, действие Codex, семантическая проверка, предметный валидатор и конкретный метод-обертка DBOS не записывают стандартные файлы вручную.

### 4.3. Межшаговая передача
Единственной межшаговой передачей является успешный возврат DBOS step. Возвращаемый объект является тем же `ResultT`, который записан в `result.json` и принят успешным `verification.json` с совпадающими digest и номером ревизии.

Конкретный workflow строит вход следующего DBOS step из:

- исходного `WorkflowInputT`;
- публичных результатов любых необходимых более ранних шагов;
- публичных результатов дочерних workflow;
- ссылок на объявленные артефакты.

Из этого набора метод-обертка DBOS step создает один `InputSourceT`, а конкретный шаг создает `InputT` только через `input_build(execution_context, input_source)`. `execution_context` нужен только для построения объявленных физических путей текущего экземпляра; предметные зависимости остаются в `InputSourceT`.

Workflow `input.json` является единственным файловым владельцем полного `config`. Настраиваемый шаг сохраняет в своем `InputT` проверенный result-relative `workflow_input_path`, а concrete workflow перед вызовом шага явно выбирает exact config через обычный типизированный доступ `workflow_input.config.step_map.<step_key>`. Выбранный config передается отдельным DBOS-recorded аргументом runtime шага; step `input.json` не копирует полный workflow config или его subset.

Следующий шаг не читает `state.json` или внутреннюю SQLite state database предыдущего владельца. Текущий владелец может прочитать собственное внутреннее состояние, чтобы достроить публичный `ResultT`, но не передает путь или содержимое private state дальше. База, необходимая следующему владельцу, является объявленным артефактом и передается только по публичной ссылке из `ResultT`.

Родительский `result.json` включает нужный дочерний результат целиком или ссылку на него. Он не копирует отдельные поля дочернего результата в параллельную модель без самостоятельной публичной семантики.

### 4.4. Объявленные артефакты
Если идентичность артефакта известна до действия, `InputT` содержит его точный физический путь. Если предметная идентичность появляется только во время действия, проект объявляет один ограниченный корень артефактов и одну детерминированную функцию `identity -> relative path`; произвольный путь не становится частью результата действия.

Когда действию нужны и физический путь записи, и будущая публичная ссылка, конкретный `input_build(...)` создает один устойчивый `ArtifactWriteTarget`: точный физический путь внутри доступного дерева и готовую нормализованную ссылку относительно корня результатов. Во время действия producer записывает и повторно читает новый артефакт только по физическому пути; публичная ссылка становится путем чтения после материализации. `ResultT` переносит только публичную ссылку; предметный Python-код достраивает ее из того же `ArtifactWriteTarget`, а не из данных действия.

Механический валидатор проверяет:

- что физический путь и публичная ссылка находятся внутри разрешенных деревьев;
- что файл существует и имеет ожидаемый тип;
- что ссылка соответствует объявленному физическому пути;
- что результат не ссылается на внутреннее состояние или внешний необъявленный путь.

Артефакты шага создает его действие или детерминированная реализация. Внешнее дерево создает владеющая им внешняя система; действие Codex его не копирует.

Если Codex последовательно создает несколько независимо восстанавливаемых предметных артефактов и каждый артефакт должен стать валидным и устойчивым до перехода к следующему элементу, контейнер предоставляет узкую предметную producer-команду. Команда читает один JSON-объект из `stdin`, выбирает ровно один объявленный target из текущего `InputT` по устойчивому идентификатору элемента, проверяет точную Pydantic-модель и принадлежность target текущему экземпляру, затем атомарно публикует объект через `JsonArtifactWriter`. Prompt требует один вызов на элемент и запрещает прямую запись, JSON в аргументе shell-команды и группировку нескольких предметных объектов в одном вызове. Отдельный progress ledger не создается, если наличие валидных объявленных артефактов уже полностью выражает устойчивый прогресс.

Для идентичности, созданной действием, producer-команда принимает текущий `input.json`, проверенный предметный ключ и один объект, сама вычисляет разрешенный соседний target через проектный layout и атомарно публикует файл. Codex не передает физический или публичный путь. Producer повторно проверяет, что вычисленный target принадлежит объявленному корню, а предметный результат использует путь, вычисленный тем же layout. Имя файла не является источником идентичности и не разбирается обратно в предметные поля.

### 4.5. Инкрементальные данные
Изменяемая предметная коллекция хранится в SQLite, если элементы появляются по одному, обновляются по устойчивому предметному ключу и должны пережить повтор, перезапуск или переход между локальными действиями. Полная перезапись растущего JSON-массива и append-only цепочка ревизий поверх JSONL не являются допустимой заменой изменяемого хранилища.

Общий runtime владеет `SqliteStateStore`, `SqliteStateReader`, `SqliteStateTable` и `SqliteStateCommand`. Конкретный контейнер объявляет только строгие Pydantic-модели строк и статический реестр разрешенных таблиц. `SqliteStateTable` связывает имя SQLite-таблицы, точную модель строки и непустой упорядоченный набор полей первичного ключа. Одно поле задает обычный ключ, несколько полей задают составной первичный ключ. Каждое поле первичного ключа является обязательным скалярным полем точной модели. Runtime создает SQLite-столбцы из полей модели, сериализует составные значения каноническим JSON в их единственном столбце и повторно проверяет точную модель после чтения. Естественная составная идентичность хранится только как составной первичный ключ; отдельный склеенный столбец ключа запрещен. Предметные строки не копируются в отдельный JSON payload, `state.json` или `result.json`.

Изменяемая база состояния имеет стандартное соседнее имя `state.sqlite3` в каталоге текущего владельца. `SqliteStateStore` открывает ее через стандартный `sqlite3`, использует `journal_mode=DELETE` и `synchronous=FULL`, выполняет каждую запись в короткой транзакции, закрывает соединение после операции и предоставляет проверяемые `upsert`, `get`, `list`, `list_by_primary_key_prefix` и `delete`. WAL запрещен, потому что объявленный артефакт должен быть одним самодостаточным файлом без обязательных `-wal` и `-shm`. Запись идентифицируется предметным первичным ключом; общие `entity_id`, `record_id`, `revision_index`, ссылки на предшествующие записи и журнал предыдущих значений запрещены. Повтор одного `upsert` с тем же ключом и теми же значениями идемпотентен, а исправление обновляет текущую строку атомарно. Межтабличные предметные связи проверяет механический валидатор контейнера; общий runtime не вводит отдельный ORM или универсальную схему внешних ключей.

Для составного первичного ключа методы `get` и `delete` получают значения в порядке, объявленном `primary_key_field_name_tuple`. Runtime проверяет число значений и каждое значение по типу соответствующего поля модели до выполнения SQL. При открытии существующей базы runtime сверяет таблицу, столбцы и порядок полей первичного ключа с текущим статическим реестром и завершает восстановление ошибкой при несовместимой схеме.

`list_by_primary_key_prefix` принимает непустой ведущий префикс значений в том же порядке и возвращает совпавшие строки в полном порядке первичного ключа. Он не принимает пропуски между полями, произвольные условия или SQL. Эта операция является единственным общим поисковым сокращением поверх составного ключа; более сложная предметная выборка остается в Python-потребителе после проверенного чтения.

Codex не выполняет raw SQL и не выбирает путь базы данных, имя таблицы, модель или границу транзакции. `SqliteStateCommand` принимает текущий публичный `input.json`, вычисляет только соседний `state.sqlite3`, разрешает таблицу через переданный контейнером статический реестр и вызывает общий store. `upsert` читает из `stdin` одну полную строку; `get` и `delete` читают объект ровно со всеми полями первичного ключа; `list` возвращает все строки; `list-prefix` читает объект ровно с непустым ведущим набором полей первичного ключа. Каждый вход повторно проверяется по точной модели строки и объявленным полям ключа. Команды чтения возвращают один объект или компактный JSON-массив в порядке первичного ключа. Конкретный executable только передает статический реестр общему владельцу команды и не повторяет разбор аргументов, работу с SQLite или управление транзакциями.

Когда следующий шаг читает объявленную SQLite-базу предыдущего владельца, его узкая команда только для чтения принимает текущий `input.json` и предметный селектор, вычисляет точный путь базы только из проверенного `InputT` и использует `SqliteStateReader` как единственного владельца downstream-чтения. Она не принимает путь базы, не изменяет предыдущую базу и не сохраняет полученные строки в новый input, result или промежуточный артефакт. Предметный селектор и способ найти соответствующую публичную ссылку принадлежат конкретному контейнеру; разбор SQLite, проверка схемы и чтение остаются в общем runtime.

`state.json` хранит только runtime FSM и скалярные checkpoint-значения; предметные строки SQLite в нем отсутствуют. Пока базу читает только текущий владелец, она является внутренним state artifact. Если следующий workflow или шаг должен читать базу, `state.sqlite3` становится объявленным артефактом, а `result.json` переносит только ссылку на этот файл, не копируя строки.

Поскольку метод `@DBOS.workflow` не выполняет файловый ввод-вывод, `ResultT` может дополнительно содержать одно минимальное предметное решение, необходимое только для детерминированного выбора следующего шага. Такое поле допустимо лишь когда оно не копирует строки, причины, счетчики или метаданные базы, однозначно выводится текущим владельцем из проверенной базы и механически сверяется с ней. Детальные данные остаются только в SQLite.

После успешной проверки результата владелец больше не изменяет объявленную database. Downstream открывает ее только для чтения. Исправляющая попытка может менять базу только до публикации и успешной проверки результата этой попытки.

JSONL разрешен только для неизменяемого append-only event/log stream или неизменяемого fixture, где существующие записи никогда не исправляются и текущее состояние не вычисляется сворачиванием ревизий. Внешний протокольный event stream MAY сохранять принадлежащий протоколу формат JSONL. Workflow state, worklist, inventory, FSM и другие изменяемые предметные данные в JSONL запрещены.

Небольшая коллекция, создаваемая одним локальным действием и сразу публикуемая целиком, остается обычным атомарным JSON.

## 5. Выполнение и восстановление

### 5.1. Жизненный цикл workflow
Конкретный `WorkflowBase.run(...)` выполняет один порядок:

1. Ожидает унаследованный `input_write_step(...)`, который через `DBOS.run_step_async` проверяет и публикует workflow `input.json`.
2. Выполняет предметную оркестрацию только через дочерние workflow и методы с `@DBOS.step`.
3. Строит один `WorkflowResultT` из публичных результатов оркестрации.
4. Ожидает унаследованный `result_write_step(...)`, который через `DBOS.run_step_async` выполняет протокол публикации результата workflow и возвращает тот же `WorkflowResultT`.

`result_write_step(...)` всегда выполняет один порядок:

1. Проверяет точную модель `WorkflowResultT`; при уже существующем `result.json` требует равенство сохраненного и заново построенного результата, а при отсутствии файла атомарно публикует новый результат.
2. Возвращает сохраненный результат без повторной проверки только при существующем успешном `VerificationResult`, digest и номер ревизии которого соответствуют этому результату; для workflow номер ревизии всегда равен `1`.
3. Во всех остальных случаях вызывает `result_validate(...)` для текущего сохраненного результата.
4. Общий runtime создает transient `VerificationDecision`, вычисляет SHA-256 канонической JSON-сериализации текущего результата и атомарно публикует `VerificationResult` с `result_revision_index=1`.
5. При успешном решении возвращает тот же `WorkflowResultT`; при `WorkflowResultValidationError` сохраняет связанный ошибочный verdict и завершает DBOS step исключением.

Проверка уровня workflow является только механической проверкой итогового объекта. Отдельная семантическая проверка для workflow не запускается. Связанный `VerificationResult(status="failed", ...)` на этом уровне означает нарушение контракта результата и не запускает цикл исправления.

Ожидаемая предметная ошибка выражается корректным `WorkflowResultT` со статусом `failed`. Такой результат получает связанный успешный `VerificationResult`, если `result_validate(...)` подтверждает, что он точно описывает конечный предметный исход.

Неожиданное инфраструктурное исключение не маскируется искусственным предметным результатом. Workflow оставляет корневой набор файлов незавершенным, сохраняет уже завершенные дочерние результаты и завершает вызов исключением для восстановления DBOS.

### 5.2. Детерминированный шаг
`WorkflowStepDeterministicBase.run(...)` выполняет:

1. Проверку контекста выполнения и имеющегося состояния восстановления.
2. Построение `InputT` через `input_build(execution_context, input_source)`.
3. Атомарную публикацию неизменяемого `input.json`.
4. При существующем `result.json` загружает его и принимает без повторной проверки только при успешном verdict с совпадающими digest и `result_revision_index=1`.
5. При отсутствии `result.json` выполняет идемпотентный `artifact_prepare(...)`, строит `ResultT` через `result_build(...)` и атомарно публикует результат.
6. Выполняет `result_validate(...)` для существующего или нового текущего результата.
7. Общий runtime строит из решения проверки `VerificationResult` с `result_revision_index=1` и публикует `verification.json`.
8. При успехе возвращает тот же `ResultT`; при ошибке механической проверки завершает шаг исключением.

Ошибка механической проверки приводит к публикации связанного `VerificationResult(status="failed", ...)` и затем завершает шаг исключением. Детерминированный шаг не имеет внутреннего цикла повторов Codex.

### 5.3. FSM шага Codex
До первой попытки `WorkflowStepCodexBase.run(...)` проверяет exact concrete config, контекст и `workflow_input_path`, строит и публикует `InputT`, затем загружает публичный workflow input и требует точного равенства переданного config значению `config.step_map.<step_key>`. После этого runtime создает состояние через `state_build(execution_context, step_input)` либо восстанавливает существующее состояние и выполняет идемпотентный `artifact_prepare(...)`.

Одна попытка выполняется в таком порядке:

1. Общий runtime рендерит action prompt.
2. Codex возвращает структурированный ответ, который разбирается как точный `ActionOutputT`.
3. Общий runtime материализует настроенные внешние деревья артефактов.
4. Конкретный шаг строит `ResultT` через `result_from_action_build(...)`.
5. Общий runtime атомарно публикует новый `result.json`, не удаляя прежний verdict, и переводит FSM в `result_published`.
6. Общий runtime преобразует успешный возврат или `StepResultValidationError` из `result_validate(...)` в transient решение механической проверки.
7. После успешной механической проверки обязательно запускается семантическая проверка, которая возвращает `VerificationDecision` без digest.
8. Общий runtime вычисляет SHA-256 канонического текущего результата, строит `VerificationResult` с `result_revision_index`, равным текущему `attempt_index`, и атомарно публикует `verification.json`.
9. При успехе FSM переходит в `completed`, и шаг возвращает `ResultT`.
10. При исправимой ошибке FSM сохраняет `verification_failed`. Если `attempt_index - 1 < workflow_step_config.correction_attempt_limit`, runtime атомарно увеличивает `attempt_index`, переходит в `ready` и начинает следующую попытку. Иначе состояние остается `verification_failed`, и шаг завершается исключением.

| Текущее состояние | Условие | Следующее состояние |
| --- | --- | --- |
| `ready` | Опубликован новый кандидат результата | `result_published` |
| `result_published` | Опубликована ошибка механической или семантической проверки | `verification_failed` |
| `result_published` | Опубликован успешный `VerificationResult` с digest текущего результата и текущим `attempt_index` | `completed` |
| `verification_failed` | Зафиксирован переход к повтору | `ready` с увеличенным `attempt_index` |
| `verification_failed` | Лимит исчерпан | Завершение шага исключением |
| `completed` | Повторный вызов с тем же входом | Возврат уже принятого `ResultT` без внешней работы |

### 5.4. Маршрутизация prompt
Prompt получает только устойчивые пути текущего экземпляра:

| Фаза | Передаваемые пути |
| --- | --- |
| Первая попытка действия | `input_path` |
| Повторная попытка действия | `input_path`, `previous_attempt_result_path`, `previous_attempt_verification_path` |
| Семантическая проверка | `input_path`, `step_result_path` |

Все пути задаются относительно корня результатов текущего запуска. Абсолютные пути host и пути вне дерева результатов не входят в контракт prompt.

Текущий step `input.json` содержит `workflow_input_path`. Action и verifier переходят по нему к публичному workflow `input.json`, читают `config.instruction` и `config.step_map.<current_step_key>.instruction` и применяют один приоритет: неизменяемые runtime и domain contracts, затем instruction шага, затем instruction workflow. Обе пользовательские инструкции являются дополнительными и не ослабляют schema, механические инварианты или предметный contract.

Runtime-owned action и verification partials являются единственным владельцем этого routing. Domain templates описывают только предметную задачу и не повторяют способ чтения или приоритет инструкций.

Повторное действие читает предыдущий feedback из `verification.json`. Общий runtime не добавляет копию result JSON, отдельный список feedback, копию workflow config или предыдущее внутреннее состояние в prompt context. Все предметные зависимости находятся в текущем step `input.json`, публичном workflow `input.json` и объявленных артефактах.

### 5.5. Результат проверки
`VerificationDecision` является transient результатом одной механической или семантической проверки:

```json
{"status": "success", "feedback_list": []}
```

или:

```json
{"status": "failed", "feedback_list": ["Return a non-empty summary."]}
```

Успех всегда имеет пустой `feedback_list`. Ошибка всегда содержит в `feedback_list` конкретные действия для исправления. Механическая и семантическая ошибки используют эту модель; после механической ошибки семантическая проверка не запускается.

`VerificationResult` является сохраненной формой решения. Он содержит те же `status` и `feedback_list`, обязательный `result_digest` и обязательный `result_revision_index`. `result_digest` является 64 lowercase hex-символами SHA-256 канонической JSON-сериализации точной разобранной модели текущего `result.json`. Для канонизации runtime сериализует `model_dump(mode="json")` с отсортированными ключами и без необязательных пробелов, кодирует результат как UTF-8 и вычисляет SHA-256. Digest не зависит от форматирования исходного файла, порядка его ключей, состояния FSM или содержимого артефактов.

`result_revision_index` связывает verdict с одной публикацией результата. Для workflow и детерминированного шага он равен `1`; для шага Codex он равен `attempt_index`, которому принадлежит текущая публикация. Две попытки могут вернуть одинаковые байты `result.json`, но иметь разные артефакты или внутреннее состояние, поэтому совпадающего digest недостаточно для приема verdict предыдущей попытки.

| Поле сохраненного verdict | Содержание |
| --- | --- |
| `status` | Решение принять или отклонить связанный результат. |
| `feedback_list` | Пустой список при успехе или конкретные исправления при ошибке. |
| `result_digest` | Обязательный lowercase SHA-256 канонического текущего результата. |
| `result_revision_index` | Обязательный номер публикации: `1` для workflow и детерминированного шага, текущий `attempt_index` для шага Codex. |

Только общий runtime строит `VerificationResult` из `VerificationDecision`, текущего результата и его номера ревизии и записывает `verification.json`. Codex, prompt, предметный валидатор и конкретный шаг не вычисляют digest или revision и не возвращают сохраненный verdict. `VerificationResult.status` отвечает только на вопрос: «Можно ли принять эту публикацию `result.json`, определенную парой `result_digest` и `result_revision_index`?». Он не является предметным исходом и не заменяет `WorkflowResult.status`.

### 5.6. Классификация ошибок и повторов
| Событие | Владелец решения | Поведение |
| --- | --- | --- |
| Ошибка разбора структурированного ответа | Низкоуровневый `CodexRunner` | Повторяет вызов Codex по `CodexExecutionRetryPolicy`; `ResultT` еще не существует. |
| `StepResultValidationError` в шаге Codex | Механическая граница | Создает ошибочное решение; runtime связывает его с текущим результатом, публикует verdict и направляет попытку в цикл исправления Codex. |
| `StepResultValidationError` в детерминированном шаге | Механическая граница | Создает ошибочное решение; runtime связывает его с текущим результатом, публикует verdict и завершает шаг исключением без повторного действия. |
| Ошибка семантической проверки | Семантическая проверка | Возвращает `VerificationDecision` с конкретными действиями для исправления; runtime публикует связанный verdict и направляет попытку в цикл исправления Codex. |
| Исчерпан лимит попыток | `WorkflowStepCodexBase` | Завершает шаг исключением, сохраняя последние `VerificationResult(status="failed", ...)` и `WorkflowStepCodexState`. |
| Исчерпаны попытки исправления одного параллельного вызова | `WorkflowStepCodexConcurrentBase` | При отсутствии других ошибок `run_list(...)` повторно поднимает первый `StepResultValidationError`, а `run_outcome_list(...)` возвращает для каждого такого элемента отсутствующий `result` и точный непустой `validation_feedback_tuple`; любая инфраструктурная или программная ошибка имеет приоритет и пробрасывается отдельно. |
| `CodexExecutionError` после исчерпания низкоуровневых попыток | Граница `CodexRunner` | Пробрасывает исключение наружу; предметный workflow не превращает его в `error_list`. Сохраненные файлы позволяют вызывающей платформе явно инициировать восстановление. |
| Ошибка profile reset, route, candidate publication или синхронного writeback | `McpPlaywrightProfileRuntime` и platform control endpoint | Не превращает инфраструктурную ошибку в correction feedback; завершает DBOS step исключением. Recovery повторяет публикацию уже принятого результата до успешного возврата шага. |
| Ошибка файловой системы, конфигурации или материализации | Граница общей среды выполнения | Не превращает инфраструктурную ошибку в `feedback_list`; завершает текущий вызов исключением. |
| Несовпадающий input или противоречивое состояние | Граница восстановления | Завершает вызов явной ошибкой без молчаливого исправления. |
| Ожидаемая конечная предметная ошибка | Конкретный workflow | Возвращает валидный `WorkflowResultT` со статусом `failed`. |

Автоматических retry-механизмов два: низкоуровневый повтор вызова в `CodexRunner` и исправление результата в `WorkflowStepCodexBase`. DBOS обеспечивает durable history и replay при явно инициированном восстановлении, но методы-обертки шага не объявляют собственную автоматическую retry-политику.

### 5.7. Атомарная публикация и восстановление
Перед публикацией модели или вычислением digest общий runtime создает plain Python snapshot через `model_dump(mode="python")`, повторно проверяет его точным `type(value)` и использует только полученный канонический объект. Это закрывает обход `validate_assignment` через изменение вложенного списка или словаря на уже созданной модели. `JsonArtifactWriter`, `SqliteStateStore` и построение `VerificationResult` применяют один и тот же принцип.

`JsonArtifactWriter` пишет проверенный snapshot во временный путь рядом с целевым, выполняет `flush`, `fsync`, атомарную замену и синхронизацию каталога. Конкретные проекты не реализуют собственную запись стандартных файлов.

`input.json` неизменяем внутри одного каталога экземпляра. Повтор с эквивалентным проверенным input использует существующий файл. Другой input в том же каталоге является ошибкой идентичности. Отсутствующий `input.json` можно создать только в новом пустом экземпляре; если каталог уже содержит result, verdict, private state, diagnostics или предметные артефакты, runtime завершает восстановление ошибкой и не присваивает существующим данным новую входную identity.

Шаг Codex создает начальный `state.json` только до начала первой попытки, когда в каталоге существует лишь проверенный `input.json`. Если `state.json` отсутствует, но уже есть result, verdict, diagnostics или предметные артефакты, runtime не создает состояние с `attempt_index=1`: номер попытки и оставшийся budget больше нельзя однозначно восстановить, поэтому bundle считается противоречивым.

Общий runtime не удаляет прежний `verification.json` перед публикацией нового `result.json`. Старый verdict может временно сосуществовать с новой публикацией результата. Если содержимое результата изменилось, различается `result_digest`; если байты результата совпали, но изменилась попытка, артефакты или private state, различается `result_revision_index`. После validation и, когда требуется, semantic verification runtime атомарно заменяет `verification.json` новым verdict. Такая последовательность не создает delete-first окна.

Verdict считается актуальным только после строгого разбора `result.json` и `verification.json` и проверки `VerificationResult.is_bound_to(result, result_revision_index=...)`. Отсутствующий verdict или несовпадающий digest/revision означает, что текущая публикация еще не подтверждена.

При restart runtime использует следующую матрицу:

| Найденные данные | Действие |
| --- | --- |
| Совпадающий input, валидный result, успешный verification с совпадающими digest и revision | Для именованного browser profile повторить идемпотентный вызов candidate publication, затем вернуть существующий result без повторного action или verification. Для остальных шагов вернуть result без внешней работы. |
| `input.json` отсутствует, но в каталоге уже есть более поздние lifecycle-файлы или артефакты | Завершить восстановление ошибкой идентичности; не создавать новый input. |
| Input без result и состояние, допускающее выполнение действия | Продолжить выполнение по внутреннему состоянию и уже созданным артефактам. |
| Шаг Codex без `state.json`, но с более поздними lifecycle-файлами или артефактами | Завершить восстановление ошибкой противоречивого bundle; не сбрасывать `attempt_index` и budget. |
| Результат workflow без verdict или с verdict другой identity | DBOS детерминированно повторяет код оркестрации, но воспроизводит завершенные дочерние workflow и steps из durable history без повторной внешней работы. `result_write_step(...)` требует равенство заново построенного и сохраненного `WorkflowResultT`, повторяет `result_validate(...)` и публикует verdict с revision `1`. |
| Результат детерминированного шага без verdict или с verdict другой identity | Загрузить существующий `ResultT`, выполнить только `result_validate(...)`, опубликовать verdict с revision `1` и вернуть результат либо снова завершить шаг через `StepResultValidationError`. `artifact_prepare(...)`, `result_build(...)` и внешние действия не повторять. |
| Результат шага Codex без verdict или с verdict другой identity, состояние `result_published` | Проверить текущий результат и артефакты, повторить `result_validate(...)`, затем обязательную семантическую проверку и опубликовать verdict с текущим `attempt_index`. Действие Codex не повторять. |
| Состояние Codex `ready`, опубликованный result отличается от result предыдущего verdict | Согласовать FSM до `result_published`, проверить уже опубликованный результат и не повторять action, которое его создало. |
| Состояние Codex `ready`, байты result совпадают, а verdict принадлежит предыдущей revision | Сначала повторить validation и semantic verification текущих артефактов. Успех принимает результат и публикует verdict текущей revision; ошибка запускает action уже открытой текущей попытки без дополнительного увеличения `attempt_index`. |
| Связанный ошибочный verdict workflow | Повторно проверить уже опубликованный `WorkflowResultT` через `result_validate(...)`; при неизменной ошибке сохранить новый связанный ошибочный verdict и снова поднять `WorkflowResultValidationError`. Если текущий валидатор принимает результат, заменить verdict на связанный успешный и вернуть тот же результат. |
| Связанный ошибочный verdict детерминированного шага | Повторно проверить уже опубликованный `ResultT` через `result_validate(...)`; при неизменной ошибке сохранить новый связанный ошибочный verdict и снова поднять `StepResultValidationError`, не вызывая `artifact_prepare(...)`, `result_build(...)` или внешние действия. Если текущий валидатор принимает результат, заменить verdict на связанный успешный и вернуть тот же результат. |
| Связанный ошибочный verdict шага Codex и состояние `result_published` | Согласовать состояние до `verification_failed`. |
| Связанный ошибочный verdict шага Codex, состояние `verification_failed` и `attempt_index - 1 < correction_attempt_limit` | Один раз увеличить `attempt_index` и атомарно перейти в `ready`. |
| Связанный ошибочный verdict шага Codex и `attempt_index - 1 >= correction_attempt_limit` | Повторно завершить шаг исключением без изменения `attempt_index` и без нового действия Codex. |
| Связанный ошибочный verdict шага Codex и состояние `completed` | Завершить вызов ошибкой несогласованного состояния; завершенный шаг не может иметь связанный ошибочный verdict. |
| Состояние опережает отсутствующие стандартные файлы | Завершить вызов ошибкой несогласованного состояния. |
| Несовпадающий input, некорректный JSON или несовместимая SQLite schema/state database | Завершить вызов явной ошибкой восстановления. |

Стандартные файлы являются единственным источником истины для завершенных переходов публикации, но `result.json` и `verification.json` образуют принятую пару только при совпадающих digest и revision. Внутренний checkpoint FSM может отставать не более чем на одну атомарную публикацию и продвигается вперед только при однозначном соответствии стандартным файлам.

Workflow или DBOS step считается завершенным после устойчивой публикации полного набора восстановления: стандартных файлов, объявленных созданных артефактов, используемого внутреннего состояния, используемой SQLite state database и материализованных внешних файлов, необходимых для повторной validation или verification.

## 6. Разработка конкретного контейнера

### 6.1. Минимальный стабильный контракт
Одно смысловое понятие имеет одну минимальную стабильную модель на своей границе. Другие слои передают эту модель, вкладывают ее целиком, ссылаются на ее артефакт или вычисляют производное значение.

Полный `WorkflowInputT` является единственным владельцем request и run-owned config. Schema version, `Workflow`, `WorkflowRun`, workflow `input.json` и конкретные шаги используют один объект без settings envelope, patch model или локальных defaults. Точный config шага существует как поле конкретного `step_map`; workflow выбирает этот объект, но не преобразует его во вторую модель.

Разные роли не должны зеркалить одинаковые данные:

- result workflow описывает итог workflow;
- result шага описывает итог одного шага;
- типизированный input описывает вход текущего владельца;
- внутреннее состояние поддерживает восстановление того же владельца;
- объявленный артефакт хранит отдельные публичные данные;
- audit view вычисляется из стабильного источника.

`WorkflowStepInvocationOutcome` допустим только как временная модель передачи результата общей конкурентной группы. Он передает тот же принятый `ResultT` без копирования или точный `validation_feedback_tuple`; конкретный workflow преобразует этот список в свое существующее предметное поле ошибки и не сохраняет outcome как второй result или artifact.

Первый способ исправления неясной границы: удалить лишнее поле, объект, владельца, прокси или слой совместимости; переиспользовать существующую модель; либо перенести поведение к владельцу данных. Новая абстракция допускается только тогда, когда она устраняет реальное дублирование, создает одну стабильную границу или делает проверку и восстановление проще прямого решения.

После правки необходимо перечитать измененную и непосредственно затронутую границу. До передачи результата удаляются избыточные сохраненные данные, повторные каналы результата проверки, прокси-слои, переходные состояния, скопированный текст схемы, повторяющиеся инструкции prompt, построение межшагового результата внутри валидатора и неясное владение.

### 6.2. Результат workflow
Конкретный `WorkflowResultT` наследуется непосредственно от общего `WorkflowResult` из `workflow-container-contract`. Между ними не создается adapter с теми же полями.

Общий result содержит:

- `status: Literal["success", "failed"]`;
- `error_list: list[str]`;
- `warning_list: list[str]`.

`status="failed"` используется тогда и только тогда, когда `error_list` текущего workflow непустой. `error_list` содержит только ошибки, делающие результат этого workflow непригодным. Предупреждения, доказанное отсутствие данных, ошибки отдельных дочерних объектов и типизированные пробелы в полноте сами по себе не делают родительский результат ошибочным: они остаются в своих структурированных предметных полях. Частичный предметный результат является успешным, если предметный контракт разрешает такую полноту.

Свободное поле `message`, дублирующее ошибки, предупреждения или `status`, запрещено. Точка входа контейнера один раз сериализует итоговый `WorkflowResultT` через `model_dump(mode="json")`; платформа не строит вторую модель результата.

Имя с суффиксом `_json` обозначает сериализованный текст JSON. Валидированная модель использует имя модели, а совместимый с JSON словарь на внешней границе использует суффикс `_payload`.

### 6.3. Правила prompt
Prompt является исполняемым контрактом, а не набором общих советов. Сначала определяется роль текста, затем выбирается минимальная подходящая структура:

| Форма | Когда применяется |
| --- | --- |
| Contract | Входы, выходы, schemas, артефакты, инструменты, naming и владение. |
| FSM | Попытки, повторы, заблокированное состояние, отмена, восстановление и конечные переходы. |
| Workflow или Step Sequence | Линейная процедура без самостоятельной state machine. |
| Persistent State | Значимые данные, которые нужны после текущего локального действия. |
| Recovery | Известный вид ошибки с однозначным корректирующим действием. |

Это инструменты структуры, а не обязательные заголовки. Prompt содержит только те блоки, которые соответствуют его поведению. Несколько обязанностей разделяются на отдельные смысловые блоки или явную последовательность.

Значимая структура сохраняется на ближайшей стабильной границе сразу после создания, если она нужна семантической проверке, повтору, перезапуску, следующему шагу или внешнему потребителю. В памяти остаются только временные значения текущего локального действия.

Понятные человеку инструкции не хранятся в многострочных строках Python. Prompt действия является полным шаблоном Jinja2 `{step_key}.md.j2`, а prompt семантической проверки имеет имя `{step_key}_verify.md.j2`. Каждый `WorkflowStepCodexBase` обязан иметь оба шаблона; отключение или формальная пустая реализация семантической проверки запрещены. Детерминированный шаг не имеет этих шаблонов; общий runtime строит его `VerificationResult` из решения механической проверки. Общие фрагменты и system prompts принадлежат `workflow-container-runtime` и доступны только через защищенный префикс `runtime/`, включая имена `runtime/system/...`. Предметные шаблоны принадлежат конкретному контейнеру и используют имена без этого префикса. Project template не может перекрыть ресурс `runtime/...`.

Prompt не копирует JSON Schema из модели Pydantic и не пересказывает механические проверки. Нейтральные учебные примеры допустимы в этом документе; предметные примеры и правила принадлежат конкретному контейнеру.

### 6.4. Механическая и семантическая проверка
Pydantic отвечает за JSON Schema, строгие типы и запрет дополнительных полей.

У конкретного шага есть одна публичная механическая граница:

```python
result_validate(execution_context, step_input, result) -> None
```

Она проверяет межполевые инварианты, существование артефактов, нахождение их путей внутри разрешенного дерева и детерминированные отношения между `InputT` и `ResultT`. При исправимой ошибке она выбрасывает `StepResultValidationError` с конкретными инструкциями в `feedback_list`.

Механический валидатор:

- не пишет артефакты;
- не строит input следующего шага;
- не возвращает список ошибок;
- не повторяет JSON Schema модели Pydantic;
- не определяет смысловую корректность внешнего источника.

Семантическая проверка получает результат, уже прошедший разбор Pydantic и механическую проверку. Она проверяет смысл, согласованность текущих артефактов и, когда применимо, соответствие источнику и сохраненным доказательствам. Она возвращает только transient `VerificationDecision`, не вычисляет digest или revision, не пишет состояние или артефакты и не создает второй канал ошибки. Общий runtime связывает это решение с текущей публикацией результата и публикует `VerificationResult`.

### 6.5. Полный пример простого workflow
Пример показывает один workflow с одним настраиваемым шагом Codex. Он суммирует входной текст, не использует browser или дополнительные артефакты и показывает весь путь от schema до DBOS step. Имена учебных классов не являются частью публичного runtime API; сигнатуры базовых классов являются нормативными.

#### Модели
```python
from pathlib import Path
from typing import ClassVar

from dbos import DBOS, DBOSConfiguredInstance, pydantic_args_validator
from pydantic import BaseModel, ConfigDict, Field

from workflow_container_contract import WorkflowResult
from workflow_container_runtime.artifact.materializer import ArtifactMaterializationPolicy, ArtifactMaterializer
from workflow_container_runtime.artifact.writer import JsonArtifactWriter
from workflow_container_runtime.codex.runner import CodexRunner
from workflow_container_runtime.mcp_playwright_profile import McpPlaywrightProfileRuntime
from workflow_container_runtime.prompt.renderer import PromptRenderer
from workflow_container_runtime.retry import CodexExecutionRetryPolicy
from workflow_container_runtime.step.base import StepResultValidationError
from workflow_container_runtime.step.codex import (
    WorkflowStepCodexBase,
    WorkflowStepCodexConfigBase,
    WorkflowStepCodexRuntimePolicy,
    WorkflowStepCodexState,
)
from workflow_container_runtime.step.context import WorkflowStepExecutionContext
from workflow_container_runtime.workflow.base import WorkflowBase
from workflow_container_runtime.workflow.config import WorkflowConfigBase, WorkflowInputBase
from workflow_container_runtime.workflow.context import WorkflowExecutionContext


class ExampleModel(BaseModel):
    """Strict base model used only by this example."""

    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True, validate_default=True)


class TextSummaryRequest(ExampleModel):
    """Requested text-summary work."""

    text: str = Field(description="Text that the workflow must summarize.", title="Text")


class WorkflowStepTextSummarizeConfig(WorkflowStepCodexConfigBase):
    """Complete user-owned config of the summary step."""


class WorkflowTextSummaryStepConfigMap(ExampleModel):
    """Closed map of configurable steps in the workflow."""

    text_summarize: WorkflowStepTextSummarizeConfig = Field(
        description="Complete settings for the text-summarize step.",
        title="Text summarize",
    )


class WorkflowTextSummaryConfig(WorkflowConfigBase):
    """Complete user-owned config of the workflow."""

    step_map: WorkflowTextSummaryStepConfigMap = Field(
        description="Settings for every configurable step in this workflow.",
        title="Step settings",
    )


class WorkflowTextSummaryInput(WorkflowInputBase[TextSummaryRequest, WorkflowTextSummaryConfig]):
    """Canonical public input of the example workflow."""


class TextSummaryStepInput(ExampleModel):
    """Persisted public input of the Codex step."""

    request: TextSummaryRequest
    workflow_input_path: Path


class TextSummaryActionOutput(ExampleModel):
    """Data owned by the Codex action."""

    summary: str


class TextSummaryStepResult(ExampleModel):
    """Public result of the Codex step."""

    summary: str


class WorkflowTextSummaryResult(WorkflowResult):
    """Public result of the example workflow."""

    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True, validate_default=True)

    summary_result: TextSummaryStepResult
```

`WorkflowTextSummaryInput` является точной моделью и workflow `input.json`, и JSON в UI/API. `TextSummaryStepInput` вкладывает устойчивый `TextSummaryRequest` целиком, а config не копирует: для него хранится только проверенный путь к публичному workflow input. `WorkflowStepTextSummarizeConfig` не добавляет предметных полей, но он не пуст: все поля `WorkflowStepCodexConfigBase` обязательны.

Из `WorkflowTextSummaryInput.model_json_schema()` генерируется и фиксируется `input.schema.json`. `workflow.yaml` указывает на него напрямую:

```yaml
input_schema_path: input.schema.json
```

Полный вход одного запуска имеет следующий вид:

```json
{
  "request": {"text": "A long text to summarize."},
  "config": {
    "instruction": "Preserve technical terminology.",
    "step_map": {
      "text_summarize": {
        "instruction": "Use no more than three sentences.",
        "model": "gpt-5.6-terra",
        "mcp_playwright_profile": null,
        "mcp_playwright_profile_source": null,
        "reasoning_effort": "high",
        "correction_attempt_limit": 3
      }
    }
  }
}
```

#### Конкретный шаг
```python
class TextSummaryStep(
    WorkflowStepCodexBase[
        TextSummaryRequest,
        TextSummaryStepInput,
        WorkflowStepTextSummarizeConfig,
        TextSummaryActionOutput,
        TextSummaryStepResult,
    ]
):
    """Build one verified summary from workflow input."""

    action_output_model: ClassVar[type[TextSummaryActionOutput]] = TextSummaryActionOutput
    config_model: ClassVar[type[WorkflowStepTextSummarizeConfig]] = WorkflowStepTextSummarizeConfig
    result_model: ClassVar[type[TextSummaryStepResult]] = TextSummaryStepResult
    state_model: ClassVar[type[WorkflowStepCodexState]] = WorkflowStepCodexState
    step_key: ClassVar[str] = "text_summarize"

    def input_build(
        self,
        execution_context: WorkflowStepExecutionContext,
        input_source: TextSummaryRequest,
    ) -> TextSummaryStepInput:
        """Build the persisted step input from the public workflow input."""

        return TextSummaryStepInput(
            request=input_source,
            workflow_input_path=execution_context.workflow_input_path,
        )

    def result_from_action_build(
        self,
        execution_context: WorkflowStepExecutionContext,
        step_input: TextSummaryStepInput,
        action_output: TextSummaryActionOutput,
    ) -> TextSummaryStepResult:
        """Build the public step result from action-owned data."""

        return TextSummaryStepResult(summary=action_output.summary)

    def result_validate(
        self,
        execution_context: WorkflowStepExecutionContext,
        step_input: TextSummaryStepInput,
        result: TextSummaryStepResult,
    ) -> None:
        """Reject an empty summary before semantic verification."""

        if not result.summary.strip():
            raise StepResultValidationError(feedback_list=["Return a non-empty summary."])
```

`TextSummaryStep` наследует точный конструктор `WorkflowStepCodexBase`; дополнительных зависимостей у предметного шага нет.

#### DBOS workflow
```python
@DBOS.dbos_class("WorkflowTextSummary")
class WorkflowTextSummary(
    WorkflowBase[WorkflowTextSummaryInput, WorkflowTextSummaryResult],
    DBOSConfiguredInstance,
):
    """Orchestrate one text-summary step."""

    def __init__(
        self,
        *,
        artifact_writer: JsonArtifactWriter,
        instance_name: str,
        summary_step: TextSummaryStep,
    ) -> None:
        """Store the reusable step dependency."""

        WorkflowBase.__init__(self, artifact_writer=artifact_writer)
        DBOSConfiguredInstance.__init__(self, instance_name)
        self._summary_step = summary_step

    @DBOS.workflow(name="text_summary", validate_args=pydantic_args_validator)
    async def run(
        self,
        execution_context: WorkflowExecutionContext,
        workflow_input: WorkflowTextSummaryInput,
    ) -> WorkflowTextSummaryResult:
        """Publish input, run the domain step, and publish the workflow result."""

        await self.input_write_step(
            execution_context=execution_context,
            workflow_input=workflow_input,
        )
        summary_result = self.text_summarize_write_step(
            execution_context=execution_context.for_step(
                step_instance_key="text_summarize",
                runtime_capability=execution_context.runtime_capability,
            ),
            request=workflow_input.request,
            workflow_step_config=workflow_input.config.step_map.text_summarize,
        )
        workflow_result = WorkflowTextSummaryResult(
            status="success",
            error_list=[],
            warning_list=[],
            summary_result=summary_result,
        )
        return await self.result_write_step(
            execution_context=execution_context,
            workflow_input=workflow_input,
            workflow_result=workflow_result,
        )

    @DBOS.step(name="text_summarize_write_step")
    def text_summarize_write_step(
        self,
        execution_context: WorkflowStepExecutionContext,
        request: TextSummaryRequest,
        workflow_step_config: WorkflowStepTextSummarizeConfig,
    ) -> TextSummaryStepResult:
        """Execute the semantic step inside one durable DBOS boundary."""

        return self._summary_step.run(
            execution_context=execution_context,
            input_source=request,
            workflow_step_config=workflow_step_config,
        )
```

Метод workflow выполняет только оркестрацию. Он выбирает exact config обычным типизированным доступом и передает его в метод с `@DBOS.step`, поэтому DBOS сохраняет фактическую конфигурацию вызова. Внешняя работа происходит внутри `TextSummaryStep.run(...)`. `WorkflowTextSummaryResult` включает устойчивый `TextSummaryStepResult` целиком и не создает вторую форму данных сводки.

#### Сборка зависимостей
Корень сборки получает инфраструктурные сервисы от точки входа контейнера и один раз создает неизменяемые экземпляры шага и workflow:

```python
def workflow_text_summary_build(
    *,
    artifact_materializer: ArtifactMaterializer,
    artifact_writer: JsonArtifactWriter,
    codex_runner: CodexRunner,
    instance_name: str,
    mcp_playwright_profile_runtime: McpPlaywrightProfileRuntime,
    prompt_renderer: PromptRenderer,
) -> WorkflowTextSummary:
    """Build the configured example workflow and its step."""

    summary_step = TextSummaryStep(
        artifact_materializer=artifact_materializer,
        artifact_writer=artifact_writer,
        codex_runner=codex_runner,
        mcp_playwright_profile_runtime=mcp_playwright_profile_runtime,
        runtime_policy=WorkflowStepCodexRuntimePolicy(
            artifact_materialization_policy=ArtifactMaterializationPolicy(artifact_root_tuple=()),
            execution_retry_policy=CodexExecutionRetryPolicy(attempt_limit=2),
        ),
        prompt_renderer=prompt_renderer,
    )
    return WorkflowTextSummary(
        artifact_writer=artifact_writer,
        instance_name=instance_name,
        summary_step=summary_step,
    )
```

Пустой `artifact_root_tuple` явно отключает материализацию, потому что этому шагу не нужны внешние артефакты. Model, reasoning, instructions, correction limit и nullable profile config здесь отсутствуют: они приходят из конкретного `WorkflowTextSummaryInput`. Точка входа отдельно создает `WorkflowExecutionContext` из каталога запуска и разрешенных возможностей среды выполнения; эти данные не хранятся в `WorkflowTextSummary` или `TextSummaryStep`.

#### Prompt templates
`text_summarize.md.j2`:

```markdown
# Task
Produce a concise summary of `request.text`.

# Sequence
1. Identify the central claims in `request.text`.
2. Summarize only information present in that text.
```

`text_summarize_verify.md.j2`:

```markdown
# Verification
Accept the current result only when the summary is faithful to `request.text`, follows the applicable instructions, contains no invented facts, and preserves the central meaning.
```

#### Результирующее дерево
```text
<result_dir>/workflow/text_summary/
  input.json                         # WorkflowTextSummaryInput
  result.json                        # WorkflowTextSummaryResult
  verification.json                  # VerificationResult
  step/text_summarize/
    input.json                       # TextSummaryStepInput
    result.json                      # TextSummaryStepResult
    verification.json                # VerificationResult
    state.json                       # WorkflowStepCodexState
```

Следующий workflow или шаг получает `WorkflowTextSummaryResult` или `TextSummaryStepResult` через возврат DBOS. Он не читает `step/text_summarize/state.json`.

### 6.6. Минимальные требования к коду
Workflow-container projects используют Python 3.14, `Black` с `target-version = ["py314"]` и `line-length = 120`, а также `pytest`. Runtime package после изменения поведения Python дополнительно проходит `python -m compileall <package>`.

Публичный API, точки входа workflow, интерфейсы шагов, стабильные границы и нетривиальные модули имеют type annotations и docstrings, описывающие реальное поведение. Стабильные config, input, result, state и ссылки на артефакты являются строгими Pydantic v2 models. JSON schemas генерируются из моделей.

Импорты кода проекта находятся на уровне модуля. Локальные импорты внутри функций и методов, резервные импорты, динамические импорты кода проекта и отложенные ошибки отсутствующей зависимости в рабочем коде запрещены.

Рефакторинг оставляет код в окончательном состоянии. Слои совместимости, перенаправляющие псевдонимы, прокси-обертки, повторные фрагменты prompt, повторные сгенерированные схемы и локальные копии кода общей среды выполнения удаляются в той же согласованной правке.

Эти минимальные требования не переносят частные правила именования, ORM, production-баз данных и другие вкусовые ограничения закрытых проектов.

## 7. Среда выполнения

### 7.1. Контейнер, секреты и writeback
Private input монтируется только для чтения в `/input/.secret`. До запуска workflow контейнер копирует его в доступный для записи pod-local `/runtime/.secret` с корректными правами. Workflow и Codex используют только runtime copy; `CODEX_HOME` не указывает на read-only mount.

Процесс workflow, установка зависимостей, DBOS и Codex используют обычный сетевой путь. Только `vpn-egress` gateway владеет OpenVPN, `tun0` и его сетевым namespace. Playwright работает в отдельном namespace, обращается к gateway через SOCKS и предоставляет workflow готовый MCP URL.

Обратную запись выполняет владелец платформы только для объявленных изменяемых префиксов входа. Snapshot создается во временном соседнем каталоге и атомарно заменяет target; доступ к обоим путям заранее задается владельцем run-local volume и процессом browser runtime, поэтому snapshot API не принимает UID/GID и не меняет права после публикации. Каждая S3-публикация создает новую версию и новый manifest; текущей становится последняя успешно опубликованная версия. Между разными запусками не вводятся compare-and-swap, writer lease или искусственный conflict поверх существующих версий и manifest.

Docker Compose и Kubernetes реализуют одинаковые правила монтирования, сети, локальной копии внутри pod и обратной записи. Bind mount, пригодный только для разработки, или общий сетевой namespace VPN не является production-контрактом.

### 7.2. Граница Codex
Подпроцесс Codex внутри workflow container не включает собственный filesystem sandbox. Файловая граница задается контейнером или pod, смонтированными snapshots `DataSource` и доступными для записи выходными путями.

Отключение Codex filesystem sandbox не переносит Codex в сетевой путь browser/VPN.

### 7.3. Browser runtime
Workflow получает `BrowserRuntimeCapability` с run-local MCP router URL, browser-runtime-visible расположением immutable исходного snapshot профиля из текущего `DataSource` и run-local platform control URL для публикации writeback candidate. Платформа всегда материализует source snapshot как каталог: при отсутствии сохраненного профиля в `DataSource` он является пустым. Workflow не запускает `@playwright/mcp`, `npx`, OpenVPN или альтернативный browser/VPN launcher и не управляет browser flags, locale, timezone, viewport, физическими каталогами профилей или выбором package.

#### Логическая конфигурация профиля
`WorkflowStepCodexConfigBase.mcp_playwright_profile` задает логическое имя target-профиля, а `mcp_playwright_profile_source` при необходимости задает точное физическое имя уже завершенного run-local source-профиля. Source не расширяется по префиксу и не получает автоматически lane suffix. Оба значения являются идентификаторами, а не путями: они являются безопасными одиночными компонентами имени и не содержат path separators, traversal или query syntax. Source требует target и не может совпадать ни с одним физическим именем target. Отсутствующий target включает изолированный режим без именованного устойчивого профиля; при этом source также отсутствует.

Для обычного шага физическое имя равно target. Для `WorkflowStepCodexConcurrentBase` с `concurrency > 1` общий runtime создает фиксированные worker lanes `{target}-1` ... `{target}-N`; invocation с нулевым индексом `j` назначается lane `(j mod N) + 1`, а каждый worker последовательно выполняет свой список через `{target}-{i}`. Config validation запрещает source, совпадающий с любым именем этого набора. Correction attempts остаются на том же lane. Пользователь не передает отдельный список физических имен.

Каждый `WorkflowRun` получает отдельный browser runtime root, уже принадлежащий `workflow_run_id`, поэтому одинаковое логическое имя в разных запусках обозначает разные каталоги. Дополнительный profile namespace в config или capability запрещен. Browser runtime хранит физический target в `/runtime/mcp_playwright_profile/profile/<physical-profile>/`; это внутреннее детерминированное отображение логического имени, а не пользовательская настройка пути.

Физические target-профили и writeback candidate находятся в предоставленном платформой writable run-local runtime volume. Платформа восстанавливает этот volume для того же `WorkflowRun` до DBOS replay; он не является публичным `result.json`, объявленным предметным артефактом или входным `DataSource`. Только policy-controlled writeback переносит candidate обратно в исходный `DataSource`.

#### Маршрутизация и жизненный цикл
Run-local `McpPlaywrightProfileRuntime` удерживает exclusive lease target-профиля на весь `WorkflowStepCodexBase.run(...)`: action, semantic verification, correction attempts и публикацию writeback candidate. При reset router отдельно удерживает source только на время атомарного копирования и упорядочивает одновременно нужные profile locks детерминированно. Разные target-профили выполняются параллельно, даже когда инициализируются из одного source. Изолированные invocation ограничиваются только `concurrency` шага.

Action получает MCP route с `profile=<physical-profile>`. Если в config указан source, action route дополнительно содержит `profile_source=<source-profile>`. При начале новой MCP client session по такому route browser runtime завершает backend target, атомарно пересоздает target из source и запускает backend заново; поэтому reset выполняется при каждом низкоуровневом action-вызове: первой попытке, transport retry и correction attempt, но не повторяется для HTTP-запросов внутри одной MCP session. Отсутствующий explicit source является инфраструктурной ошибкой и не заменяется capability source. Verification использует тот же target без `profile_source`, поэтому подключается к тому же backend без reset. Если source не указан и target еще не существует, router один раз инициализирует его из immutable `BrowserRuntimeCapability.mcp_playwright_profile_source`; существующий target продолжается без повторной инициализации. Отсутствующий target передается router без параметра `profile`; общий unprofiled backend использует Playwright MCP isolated-session mode и не создает устойчивый именованный профиль. URL строит только `McpPlaywrightProfileRuntime` через структурированный URL API:

```text
<mcp_url>                                                   # isolated action or verification
<mcp_url>?profile=source-discover-1                         # named verification
<mcp_url>?profile=canonical-select&profile_source=profile-1 # named action with reset
```

Router лениво владеет одним внутренним Playwright MCP backend на каждый активный физический профиль. Именованный backend сохраняет текущую настройку shared browser context; action и verification одного lifecycle последовательно подключаются к нему под одним profile lease. Эта задача не меняет shared-context implementation. Workflow может рассчитывать на cookies, storage и устойчивый `userDataDir`, но не использует вкладки, текущий URL или другой in-memory page state как межшаговый handoff contract. Router завершает backend до reset или snapshot выбранного профиля; следующее обращение лениво запускает его снова с тем же `userDataDir`.

#### Writeback candidate
`WorkflowBrowserConfigBase.mcp_playwright_profile_writeback_policy` определяет writeback без скрытых defaults. `mcp_playwright_profile_name_prefix=""` разрешает любой именованный профиль; непустое значение допускает только физические имена, начинающиеся с этого case-sensitive префикса. Изолированные профили никогда не участвуют. Пустой `workflow_run_status_list` полностью отключает candidate и writeback. `created` не является допустимым условием; остальные значения принадлежат общему `WorkflowRunStatus`. Policy проверяет статус платформенного `WorkflowRun`, а не `VerificationResult.status` или предметный `WorkflowResult.status`: принятый `WorkflowResult(status="success")` переводит запуск в `done`; принятый `WorkflowResult(status="failed")` или необработанное исключение workflow переводит его в `failed`; `cancelled` устанавливает платформа при отмене до завершения workflow.

После успешной semantic verification именованного профиля общий runtime, не освобождая profile lease, выполняет `POST <mcp_playwright_profile_writeback_candidate_url>?profile=<physical-profile>` с пустым body и явным runtime-owned конечным положительным тайм-аутом. URL уже привязан платформой к текущему `WorkflowRun`, точному `DataSource` и изменяемому префиксу, из которого был материализован capability source; runtime не передает эти значения, policy или filesystem path повторно. Будущий run-local platform control endpoint проверяет сохраненную policy, в принадлежащей ему транзакции блокирует строку этого `DataSource` до обращения к browser router и для подходящего именованного профиля вызывает внутренний browser-router endpoint `POST /runtime/mcp-playwright-profile/writeback-candidate?profile=<physical-profile>` с пустым body. Browser router завершает backend выбранного профиля, атомарно заменяет `/runtime/mcp_playwright_profile/writeback_candidate/` его полным snapshot и возвращает `204`. Будущий platform control endpoint под той же блокировкой обходит candidate, выполняет S3 upload, публикует `DataArtifact` и `DataSourceManifest`, выполняет `commit` и только после этого возвращает внешний `204`; внутренние сервисы не выполняют `commit`, `rollback` и не открывают вложенную транзакцию. Другой HTTP status на любом участке является инфраструктурной ошибкой. Пустой список статусов или профиль, отфильтрованный по имени, дает успешный no-op без обращения к browser router. Candidate всегда один: последняя успешно завершенная подходящая invocation заменяет предыдущую. SQLite, реестр кандидатов, sequence number и сравнение содержимого для этого не нужны.

DBOS step считается успешно завершенным только после необходимого вызова candidate endpoint. `TimeoutError` и другие transport failures остаются инфраструктурными исключениями, освобождают profile lease при выходе из текущего вызова и не превращаются в correction feedback. При recovery уже принятого `result.json` общий runtime повторно получает тот же profile lease и повторяет этот идемпотентный вызов до возврата результата. Повтор может создать дополнительную S3 version при `working`; это допустимый replay, а не conflict.

Непустой `workflow_run_status_list` разрешает обновление candidate после каждой успешно проверенной подходящей invocation независимо от перечисленных терминальных статусов. Значение `working` дополнительно означает checkpoint: будущий platform endpoint синхронно записывает только что обновленный candidate в исходный `DataSource` до возврата из DBOS step. Терминальные `done`, `failed` и `cancelled` означают одну публикацию текущего candidate при соответствующем переходе статуса запуска. Если policy содержит и `working`, и терминальный статус, обе публикации выполняются как явно запрошенные версии.

Отсутствие candidate допустимо при отключенной policy, отсутствующей browser capability, использовании только изолированных профилей, отсутствии invocation с подходящим именованным профилем или до первого успешного подходящего invocation при `working`. Факт использования именованного профиля определяется существованием его каталога только под `/runtime/mcp_playwright_profile/profile/`; отдельный usage registry не создается. Терминальная финализация завершается ошибкой только тогда, когда текущий терминальный статус требует writeback, существует хотя бы один каталог физического профиля, подходящий под policy, но ни одна подходящая invocation не завершилась успешно и candidate не существует. Параллельные запуски публикуют обычные S3 versions и manifests по правилу last successful write wins.

Поисковые запросы выполняются через встроенный веб-поиск Codex. Браузерная среда выполнения используется для целевых страниц, навигации по сайту и сохранения браузерных доказательств, а не для публичных страниц результатов поисковой системы.

Browser-backed `ActionOutputT`, который открывает целевые URL, наследуется от `BrowserActionResult` общего runtime и возвращает `browsing_error_list: list[BrowsingError]`. Производный публичный `ResultT` сохраняет тот же список, чтобы сетевые ошибки оставались видимыми в `result.json`; следующий шаг получает весь стабильный `ResultT`, даже если использует только его предметные данные. Каждая видимая в браузере ошибка имеет точную форму `{url, error}`.

Браузерные инструменты пишут доказательства только в объявленные целевые каталоги. JavaScript внутри `page.evaluate` является чистым браузерным JavaScript: API Node.js, CommonJS, динамические импорты и доступ к локальной файловой системе запрещены.

Локальные артефакты читаются через файловую систему, а не браузерные инструменты с `file://`, `localhost` или loopback URL. Семантическая проверка читает разобранный JSON только через точную модель и не использует предполагаемые пути или хрупкие glob-скрипты.

### 7.4. Материализация внешних артефактов
`workflow-container-runtime` предоставляет независимую от источника политику материализации в виде упорядоченного неизменяемого кортежа корней артефактов. Пустой кортеж отключает материализацию.

Каждый корень политики является абсолютным путем или путем относительно `result_dir` и зеркалит дерево экземпляров запуска. Для текущего шага `ArtifactMaterializer` берет поддерево `<artifact_root>/<step_instance_dir relative to result_dir>` и работает по политике корней, не выбирая файлы по ссылкам из результата.

До первой записи materializer проверяет полное выбранное дерево: containment, отсутствие symlink и отсутствие пересечения с runtime-owned корневыми путями `input.json`, `result.json`, `state.json`, `state.sqlite3`, `verification.json` и `diagnostics/`. Одна ошибка отклоняет все дерево; безопасные соседние файлы не копируются частично. После успешной предварительной проверки каждый файл публикуется через временный соседний файл, `fsync`, атомарную замену и синхронизацию каталога, поэтому существующий target не проходит через видимое частично записанное состояние.

Материализованные файлы, необходимые для повторной validation или verification, входят в набор восстановления. Конкретный workflow, prompt и действие не реализуют материализацию повторно.

Корень сборки browser-backed шага явно создает `ArtifactMaterializationPolicy(artifact_root_tuple=(Path(".playwright-mcp/current"),))`, если этому шагу нужны браузерные доказательства. Пустой кортеж явно отключает материализацию. Имена политики и API `ArtifactMaterializer` остаются независимыми от источника.

## 8. Проверка реализации
Исполняемое поведение общего runtime проверяется автоматизированными behavior tests. Обязательное покрытие включает:

- публичные интерфейсы классов;
- генерацию `input.schema.json` из concrete `WorkflowInputT`, drift check и полный ограниченный schema profile;
- одинаковую validation semantics schema в frontend/backend boundary и concrete Pydantic parsing в контейнере;
- полные snapshots `Workflow.workflow_input_json` и `WorkflowRun.workflow_input_json` без patch/merge/default fallback;
- exact typed `step_map`, отсутствие пустых config entries и передачу выбранного config как DBOS-recorded argument;
- одинаковые per-call model/reasoning для action и verifier, явный correction limit и отсутствие constructor-owned run config;
- run-local concurrency только для `WorkflowStepCodexConcurrentBase`, соблюдение bound и исходного порядка результатов без изменения DBOS queue;
- фиксированные browser worker lanes, отдельный backend на активный именованный профиль, параллельность разных профилей, exclusive lease одного профиля на полный lifecycle шага и отсутствие сериализации по общему MCP router URL;
- unprofiled Playwright MCP isolated-session mode, однократную инициализацию target из immutable capability source, один reset из явного source в начале первой action-попытки, каждого transport retry и correction attempt, verification без reset и сохранение текущего shared-context режима именованных backend;
- применение `McpPlaywrightProfileWritebackPolicy`, атомарную замену единственного candidate, определение фактически использованных именованных профилей без отдельного реестра, синхронный `working` checkpoint, терминальный writeback, допустимые случаи отсутствия candidate и S3 last-write-wins без искусственного conflict;
- прямые и chained input migrations, отсутствие неоднозначной цепочки, неизменность source input при ошибке и final target-schema validation;
- жизненный цикл детерминированного шага;
- переходы FSM Codex;
- механические и семантические ошибки;
- повторную проверку точных snapshot перед JSON/SQLite publication и вычислением digest;
- атомарную публикацию, обязательные digest/revision и соответствие `result.json`/`verification.json`;
- восстановление после перезапуска;
- ошибки identity при отсутствующем input или состоянии уже начатого экземпляра;
- изоляцию внутреннего состояния;
- создание SQLite-таблиц из точных моделей, обычный и составной первичный ключ без отдельного склеенного столбца, проверяемые CRUD и чтение по ведущему префиксу ключа, детерминированный порядок строк, идемпотентный `upsert` и восстановление;
- producer для динамической идентичности выводит target только из проверенного ключа внутри объявленного root, не принимает путь действия и идемпотентно обрабатывает повтор того же объекта;
- containment артефактов;
- all-or-nothing материализацию без доступа к runtime-owned путям;
- защищенный `runtime/` namespace prompt resources;
- полный пример или эквивалентный integration path через конкретный workflow.

`workflow.yaml`, `versions.yaml` и `input.schema.json` проверяются загрузчиками и повторно используемыми checks из `workflow-container-contract`. Конкретные проекты вызывают эти checks для собственных файлов, проверяют равенство committed schema результату текущего `WorkflowInputT.model_json_schema()` и не копируют tests загрузчиков.

Семантика prompt и инструкций проверяется внимательным повторным чтением и `workflow-container-audit`. Тесты Pytest, которые проверяют наличие конкретных фраз, заголовков, примеров или расположение файлов инструкций, запрещены.

После изменения проверяются все разделы-владельцы этого документа, которые измененный артефакт реализует или на которые он опирается. Частичный пересказ не заменяет канонический контракт.

## Приложение A. Публичные интерфейсы
Этот раздел является точным API-контрактом. Основной текст объясняет назначение интерфейсов, но не переопределяет их сигнатуры.

`workflow-container-contract` владеет runtime-neutral статусами запуска и политикой browser-profile writeback:

```python
WorkflowRunStatus = Literal["created", "working", "done", "failed", "cancelled"]


class McpPlaywrightProfileWritebackPolicy(BaseModel):
    mcp_playwright_profile_name_prefix: str
    workflow_run_status_list: tuple[WorkflowRunStatus, ...]
```

Оба поля policy обязательны. Пустой `mcp_playwright_profile_name_prefix` означает отсутствие фильтра, а пустой `workflow_run_status_list` отключает writeback. JSON представляет статусы массивом, а валидированная модель хранит их неизменяемым `tuple` без повторов и `created`.

В следующих фрагментах используются эти стандартные импорты:

```python
from __future__ import annotations

from abc import abstractmethod
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import ClassVar, Generic, Literal, Self, TypeVar, final

from dbos import DBOS, pydantic_args_validator
from pydantic import BaseModel, Field

from workflow_container_contract import McpPlaywrightProfileWritebackPolicy, WorkflowResult
```

```python
WorkflowCodexModel = Literal["gpt-5.6-luna", "gpt-5.6-sol", "gpt-5.6-terra"]
WorkflowCodexReasoningEffort = Literal["low", "medium", "high", "xhigh", "max"]

RequestT = TypeVar("RequestT", bound=BaseModel)
WorkflowConfigT = TypeVar("WorkflowConfigT", bound="WorkflowConfigBase")
WorkflowInputT = TypeVar("WorkflowInputT", bound="WorkflowInputBase")
WorkflowResultT = TypeVar("WorkflowResultT", bound=WorkflowResult)
InputSourceT = TypeVar("InputSourceT", bound=BaseModel)
InputT = TypeVar("InputT", bound=BaseModel)
ActionOutputT = TypeVar("ActionOutputT", bound=BaseModel)
ResultT = TypeVar("ResultT", bound=BaseModel)
WorkflowStepCodexConfigT = TypeVar("WorkflowStepCodexConfigT", bound="WorkflowStepCodexConfigBase")
WorkflowStepCodexConcurrentConfigT = TypeVar(
    "WorkflowStepCodexConcurrentConfigT",
    bound="WorkflowStepCodexConcurrentConfigBase",
)


def state_database_path_get(instance_dir: Path) -> Path:
    ...


class ArtifactMaterializationPolicy(BaseModel):
    artifact_root_tuple: tuple[Path, ...]


class BrowserRuntimeCapability(BaseModel):
    mcp_playwright_profile_source: str
    mcp_playwright_profile_writeback_candidate_url: str
    mcp_url: str


class BrowsingError(BaseModel):
    error: str
    url: str


class BrowserActionResult(BaseModel):
    browsing_error_list: list[BrowsingError]


class CodexRunnerConfig(BaseModel):
    model: WorkflowCodexModel
    reasoning_effort: WorkflowCodexReasoningEffort


class CodexExecutionRetryPolicy(BaseModel):
    attempt_limit: int = Field(ge=1)


class WorkflowConfigBase(BaseModel):
    instruction: str = Field(
        description="Additional instruction applied to every Codex step in this workflow.",
        json_schema_extra={"default": "", "x-ui-control": "textarea"},
        title="Workflow instruction",
    )


class WorkflowBrowserConfigBase(WorkflowConfigBase):
    mcp_playwright_profile_writeback_policy: McpPlaywrightProfileWritebackPolicy


class WorkflowInputBase(BaseModel, Generic[RequestT, WorkflowConfigT]):
    config: WorkflowConfigT = Field(description="Complete settings for this run.", title="Configuration")
    request: RequestT = Field(description="Domain work requested from the workflow.", title="Request")


class WorkflowRuntimeCapability(BaseModel):
    browser: BrowserRuntimeCapability | None


class McpPlaywrightProfileRoute(BaseModel):
    action_runtime_capability: WorkflowRuntimeCapability
    mcp_playwright_profile: str | None
    verification_runtime_capability: WorkflowRuntimeCapability


class WorkflowStepCodexConfigBase(BaseModel):
    correction_attempt_limit: int = Field(
        description="Maximum correction attempts after the initial action attempt.",
        ge=0,
        json_schema_extra={"default": 3},
        title="Correction attempt limit",
    )
    instruction: str = Field(
        description="Additional instruction applied only to this step.",
        json_schema_extra={"default": "", "x-ui-control": "textarea"},
        title="Step instruction",
    )
    mcp_playwright_profile: str | None = Field(
        description="Run-local logical Playwright target profile, or null for isolated execution.",
        json_schema_extra={"default": None},
        title="Playwright profile",
    )
    mcp_playwright_profile_source: str | None = Field(
        description="Exact completed run-local physical profile copied into the target before every low-level action call.",
        json_schema_extra={"default": None},
        title="Playwright profile source",
    )
    model: WorkflowCodexModel = Field(
        description="Codex model used by action and verifier.",
        json_schema_extra={"default": "gpt-5.6-terra"},
        title="Model",
    )
    reasoning_effort: WorkflowCodexReasoningEffort = Field(
        description="Reasoning effort used by action and verifier.",
        json_schema_extra={"default": "high"},
        title="Reasoning effort",
    )

    def mcp_playwright_profile_physical_list_get(self) -> list[str | None]:
        ...


class WorkflowStepCodexConcurrentConfigBase(WorkflowStepCodexConfigBase):
    concurrency: int = Field(
        description="Maximum concurrent independent invocations of this step inside one workflow run.",
        ge=1,
        json_schema_extra={"default": 1},
        title="Concurrency",
    )

    def mcp_playwright_profile_physical_list_get(self) -> list[str | None]:
        ...


class WorkflowStepCodexRuntimePolicy(BaseModel):
    artifact_materialization_policy: ArtifactMaterializationPolicy
    execution_retry_policy: CodexExecutionRetryPolicy


class WorkflowStepExecutionContext(BaseModel):
    result_dir: Path
    runtime_capability: WorkflowRuntimeCapability
    step_instance_dir: Path
    workflow_input_path: Path


class WorkflowExecutionContext(BaseModel):
    result_dir: Path
    runtime_capability: WorkflowRuntimeCapability
    workflow_instance_dir: Path

    def for_child_workflow(
        self,
        *,
        runtime_capability: WorkflowRuntimeCapability,
        workflow_instance_key: str,
    ) -> WorkflowExecutionContext:
        ...

    def for_step(
        self,
        *,
        runtime_capability: WorkflowRuntimeCapability,
        step_instance_key: str,
    ) -> WorkflowStepExecutionContext:
        ...


class WorkflowStepCodexState(BaseModel):
    attempt_index: int = Field(ge=1)
    state: Literal["ready", "result_published", "verification_failed", "completed"]


class VerificationDecision(BaseModel):
    feedback_list: list[str]
    status: Literal["success", "failed"]


class VerificationResult(VerificationDecision):
    result_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    result_revision_index: int = Field(ge=1)

    @classmethod
    def from_decision(
        cls,
        *,
        decision: VerificationDecision,
        result: BaseModel,
        result_revision_index: int,
    ) -> Self:
        ...

    def is_bound_to(self, result: BaseModel, *, result_revision_index: int) -> bool:
        ...


class SqliteStateTable[RecordT: BaseModel](BaseModel):
    name: str
    primary_key_field_name_tuple: tuple[str, ...]
    record_model: type[RecordT]


class WorkflowStepInvocation(BaseModel, Generic[InputSourceT]):
    execution_context: WorkflowStepExecutionContext
    input_source: InputSourceT


class WorkflowStepInvocationOutcome(BaseModel, Generic[ResultT]):
    result: ResultT | None
    validation_feedback_tuple: tuple[str, ...]
```

Все Pydantic-модели в этом блоке используют строгую конфигурацию. `WorkflowInputBase`, config, context, capability, policy, route, `SqliteStateTable`, `WorkflowStepInvocation` и `WorkflowStepInvocationOutcome` дополнительно используют `frozen=True`; их поля нельзя менять после создания. `WorkflowStepInvocationOutcome` принимает только `result` с пустым `validation_feedback_tuple` либо отсутствующий `result` с непустым `validation_feedback_tuple`. `WorkflowStepCodexState` остается изменяемым состоянием. Конкретные input-модели являются полными снимками: создание без обязательного значения или с дополнительным полем завершается validation error.

`mcp_playwright_profile` и `mcp_playwright_profile_source` обязательны как поля полного config, даже когда их значение равно `None`. Source без target и одинаковые source/target запрещены. Непустые значения являются безопасными логическими именами, а не filesystem paths. `McpPlaywrightProfileRoute` является transient runtime-объектом: action и verification получают производные capability с разными MCP routes, но с теми же остальными возможностями запуска.

`VerificationDecision` запрещает непустой `feedback_list` при `status="success"` и требует непустой `feedback_list` при `status="failed"`. `VerificationResult.result_digest` обязателен и содержит SHA-256 канонической JSON-сериализации переданной точной модели результата. `VerificationResult.result_revision_index` обязателен и связывает verdict с одной публикацией результата. `from_decision(...)` является runtime-owned способом построения сохраненного verdict; `is_bound_to(...)` принимает ожидаемую revision и является обязательной проверкой перед приемом verdict при recovery.

`WorkflowRuntimeCapability` расширяется только явными необязательными полями, тип которых является отдельной моделью общей среды выполнения. Конкретный проект не добавляет в него предметные данные. Физические модули-владельцы всех интерфейсов перечислены один раз в `Приложение B. Структура workflow-container-runtime`.

`state_database_path_get(...)` является единственным владельцем стандартного соседнего пути `state.sqlite3`. Конкретные проекты и обертки команд не собирают это имя вручную.

`WorkflowStepCodexConfigBase.correction_attempt_limit` ограничивает число исправляющих action-попыток после первой; максимальное число action-попыток равно `1 + correction_attempt_limit`. `CodexExecutionRetryPolicy.attempt_limit` отдельно ограничивает низкоуровневые повторы одного вызова Codex до получения валидного структурированного ответа. `WorkflowStepCodexRuntimePolicy` принадлежит source-коду и не входит в пользовательский `WorkflowInputT`; все поля пользовательских config задаются в полном input явно.

```python
class JsonArtifactWriter:
    def schema_write(self, path: Path, model: type[BaseModel]) -> None:
        ...

    def write(self, path: Path, value: BaseModel) -> None:
        ...


class SqliteStateStore:
    def initialize(self, path: Path, table_list: list[SqliteStateTable[BaseModel]]) -> None:
        ...

    def upsert[RecordT: BaseModel](
        self,
        path: Path,
        table: SqliteStateTable[RecordT],
        record: RecordT,
    ) -> RecordT:
        ...

    def get[RecordT: BaseModel](
        self,
        path: Path,
        table: SqliteStateTable[RecordT],
        primary_key_value_tuple: tuple[object, ...],
    ) -> RecordT | None:
        ...

    def list[RecordT: BaseModel](
        self,
        path: Path,
        table: SqliteStateTable[RecordT],
    ) -> list[RecordT]:
        ...

    def list_by_primary_key_prefix[RecordT: BaseModel](
        self,
        path: Path,
        table: SqliteStateTable[RecordT],
        primary_key_value_prefix_tuple: tuple[object, ...],
    ) -> list[RecordT]:
        ...

    def delete[RecordT: BaseModel](
        self,
        path: Path,
        table: SqliteStateTable[RecordT],
        primary_key_value_tuple: tuple[object, ...],
    ) -> None:
        ...


class SqliteStateReader:
    def list[RecordT: BaseModel](
        self,
        path: Path,
        table: SqliteStateTable[RecordT],
    ) -> list[RecordT]:
        ...


class SqliteStateCommand:
    def run(
        self,
        argument_list: list[str],
        input_model: type[BaseModel],
        table_by_name_map: dict[str, SqliteStateTable[BaseModel]],
    ) -> int:
        ...


class ArtifactMaterializer:
    def materialize(
        self,
        *,
        policy: ArtifactMaterializationPolicy,
        result_dir: Path,
        step_instance_dir: Path,
    ) -> None:
        ...


class McpPlaywrightProfileRuntime:
    def __init__(
        self,
        *,
        mcp_playwright_profile_writeback_candidate_http_timeout_seconds: float = ...,
    ) -> None:
        ...

    @contextmanager
    def lease(
        self,
        *,
        mcp_playwright_profile: str | None,
        mcp_playwright_profile_source: str | None,
        runtime_capability: WorkflowRuntimeCapability,
    ) -> Generator[McpPlaywrightProfileRoute]:
        ...

    def writeback_candidate_publish(self, route: McpPlaywrightProfileRoute) -> None:
        ...


class PromptRenderer:
    def render(
        self,
        *,
        template_name: str,
        variable_by_name_map: Mapping[str, str],
    ) -> str:
        ...


class CodexRunner:
    def __init__(
        self,
        *,
        artifact_writer: JsonArtifactWriter,
        prompt_renderer: PromptRenderer,
        workflow_container_name: str,
    ) -> None:
        ...

    def run[OutputT: BaseModel](
        self,
        *,
        config: CodexRunnerConfig,
        diagnostic_dir: Path,
        output_model: type[OutputT],
        prompt: str,
        retry_policy: CodexExecutionRetryPolicy,
        runtime_capability: WorkflowRuntimeCapability,
        working_directory: Path,
    ) -> OutputT:
        ...
```

- `JsonArtifactWriter.schema_write(...)` атомарно публикует JSON Schema, полученную непосредственно из переданной Pydantic-модели; предметный код не сериализует schema вручную.
- `SqliteStateStore` создает таблицы только из статически переданных `SqliteStateTable`, проверяет точную модель до записи и после чтения, выполняет один idempotent upsert по предметному primary key и не хранит историю предыдущих значений.
- `SqliteStateReader.list(...)` является единственным публичным API downstream-чтения: он открывает только существующую объявленную базу через SQLite URI `mode=ro`, проверяет схему и возвращает строки в полном порядке primary key без изменения базы.
- `SqliteStateCommand` вычисляет `state.sqlite3` только из текущего `input.json`, принимает одну разрешенную операцию и одну разрешенную таблицу, читает payload через `stdin` и не предоставляет Codex raw SQL или произвольный путь.
- `McpPlaywrightProfileRuntime` выводит phase-specific MCP routes, удерживает profile lease на всем lifecycle шага и публикует writeback candidate только после успешной semantic verification. Он не запускает Playwright и не копирует физические каталоги профилей самостоятельно.
- `PromptRenderer` принимает только переменные маршрутизации текущей фазы. Защищенный namespace `runtime/` разрешается только runtime loader, `runtime/system/...` является единственным путем к общим system prompts, а имена без префикса разрешаются из предметного template tree. Runtime partials предоставляют domain template только пути, объявленные для текущей фазы в `5.4. Маршрутизация prompt`; domain template не открывает `state.json` и не ищет дополнительные recovery-файлы.
- `CodexRunnerConfig` не имеет скрытых значений по умолчанию и передается в каждый вызов. `CodexRunner` не хранит model или reasoning между вызовами.
- `CodexRunner` отвечает только за один низкоуровневый вызов и не владеет FSM шага.
- `CodexRunner` пишет diagnostics только в переданный детерминированный `diagnostic_dir`; рабочий каталог остается корнем результатов, относительно которого prompt разрешает публичные пути.

```python
class StepResultValidationError(RuntimeError):
    feedback_list: list[str]

    def __init__(self, *, feedback_list: list[str]) -> None:
        ...


class WorkflowResultValidationError(RuntimeError):
    feedback_list: list[str]

    def __init__(self, *, feedback_list: list[str]) -> None:
        ...
```

Оба исключения требуют непустой `feedback_list`. Общий runtime преобразует исключение в `VerificationDecision`, связывает его с текущим результатом и публикует `VerificationResult`. `WorkflowStepCodexBase` направляет такое решение в цикл исправления; `WorkflowStepDeterministicBase` повторно поднимает исключение без цикла исправления; workflow завершает `result_write_step(...)` без цикла исправления.

```python
class WorkflowBase(Generic[WorkflowInputT, WorkflowResultT]):
    def __init__(self, *, artifact_writer: JsonArtifactWriter) -> None:
        ...

    @final
    async def input_write_step(
        self,
        execution_context: WorkflowExecutionContext,
        workflow_input: WorkflowInputT,
    ) -> None:
        ...

    @final
    async def result_write_step(
        self,
        execution_context: WorkflowExecutionContext,
        workflow_input: WorkflowInputT,
        workflow_result: WorkflowResultT,
    ) -> WorkflowResultT:
        ...

    def result_validate(
        self,
        execution_context: WorkflowExecutionContext,
        workflow_input: WorkflowInputT,
        workflow_result: WorkflowResultT,
    ) -> None:
        ...
```

Конкретный workflow добавляет один публичный метод:

```python
@DBOS.workflow(..., validate_args=pydantic_args_validator)
async def run(
    self,
    execution_context: WorkflowExecutionContext,
    workflow_input: WorkflowInputT,
) -> WorkflowResultT:
    ...
```

`input_write_step(...)` и `result_write_step(...)` не переопределяются, ожидаются concrete workflow и каждый выполняет свою файловую операцию через `DBOS.run_step_async`. `result_validate(...)` может оставаться пустой реализацией только при отсутствии итоговых предметных инвариантов.

```python
class WorkflowStepBase(Generic[InputSourceT, InputT, ResultT]):
    result_model: ClassVar[type[ResultT]]

    def __init__(self, *, artifact_writer: JsonArtifactWriter) -> None:
        ...

    @abstractmethod
    def input_build(
        self,
        execution_context: WorkflowStepExecutionContext,
        input_source: InputSourceT,
    ) -> InputT:
        ...

    def artifact_prepare(
        self,
        execution_context: WorkflowStepExecutionContext,
        step_input: InputT,
    ) -> None:
        ...

    def result_validate(
        self,
        execution_context: WorkflowStepExecutionContext,
        step_input: InputT,
        result: ResultT,
    ) -> None:
        ...
```

`WorkflowStepBase` владеет общей публикацией input/result/verification и recovery mechanics, но не объявляет один ложный `run(...)` для шагов с разными входами выполнения. Точную финальную сигнатуру запуска объявляет следующий базовый класс, который знает, нужен ли run-owned config.

```python
class WorkflowStepDeterministicBase(
    WorkflowStepBase[InputSourceT, InputT, ResultT],
    Generic[InputSourceT, InputT, ResultT],
):
    @final
    def run(
        self,
        execution_context: WorkflowStepExecutionContext,
        input_source: InputSourceT,
    ) -> ResultT:
        ...

    @abstractmethod
    def result_build(
        self,
        execution_context: WorkflowStepExecutionContext,
        step_input: InputT,
    ) -> ResultT:
        ...
```

```python
class WorkflowStepCodexBase(
    WorkflowStepBase[InputSourceT, InputT, ResultT],
    Generic[InputSourceT, InputT, WorkflowStepCodexConfigT, ActionOutputT, ResultT],
):
    action_output_model: ClassVar[type[ActionOutputT]]
    config_model: ClassVar[type[WorkflowStepCodexConfigT]]
    result_model: ClassVar[type[ResultT]]
    state_model: ClassVar[type[WorkflowStepCodexState]]
    step_key: ClassVar[str]

    def __init__(
        self,
        *,
        artifact_materializer: ArtifactMaterializer,
        artifact_writer: JsonArtifactWriter,
        codex_runner: CodexRunner,
        mcp_playwright_profile_runtime: McpPlaywrightProfileRuntime,
        prompt_renderer: PromptRenderer,
        runtime_policy: WorkflowStepCodexRuntimePolicy,
    ) -> None:
        ...

    @final
    def run(
        self,
        execution_context: WorkflowStepExecutionContext,
        input_source: InputSourceT,
        workflow_step_config: WorkflowStepCodexConfigT,
    ) -> ResultT:
        ...

    def state_build(
        self,
        execution_context: WorkflowStepExecutionContext,
        step_input: InputT,
    ) -> WorkflowStepCodexState:
        ...

    @abstractmethod
    def result_from_action_build(
        self,
        execution_context: WorkflowStepExecutionContext,
        step_input: InputT,
        action_output: ActionOutputT,
    ) -> ResultT:
        ...


class WorkflowStepCodexConcurrentBase(
    WorkflowStepCodexBase[
        InputSourceT,
        InputT,
        WorkflowStepCodexConcurrentConfigT,
        ActionOutputT,
        ResultT,
    ],
    Generic[InputSourceT, InputT, WorkflowStepCodexConcurrentConfigT, ActionOutputT, ResultT],
):
    @final
    async def run_outcome_list(
        self,
        invocation_list: list[WorkflowStepInvocation[InputSourceT]],
        workflow_step_config: WorkflowStepCodexConcurrentConfigT,
    ) -> list[WorkflowStepInvocationOutcome[ResultT]]:
        ...

    @final
    async def run_list(
        self,
        invocation_list: list[WorkflowStepInvocation[InputSourceT]],
        workflow_step_config: WorkflowStepCodexConcurrentConfigT,
    ) -> list[ResultT]:
        ...
```

`WorkflowStepCodexConfigT` имеет верхнюю границу `WorkflowStepCodexConfigBase`, а `WorkflowStepCodexConcurrentConfigT` — `WorkflowStepCodexConcurrentConfigBase`. `WorkflowStepDeterministicBase` наследует конструктор `WorkflowStepBase` без изменений. Имена templates шага Codex выводятся из `step_key`; поля с именами templates в config запрещены.

`WorkflowStepCodexBase.run(...)` проверяет, что переданный config имеет точный тип `config_model`, и сверяет его с `config.step_map.<step_key>` в workflow input, на который ссылается step `input.json`. Он строит новый `CodexRunnerConfig` для action и verifier каждой попытки, получает phase-specific capability через один `McpPlaywrightProfileRuntime` и не сохраняет run-owned config в экземпляре шага. После успешной verification base публикует подходящий profile candidate до возврата `ResultT`.

`WorkflowStepCodexConcurrentBase.run_list(...)` и `run_outcome_list(...)` вызываются только из асинхронного DBOS workflow. Оба принимают непустой упорядоченный список независимых `WorkflowStepInvocation` и до запуска требуют один общий `result_dir`, один общий `workflow_input_path`, уникальные `step_instance_dir` и нахождение каждого каталога шага внутри того же запуска. Затем base создает не более `concurrency` фиксированных worker lanes, детерминированно распределяет invocation round-robin по исходному индексу, выполняет каждый lane последовательно через `DBOS.run_step_async` и возвращает значения в исходном порядке. Он не изменяет очередь DBOS и не допускает одновременное выполнение зависимых вызовов. Для именованного browser profile каждый lane получает физическое имя по правилу `7.3. Browser runtime`.

Ошибка одного элемента не прекращает планирование остальных: base выполняет весь список с тем же ограничением параллельности и ожидает каждый результат. Если присутствует ошибка не типа `StepResultValidationError`, оба метода поднимают первую такую ошибку по индексу. Иначе `run_list(...)` поднимает первый `StepResultValidationError`, а `run_outcome_list(...)` возвращает каждую такую ошибку как неизменяемый `WorkflowStepInvocationOutcome`. Успешные устойчиво сохраненные результаты переиспользуются при восстановлении.

`StepResultValidationError` имеет одно публичное поле `feedback_list: list[str]`. Список непустой и содержит действия, которые может выполнить следующая попытка Codex.

## Приложение B. Структура workflow-container-runtime
`workflow-container-runtime` владеет следующими модулями:

| Путь | Ответственность |
| --- | --- |
| `workflow_container_runtime/capability.py` | `BrowserRuntimeCapability` и составная модель `WorkflowRuntimeCapability`. |
| `workflow_container_runtime/codex/config.py` | Точная per-call конфигурация модели и reasoning для `CodexRunner`. |
| `workflow_container_runtime/codex/runner.py` | `CodexRunner` и только низкоуровневая граница подпроцесса Codex. |
| `workflow_container_runtime/instance.py` | Проверка ключей и расположения каталогов экземпляров. |
| `workflow_container_runtime/mcp_playwright_profile.py` | `McpPlaywrightProfileRoute`, `McpPlaywrightProfileRuntime`, profile lease, phase-specific MCP routing и вызов writeback-candidate endpoint. |
| `workflow_container_runtime/model.py` | Проверка строгой конфигурации Pydantic-моделей на runtime boundary. |
| `workflow_container_runtime/retry.py` | Неизменяемая политика низкоуровневых повторов `CodexRunner`. |
| `workflow_container_runtime/verification.py` | Transient `VerificationDecision`, связанный с публикацией результата `VerificationResult`, канонический SHA-256 и revision contract. |
| `workflow_container_runtime/workflow/base.py` | `WorkflowBase`, `WorkflowResultValidationError`, публикация workflow и восстановление. |
| `workflow_container_runtime/workflow/config.py` | `WorkflowConfigBase`, `WorkflowBrowserConfigBase` и `WorkflowInputBase`. |
| `workflow_container_runtime/workflow/context.py` | `WorkflowExecutionContext` и построение контекстов дочерних workflow и шагов. |
| `workflow_container_runtime/step/base.py` | `StepResultValidationError`, `WorkflowStepInvocationOutcome`, `WorkflowStepBase`, `WorkflowStepDeterministicBase`, `WorkflowStepCodexBase` и `WorkflowStepCodexConcurrentBase`. |
| `workflow_container_runtime/step/browser.py` | `BrowsingError` и `BrowserActionResult`. |
| `workflow_container_runtime/step/context.py` | `WorkflowStepExecutionContext` и `WorkflowStepInvocation`. |
| `workflow_container_runtime/step/codex.py` | Config bases шагов Codex, `WorkflowStepCodexRuntimePolicy` и `WorkflowStepCodexState`. |
| `workflow_container_runtime/step/file.py` | Стандартные имена файлов и path helpers. |
| `workflow_container_runtime/prompt/renderer.py` | `PromptRenderer` и общие каталоги шаблонов. |
| `workflow_container_runtime/artifact/materializer.py` | `ArtifactMaterializationPolicy` и `ArtifactMaterializer`. |
| `workflow_container_runtime/state/sqlite.py` | `state_database_path_get`, `SqliteStateTable`, `SqliteStateStore`, `SqliteStateReader`, `SqliteStateCommand` и общие module-private codec mechanics SQLite current state. |
| `workflow_container_runtime/artifact/writer.py` | `JsonArtifactWriter`. |

Конкретные контейнеры содержат конкретные подклассы и предметное поведение. Метод-обертка DBOS создает `InputSourceT`, вызывает `run(...)` конкретного шага и возвращает тот же `ResultT`.

Публичный пакет `workflow_container_runtime/stage/**`, перенаправляющие импорты, API совместимости жизненного цикла и псевдонимы моделей в канонической структуре отсутствуют.
