# Workflow Container Authoring

## Назначение
Этот документ владеет общим контрактом разработки workflow-container проектов. Он описывает, как писать `DBOS` workflow source, `Codex` stages, prompt templates, validators и artifacts. Runtime platform принадлежит `marketplace-automation`; generic workflow-container runtime принадлежит `workflow-container-runtime`; browser/VPN runtime принадлежит `browser-vpn-runtime`; domain logic принадлежит каждому конкретному workflow-container project.

Канонический путь этого контракта внутри установленного plugin: `references/workflow-container-authoring.md`.

Конкретный workflow-container project может ссылаться на этот документ из своих инструкций и design-документов, но не должен зависеть от `workflow-container-developer` в production runtime, импортировать его product code или требовать его CLI для запуска workflow.

## Code Quality Baseline
Проекты workflow-container экосистемы должны использовать общий минимальный baseline качества кода. Этот baseline переносит только проверяемые и идиоматические правила, которые защищают сопровождаемость проекта, и не переносит приватные вкусовые ограничения из внутренних репозиториев.

`pyproject.toml` должен объявлять `requires-python = ">=3.14"` и конфигурацию `Black` с `target-version = ["py314"]` и `line-length = 120`. Форматирование должно выполняться через `Black`, а не через ручное выравнивание.

Тесты должны запускаться через `pytest`. Runtime package проекты должны дополнительно проходить `python -m compileall <package>` перед handoff после Python behavior changes.

Public API, stable boundary functions, workflow entrypoints, stage interfaces и non-trivial modules должны иметь type annotations и docstrings, описывающие реальный контракт. Stable config, result, state, stage payload и cross-boundary data objects должны быть strict `Pydantic` v2 models. JSON schema artifacts должны генерироваться из этих моделей, а не храниться как второй ручной источник истины.

Refactor должен оставлять код в конечном steady state. Compatibility bridges, forwarding aliases, proxy wrappers, duplicated prompt partials, duplicated generated schemas и локальные копии runtime-owned code запрещены, если пользователь явно не запросил staged migration.

Project-local imports должны быть обычными module-scope imports. Production code не должен использовать local imports, import fallbacks, dynamic project-local imports или deferred missing-dependency fallbacks.

Полные приватные naming grammar, ORM rules, production database rules, обязательные docstring для каждой private helper function и другие внутренние правила приватных репозиториев не входят в этот baseline.

## Prompt Authoring Contract

Workflow-container prompts and instruction artifacts must be written as executable contracts, not as broad advice. The author must first identify the artifact role, then choose the instruction form that makes that role unambiguous.

Use `Contracts` when the text defines boundaries, inputs, outputs, schemas, artifact layout, allowed tools, forbidden tools, naming rules, source access rules, or ownership.

Use `FSM` when the process has states, retry loops, verification loops, blocked states, cancellation, crash recovery, multi-attempt execution, or terminal state transitions.

Use `Workflow` or `Step Sequence` when the process is a linear procedure without meaningful state-machine transitions.

Use `Persistent State` when generated, extracted, normalized, validated, externally loaded, or otherwise significant structured data is needed beyond the current local action.

Use `Recovery` where known failure modes can occur and the next corrective action must be deterministic.

These names are instruction-structure tools, not mandatory universal section headings. A prompt must not contain every section by default. A prompt must use the structure that matches its actual behavior.

When one prompt has multiple responsibilities, such as boundary contract, workflow sequence, retry, recovery, persistent state, external-source access, and verification handoff, it must separate those responsibilities into clear role-specific instruction blocks or an explicit execution sequence. A long flat prompt that mixes several roles without clear workflow structure is invalid even when each individual sentence is technically correct.

Significant structured data must be persisted at the nearest stable boundary when it is needed by a later step, verifier, retry, restart, follow-up, or external consumer. It must not be accumulated only in model memory and written at the end of a long stage.

Ephemeral local context may stay in the current execution when it is limited to the current local action, such as one current identifier, one loop item, or a short local counter. When such values become a list, registry, queue, recovery state, audit state, or cross-step handoff, they become persistent state and must be written explicitly.

The shared authoring contract must avoid domain-specific examples. Examples are allowed only when they are clearly illustrative or belong to a domain-owned prompt in the concrete workflow-container project. A shared workflow-container contract must not turn a domain-specific case into a generic rule.

