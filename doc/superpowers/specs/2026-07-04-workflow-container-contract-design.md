# `workflow-container-contract`

## Цель
`workflow-container-contract` становится runtime-neutral Python package для общих контрактов workflow-container экосистемы. Он владеет Pydantic v2 моделями и loader-ами для файлов `workflow.yaml`, `versions.yaml` и общего результата workflow run.

Пакет нужен, чтобы `marketplace-automation`, `workflow-container-developer` и конкретные workflow-container projects не держали разные частичные копии одного контракта. `workflow-container-runtime` не должен владеть этими моделями, потому что он отвечает за исполнение внутри контейнера, а не за platform/source metadata.

## Границы Ответственности

### `workflow-container-contract`
`workflow-container-contract` владеет только runtime-neutral contract моделями:

- `WorkflowDefinition` для `workflow.yaml`;
- `WorkflowVersionDefinition` для `versions.yaml`;
- `WorkflowResult` для общего результата workflow run;
- loader-ами `from_path(path)` на моделях;
- helper-ом для проверки реальных contract-файлов workflow-container проекта в тестах.

Пакет не должен зависеть от `marketplace-automation`, `workflow-container-runtime`, `workflow-container-developer`, `brand-size-chart` или других конкретных workflow-container projects.

### `marketplace-automation`
`marketplace-automation` владеет platform runtime и persistence:

- `WorkflowSource`, `WorkflowSourceVersion`, `Workflow`, `WorkflowRun`;
- `DataSource`, `DataContainer`, snapshots и storage;
- запуском workflow container;
- финализацией статуса run на основе `WorkflowResult`;
- platform-specific API, DB и storage glue.

`marketplace-automation` должен импортировать общие contract models из `workflow-container-contract` вместо локального дублирования. Локальный `backend.workflow_config` может оставаться только для platform-specific helper-ов, которые не являются YAML/result contract.

### `workflow-container-runtime`
`workflow-container-runtime` не владеет `workflow.yaml`, `versions.yaml` или `WorkflowResult`. Он остается владельцем runtime-механики: Codex runner, prompt renderer, JSON schema output boundary, generic prompt partials и artifact helpers.

### `workflow-container-developer`
`workflow-container-developer` больше не владеет Python CLI `audit` для contract validation. Старый `audit` subcommand и `WorkflowContainerAudit` должны быть удалены. Если CLI остается, он может быть только generic helper-ом, например для `list` соседних workflow-container projects.

### Workflow-Container Projects
Каждый workflow-container project владеет своими `workflow.yaml`, `versions.yaml`, `AGENTS.md`, `doc/design/**`, domain models, prompts, validators и tests. Проверка `workflow.yaml` и `versions.yaml` должна входить в test suite каждого workflow-container project через общий helper из `workflow-container-contract`, без копирования тестовой логики.

## Модель `WorkflowDefinition`
`WorkflowDefinition` валидирует `workflow.yaml`.

Поля:

- `name: str`;
- `image: str`;
- `command_list: list[str]` с YAML alias `command`;
- `data_source_list: list[WorkflowDataSourceDefinition]`;
- `data_container_list: list[WorkflowDataContainerDefinition]`;
- `runtime_capability_list: list[WorkflowRuntimeCapabilityDefinition]`.

`WorkflowDataSourceDefinition`:

- `name: str`;
- `prompt: str`;
- `is_private: bool = false`;
- `mutable_prefix_list: list[str] = []`;
- instance method `match_mutable_path(logical_path: str) -> bool`.

`WorkflowDataContainerDefinition`:

- `name: str`;
- `prompt: str`;
- `schema_athena_document: dict[str, object] = {}` с alias `schema_athena`;
- `schema_view_document: dict[str, object] = {}` с alias `schema_view`.

`WorkflowRuntimeCapabilityDefinition`:

- `name: str`;
- `data_source_name: str`.

Validation:

- required string fields must be non-empty after validation;
- `command_list` must be non-empty and contain non-empty strings;
- data source names must be unique;
- data container names must be unique;
- runtime capability names must be unique;
- every runtime capability must reference a declared data source;
- `mutable_prefix_list` entries must be safe relative logical path patterns;
- object fields use strict Pydantic validation and forbid unknown fields unless this spec explicitly allows extension.

`WorkflowDefinition.from_path(path)` reads YAML from `path`, requires a mapping payload, validates it and returns a `WorkflowDefinition`.

## Модель `WorkflowVersionDefinition`
`WorkflowVersionDefinition` валидирует `versions.yaml`.

Поля:

- `project: str`;
- `version: str`;
- `contract_version_by_name_map: dict[str, int]` с YAML alias `contracts`.

Validation:

- `project` must be non-empty;
- `version` must be SemVer in the form `X.Y.Z`;
- `contract_version_by_name_map` keys must be non-empty;
- contract versions must be positive integers.

