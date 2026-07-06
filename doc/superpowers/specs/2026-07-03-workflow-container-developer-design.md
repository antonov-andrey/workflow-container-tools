# `workflow-container-developer`

## Цель
`workflow-container-developer` становится отдельным developer workspace и canonical authoring contract для разработки workflow-container проектов, лежащих рядом с ним в файловой системе.

Проект не является runtime dependency конкретных workflow-container и не участвует в production-запуске. Пользователь заходит в `workflow-container-developer`, запускает интерактивный `Codex CLI` и разрабатывает выбранный соседний workflow-container project через общие инструкции, общие проверки и общие CLI-инструменты.

## Границы Ответственности

### `workflow-container-developer`
`workflow-container-developer` владеет только общими правилами разработки workflow-container проектов. Канонический reusable authoring contract живет в `doc/design/workflow-container-authoring.md`:

- authoring contract для `DBOS` workflow source;
- общие инструкции для `Codex CLI` при разработке соседних workflow-container;
- общие design-документы для структуры `DBOS`, stage action/verification loop, prompt templates, JSON schema validation, artifact materialization, local run/debug и contract audit;
- generic CLI-инструменты для работы с соседними workflow-container projects;
- reference skeleton/template нового workflow-container, если он не содержит доменной логики конкретного workflow.

`workflow-container-developer` не должен содержать hardcode конкретных workflow-container names, source types, brand logic, marketplace logic, table schemas или wrapper-команды для одного конкретного workflow. Вся конкретика должна жить в целевом workflow-container project.

### `marketplace-automation`
`marketplace-automation` владеет platform runtime contract:

- `WorkflowSource`, `WorkflowSourceVersion`, `Workflow`, `WorkflowRun`, `DataSource`, `DataContainer`;
- parsing and validation внешнего `workflow.yaml`;
- snapshots входных `DataSource`;
- создание output `DataContainer`;
- запуск workflow container;
- terminal result и input writeback validation.

`marketplace-automation` не должен владеть внутренними правилами написания `DBOS` workflow, `Codex` stages, prompt templates, semantic validators, source-specific logic или artifact layout конкретного workflow-container.

### `browser-vpn-runtime`
`browser-vpn-runtime` владеет reusable browser/VPN runtime capability:

- `OpenVPN`;
- persistent `Playwright` profile;
- headed Chromium, stealth, locale, timezone, viewport;
- `Playwright MCP` launcher;
- readiness checks;
- profile materialization and snapshot helpers.

`browser-vpn-runtime` не должен знать доменную логику workflow-container проектов. Он предоставляет runtime capability, а не authoring contract и не workflow orchestration.

### Конкретный Workflow-Container Project
Один workflow-container project владеет своей domain task и production workflow source:

- `workflow.yaml`;
- `versions.yaml`;
- project-local `AGENTS.md`;
- domain-specific `doc/design/**`;
- workflow implementation, schemas, prompts, validators и tests;
- local специализации общего authoring contract.

Конкретный workflow-container не должен знать о `workflow-container-developer` как runtime dependency, import dependency или production dependency. Он может зависеть от `browser-vpn-runtime` только как от runtime capability или development dependency, если браузер действительно нужен.

## Файловая Модель
Проекты лежат рядом:

```text
<projects-root>/
  workflow-container-developer/
  <workflow-container-project>/
  browser-vpn-runtime/
  marketplace-automation/
  <other-workflow-container>/
```

`workflow-container-developer` может обнаруживать соседние workflow-container projects через filesystem scan родительской директории. Целевой workflow-container выбирается явно через CLI-аргумент, интерактивный выбор или конфигурацию команды. Обнаружение должно опираться на project-owned markers целевого проекта, например наличие `workflow.yaml` и `versions.yaml`, а не на hardcoded names.

## Общие CLI-Инструменты
CLI-инструменты `workflow-container-developer` должны быть generic:

- list adjacent workflow-container projects;
- validate one target project has `workflow.yaml`, `versions.yaml`, `AGENTS.md`, expected prompt/template layout and documented local design;
- run generic workflow-container contract audit for one target project;
- run target project tests through the target project's declared test command;
- run target project formatting or static checks through declared commands;
- validate prompt template structure and absence of duplicated prompt prose outside templates;
- validate that target project does not duplicate common authoring rules that belong to `workflow-container-developer`;
- run local workflow smoke command only when the target project declares a standard local run command.

CLI-инструменты не должны содержать branches such as `if project == "<workflow-container-project>"`. Project-specific commands must be declared by the target project in its own config or documentation and consumed generically.

## Общий Authoring Contract
`doc/design/workflow-container-authoring.md` должен владеть общими правилами, которые сейчас частично разложены по `marketplace-automation` и target workflow-container projects:

- `DBOS` workflow source structure;
- stateless `@DBOS.dbos_class` workflow and step owners;
- explicit durable arguments for `DBOS` methods;
- deterministic workflow layer and side-effect step layer;
- separation between platform runtime contract, `DBOS` workflow layer, `DBOS` step layer, semantic stage layer, validator layer and artifact layer;
- stage naming: action stage `{object}_{action}`, verification stage `{object}_{action}_verify`;
- action result path `result.json`;
- verification result path `verification.json`;
- no separate fix stages;
- verification failure loops back to the same action stage;
- full Jinja2 template file per `Codex` stage;
- shared prompt fragments under one template partials tree;
- no human-readable stage instructions in Python multiline strings;
- schema validation at `Codex` runner boundary from Pydantic-generated JSON Schema;
- runtime-owned artifact materialization policy layer;
- generated artifacts vs external artifact references;
- no browser-specific copy behavior inside `Workflow Source` or `Codex` stage;
- browser runtime received as external `MCP` URL;
- workflow code does not launch `@playwright/mcp`, `npx`, OpenVPN or custom browser runtime;
- `Codex` subprocess has no filesystem sandbox inside workflow container.

## Рефакторинг Текущих Проектов
Нужно перенести ownership общих правил:

- из `marketplace-automation/doc/design/workflow-runtime.md` в `workflow-container-developer` переносятся authoring rules для `DBOS`, `Codex` stage, prompt templates, validation и artifact materialization;
- в `marketplace-automation/doc/design/workflow-runtime.md` остаются только platform runtime rules: network boundary, `WorkflowRun`, `DataSource`, `DataContainer`, runtime capabilities, terminal result and input writeback;
- из `<workflow-container-project>/doc/design/<workflow-container-project>.md` в `workflow-container-developer` выносятся общие правила workflow-container authoring;
- в `<workflow-container-project>/doc/design/<workflow-container-project>.md` остаются только domain-specific правила загрузчика таблиц размеров;
- `<workflow-container-project>/AGENTS.md` остается project-local and domain-specific, а общие правила контейнерной разработки заменяются ссылкой на `workflow-container-developer` contract.

## Проверка Границ
После рефакторинга должны выполняться следующие проверки:

- `workflow-container-developer` не содержит hardcoded target-project logic;
- `<workflow-container-project>` не импортирует, не вызывает и не требует `workflow-container-developer` для production run;
- `marketplace-automation` не описывает внутреннюю реализацию `Codex` stages и semantic validators конкретного workflow-container;
- `browser-vpn-runtime` не содержит domain workflow logic;
- generic CLI-инструменты `workflow-container-developer` могут работать с `<workflow-container-project>` как с target project only through declared target project files and commands;
- текущие тесты `<workflow-container-project>`, `browser-vpn-runtime` и `marketplace-automation` остаются зелеными после переноса ownership.

## Не Входит В Эту Спецификацию
Эта спецификация не требует:

- реализации нового workflow-container domain project;
- изменения production deployment model `marketplace-automation`;
- изменения browser/VPN runtime behavior;
- переписывания domain logic `<workflow-container-project>`;
- автоматического подключения `workflow-container-developer` как submodule к другим проектам;
- runtime-зависимости workflow-container projects от `workflow-container-developer`.