## Runtime Package Boundary
`workflow-container-runtime` владеет generic исполняемым runtime-кодом и generic prompt resources, которые нужны workflow-container проектам в production runtime: `Codex` subprocess runner, JSON schema output boundary, common prompt renderer, common prompt partials, generic verified stage lifecycle, generic browser-tool event validation и generic artifact helpers.

Конкретный workflow-container project должен подключать `workflow-container-runtime` как обычную pinned Python dependency. Он не должен копировать в свой код generic `CodexStageRunner`, generic verified stage lifecycle, generic `Codex` subprocess lifecycle, runtime-owned prompt partials или generic browser-tool validation. В конкретном workflow-container project остаются только domain workflow, domain schemas, domain validators, domain prompt templates, domain prompt partials и domain artifact semantics.

`workflow-container-developer` может проверять наличие локальных копий runtime-owned файлов, но не является runtime dependency и не должен поставлять importable runtime code.

## `DBOS` Workflow Source
`Workflow Source`, который использует `DBOS`, должен оформлять `workflow` и `step` владельцев как `@DBOS.dbos_class` классы с instance-method методами.

Экземпляры таких классов должны быть stateless. Все durable данные запуска должны передаваться явными аргументами `DBOS` метода. `self` может хранить только stateless dependencies: factories, registries, validators, artifact layout, prompt loader, `Codex` runner и другие неизменяемые сервисы без run-specific mutable state.

`DBOS` workflow method владеет deterministic orchestration. `DBOS` step method владеет одной side-effect phase. Browser, network, filesystem writes, `Codex`, secret access и другие external IO должны выполняться только внутри `DBOS` steps или до старта root workflow.

`Workflow Source` должен разделять platform runtime contract, `DBOS` workflow layer, `DBOS` step layer, semantic stage layer, validator layer и artifact layer. Platform владеет запуском контейнера, `DataSource`, `DataContainer`, runtime capabilities, finalization, input writeback и статусом `WorkflowRun`. Контейнер возвращает `WorkflowResult`; `WorkflowResult` не управляет platform output, writeback или diagnostics списками через result payload. `Workflow Source` владеет смыслом своих шагов, prompts, result schemas, validators, artifact paths и интерпретацией данных.

## `Codex` Stage
Codex-backed stage должен состоять из action stage и verification stage. Action stage name должен иметь форму `{object}_{action}`, где `{action}` является глаголом. Verification stage name должен быть action stage name с постфиксом `_verify`.

Action stage пишет `result.json`. Verification stage пишет `verification.json` в тот же stage directory и не владеет отдельным artifact namespace. Batch, retry или resumable progress пишет один optional `state.json` в тот же stage directory. Stage-specific public state filenames запрещены. Domain meanings such as inventories, execution plans, queues, or resumable item lists must be typed contents of `state.json`, not separate public state artifacts.

Verification result должен быть минимальным: `status`, `feedback_list`, and `error_list`. Verification result не владеет artifact list, artifact namespace, source-of-truth state или copied result payload. Verification failure возвращается как feedback в тот же action stage до достижения attempt limit. Отдельные fix stages запрещены.

Prompt каждого Codex-backed stage должен быть одним полным Jinja2 template-файлом. `Workflow Source` должен рендерить template через typed context object и strict undefined handling. Python code не должен хранить human-readable stage instructions в multiline strings; Python code может выбирать template, строить typed context и передавать machine-facing values.

`Codex` output должен валидироваться на границе runner-а через JSON schema, сгенерированную из Pydantic model stage result. Stage code может записывать `result.json` только после успешной schema/model validation.

Mechanical validators проверяют schema-adjacent invariants, paths, duplicates, required files и internal consistency. Semantic verification проверяет correctness относительно prompt context, evidence и source data. Следующий stage читает verified `result.json` and declared artifacts; он не должен создавать отдельный cross-stage interpretation layer, который заново валидирует смысл предыдущего stage.

Owner-controlled names for JSON payload values must use `_json`.

## Artifact Materialization
Codex-backed action stage различает generated artifacts и external artifact references.

Generated artifacts принадлежат текущему stage. Они создаются самим stage или детерминированно материализуются из validated stage result.