`WorkflowVersionDefinition.from_path(path)` reads YAML from `path`, requires a mapping payload, validates it and returns a `WorkflowVersionDefinition`.

## Ошибки Валидации
`workflow-container-contract` должен предоставлять project-neutral validation errors. Ошибки могут быть Pydantic `ValidationError`, YAML parser errors, filesystem errors или package-owned exceptions для file-shape failures. Они не должны импортировать, возвращать или упоминать HTTP, DB, API, `marketplace-automation`, `workflow-container-developer`, `workflow-container-runtime` или конкретный workflow-container project.

## Модель `WorkflowResult`
`WorkflowResult` заменяет старый `WorkflowTerminalResult`.

Общие поля:

- `status: Literal["success", "failed"]`;
- `message: str`;
- `error_list: list[str] = []`.

Старые platform-поля `output_container_id_list`, `input_writeback_ref_list` и `diagnostic_path_list` запрещены в новом контракте. Workflow-container результат не должен управлять platform storage/writeback списками через result payload.

`WorkflowResult` должен разрешать дополнительные domain-specific поля, потому что реальные workflow-container results расширяют общий envelope. Например текущий `brand-size-chart` run result содержит domain fields поверх `status`, `message` и `error_list`. `marketplace-automation` должен читать только общий envelope и не интерпретировать domain-specific поля.

Cancellation остается platform action, а не обязательным workflow-container result status. Если run отменен платформой, `marketplace-automation` должен завершать его через platform cancellation flow, а не требовать от container `WorkflowResult(status="cancelled")`.

## Общий Test Helper
`workflow-container-contract` должен предоставить helper для использования в workflow-container tests:

```python
from pathlib import Path

from workflow_container_contract.testing import workflow_contract_file_validate


def test_workflow_contract_file_validate() -> None:
    workflow_contract_file_validate(project_root=Path.cwd())
```

`workflow_contract_file_validate(project_root)` должен:

- валидировать `project_root / "workflow.yaml"` через `WorkflowDefinition.from_path`;
- валидировать `project_root / "versions.yaml"` через `WorkflowVersionDefinition.from_path`;
- проверять, что `WorkflowDefinition.name` и `WorkflowVersionDefinition.project` дают один и тот же canonical project key.

Canonical project key вычисляется одинаково для обоих значений: lowercase, каждая последовательность не `a-z`, не `0-9` символов заменяется одним `_`, ведущие и замыкающие `_` удаляются. Например `brand_size_chart` и `brand-size-chart` дают один key `brand_size_chart`.

Helper не должен зависеть от `pytest`; он может выбрасывать обычные exceptions, которые тестовый runner покажет как failure.

## Изменения В Проектах

### `workflow-container-contract`
Создать package, `pyproject.toml`, `AGENTS.md`, README, модели, loader-и и tests.

### `marketplace-automation`
Заменить локальные YAML contract models на импорт из `workflow-container-contract`. Удалить `WorkflowTerminalResult` и все старые terminal-result payload contracts в пользу `WorkflowResult`.

Нужно проверить и обновить:

- `backend/workflow_config.py`;
- `backend/api/workflow.py`;
- `backend/workflow_run.py`;
- `test/backend/test_workflow_config.py`;
- `test/backend/test_workflow_api.py`;
- `test/backend/test_workflow_run.py`;
- `doc/design/backend.md`;
- `doc/design/data-storage.md`;
- `doc/design/persistence.md`;
- `doc/design/workflow-runtime.md`.

`marketplace-automation` должен соответствовать текущим контейнерам. Старый `terminal result` wording должен быть заменен на `workflow result` там, где речь идет о result payload контейнера. Новые API/docs/tests не должны требовать от контейнера `output_container_id_list`, `input_writeback_ref_list` или `diagnostic_path_list`.

### `workflow-container-developer`
Удалить старый Python CLI audit:

- удалить `workflow_container_developer/audit.py`;
- удалить `audit` subcommand из `workflow_container_developer/cli.py`;
- удалить audit tests;
- обновить README/tests/help expectations.

Если нужен contract validation в developer workflow, он должен идти через `workflow-container-contract` helper или через tests конкретного workflow-container, а не через отдельную mechanical audit команду.

### `brand-size-chart`
Добавить dependency на `workflow-container-contract`. Добавить один тест, который вызывает общий `workflow_contract_file_validate(project_root=Path.cwd())`.

Проверить, что текущий `brand_size_chart.model.run.RunResult` совместим с `WorkflowResult`: он должен иметь `status`, `message`, `error_list` и может иметь дополнительные domain-specific fields.

## Verification
Минимальная проверка после реализации:

- `workflow-container-contract`: `python -m pytest -q`, `python -m compileall workflow_container_contract`;
- `workflow-container-developer`: `python -m pytest -q`, `python -m compileall workflow_container_developer`, plugin validation;
- `marketplace-automation`: targeted workflow config/run/API tests plus repository-required checks from its local instructions;
- `brand-size-chart`: `python -m pytest -q`.