External artifact references указывают на файлы, созданные другой run-owned системой или предыдущим stage. Codex-backed action stage не должен копировать такие файлы. Он должен вернуть references в своем schema-valid result.

`workflow-container-runtime` должен предоставлять artifact materialization layer с явными policy. Source-agnostic часть получает references из validated stage result, проверяет принадлежность каждого source path разрешенному run artifact root, нормализует references для текущего output bundle, копирует файл только когда declarative workflow policy требует stage-owned copy, иначе сохраняет normalized reference. Runtime может содержать default browser artifact copy policy для browser evidence artifacts, созданных внешним browser/VPN runtime, но эта browser-specific логика должна быть изолирована в одном runtime-owned policy object, включена по умолчанию и отключаема через stage config. Workflow-container projects, prompt templates и Codex stages не должны копировать или переопределять эту browser-copy логику.

`DBOS` step считается завершенным только после durable записи `result.json`, `verification.json` и всех generated artifacts, необходимых для автоматического восстановления после restart с этого или следующего step.

## Codex Sandbox Boundary
`Codex` subprocess внутри workflow container не должен включать собственный filesystem sandbox. Sandbox workflow определяется контейнером, Kubernetes pod, подключенными `DataSource` snapshot-ами и разрешенными output `DataContainer` path-ами.

`Workflow Source` должен запускать `Codex` так, чтобы он мог записывать stage artifacts и evidence в разрешенную рабочую область без `bubblewrap` или namespace-зависимостей внутри контейнера. Отключение filesystem sandbox не переносит `Codex` в browser/VPN network path.

## Browser Runtime Boundary
Workflow source получает browser runtime как готовый `MCP` URL. Source code workflow может передать этот URL в `Codex`, но не владеет настройками OpenVPN, stealth, browser flags, user agent, locale, timezone, viewport, profile materialization или выбором Playwright `MCP` package.

Workflow source не должен запускать прямые `@playwright/mcp`, `npx`, OpenVPN или альтернативные browser/VPN launchers.

Search queries должны выполняться через внутренний web search `Codex`, а не через browser runtime. `Codex` stage не должен открывать public search-engine result pages через Playwright `MCP`; browser runtime используется только для target source pages, выбранных из internal search results, site navigation, saved evidence или prompt context.

Каждый browser-backed action stage result, который открывает target URLs, должен иметь schema-valid `browsing_error_list` с объектами `{url, error}`. В этот список записываются все URL, по которым stage получил network error, timeout, DNS/TLS error, HTTP blocker, CAPTCHA, bot-check, access-denied, redirect-loop или другой browser-visible отказ. Такие ошибки нельзя прятать только в screenshots, notes, evidence files или generic `error_list`.

Browser tools могут записывать только browser evidence artifacts под объявленные browser evidence write directories, когда browser tool получает явный filename argument для snapshot, screenshot, download или другого browser-owned artifact.

Browser page JavaScript должен быть чистым browser JavaScript, выполняемым через `browser_evaluate` или эквивалентный `page.evaluate` page context. Он может читать DOM, `window`, `document`, links, tables, visible text и browser-visible state, затем возвращать serializable data. Browser page JavaScript не должен использовать `browser_run_code_unsafe`, Node.js APIs, CommonJS или Node module systems, dynamic `import(...)`, `node:` modules, `fs`, `path`, `process`, `Buffer` или local filesystem access.

Local result artifacts не должны открываться через browser tools с `file://`, `localhost` или `127.0.0.1`. Local artifacts читаются через normal filesystem access outside browser page context.

Semantic verification не должна использовать `jq`, shell one-liners with guessed JSON paths или brittle glob scripts over heterogeneous JSON artifacts. Schema validation уже выполняется workflow, а semantic verification читает current JSON artifacts as data. Если semantic verification inspect-ит JSON artifacts with local code, it must validate each parsed JSON value shape before field access and skip unrelated JSON artifact shapes.

## Проверки
Контрактные проверки workflow-container projects должны подтверждать stage naming, наличие полных Jinja2 templates для action и verification stages, отсутствие human-readable stage instructions в Python multiline strings, schema validation на runner boundary, централизованную runtime-owned artifact materialization policy без browser-specific копирования внутри workflow-container project или `Codex` stage, отключенный `Codex` filesystem sandbox внутри workflow container и browser access только через внешний `MCP` URL.
