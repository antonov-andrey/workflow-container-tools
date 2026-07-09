# Workflow Container Authoring

## Назначение
Этот документ владеет общим контрактом разработки workflow-container проектов. Он описывает, как писать `DBOS` workflow source, `Codex` stages, prompt templates, validators и artifacts. Runtime platform принадлежит `marketplace-automation`; runtime-neutral workflow source contracts принадлежат `workflow-container-contract`; generic workflow-container runtime принадлежит `workflow-container-runtime`; browser/VPN runtime принадлежит `browser-vpn-runtime`; domain logic принадлежит каждому конкретному workflow-container project.

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

## Minimal Stable Contract
Workflow-container data contracts must be minimal and stable. One semantic concept must have one minimal stable model at its owning boundary. Other layers must pass that model, reference it, or derive from it instead of creating a second shape for the same concept.

Stage result, DBOS handoff payload, typed stage input, private state, declared artifact and audit view are different roles. They must not mirror the same fields only because several stages need the data. If one value can be derived from an existing stable object, artifact handle, typed stage input, registry, or verified handoff payload, a second field for that value is forbidden.

Avoid duplicated status, error, message, note, priority, identity, path and applicability channels. Runtime lifecycle state belongs to runtime lifecycle results. Domain state belongs to one domain model. Human-readable audit or UI views may expose a subset derived from the stable source, but they must not become a second owner of that data.

Simplification is the default correction path. When one boundary is unclear, duplicated, hard to verify, or hard to recover, first try to remove fields, remove objects, merge owners, reuse an existing stable object, or move behavior to the single owner that already has the data. Do not add wrappers, compatibility bridges, translation layers, mirror models, extra state files, prompt aliases, or validator rebuild steps when removing the duplication solves the problem.

If simplification cannot solve the problem, design the smallest idiomatic change that satisfies `KISS`, `DRY`, single source of truth, explicit ownership and steady-state refactor principles. A new abstraction is allowed only when it removes real duplication, creates one stable boundary, or makes recovery and validation simpler than the direct version.

After every change, review the changed or directly affected boundary for code quality, data minimality and contract clarity. Fix redundant fields, redundant result channels, proxy layers, bridge states, copied schema text, duplicated prompt instructions, validator-owned object reconstruction, unclear ownership and unnecessary custom structure before handoff. Do not expand this review into unrelated broad refactoring outside the changed or directly affected boundary unless the user explicitly asks for that wider cleanup.

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

## Workflow Source Contract Boundary
`workflow-container-contract` владеет runtime-neutral контрактами workflow source: `Pydantic` models и loaders для `workflow.yaml` и `versions.yaml`, включая `WorkflowDefinition` и `WorkflowVersionsDefinition`. `marketplace-automation` и workflow-container projects должны использовать эти модели как общий контракт чтения и валидации workflow source metadata. `workflow-container-developer` только документирует и audit-ит этот контракт; он не должен становиться runtime owner или import dependency для этих моделей.

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

Action output and artifacts: `Codex` action возвращает schema-valid JSON через structured output и пишет только явно объявленные generated artifacts или optional private `state.json`. Generated artifacts принадлежат текущему stage. Action stage не пишет standard runtime files.

Verification output: verification stage возвращает только minimal `StageVerificationResult` со `status` and `feedback_list`. Verification stage не владеет artifact list, artifact namespace, source-of-truth state или second failure channel. Successful verification payload is exactly `{"status": "success", "feedback_list": []}`. Verification failure возвращается как feedback в тот же action stage до достижения attempt limit. Отдельные fix stages запрещены.

Typed stage input: runtime config accepts one strict Pydantic `InputT` object. Runtime writes that object as `input.json`. Prompts read stage input from disk through `input_path`. Generic prompt fields such as `prompt_context`, `prompt_context_path`, `shared_instruction`, `stage_instruction`, or `stage_state_path` are forbidden at the runtime boundary; domain instruction fields belong inside the concrete `InputT`.

Input worklist and progress state: input worklists and input execution plans belong to typed `InputT` in `input.json`. Generated batch, retry или resumable progress должен быть durable через declared stage artifacts или через private `state.json`, когда отдельный state реально нужен. Generated domain meanings such as inventories, queues, or resumable item lists must be typed contents of declared stage artifacts or private `state.json`, not separate public state artifacts.

Private state boundary: `state.json`, когда он используется, является private state текущего stage и его validator. Следующий stage не должен зависеть от предыдущего `state.json`. Stage-specific public state filenames запрещены.

Template naming: prompt каждого Codex-backed stage должен быть одним полным Jinja2 template-файлом. Имя action template должно быть `{stage_key}.md.j2`; имя verification template должно быть `{stage_key}_verify.md.j2`. Runtime config не должен принимать отдельные поля с именами template.

Retry prompt inputs: retry data may be read only from typed `InputT`, declared stage artifacts, optional private `state.json` in the current stage directory when this stage uses one, and runtime-provided retry paths owned by `Prompt Routing`. Runtime не должен добавлять другие generic retry-data channels at the runtime boundary.

Python prompt text placement: Python code не должен хранить human-readable stage instructions в multiline strings. Python code строит typed stage input и передает machine-facing values.

## Stage Lifecycle
Порядок stage lifecycle фиксирован:

`WorkflowBase` owns workflow-level orchestration mechanics for one workflow family.

`WorkflowStepBase[InputT, ResultT]` owns:

- building and persisting `InputT` as `input.json`;
- writing public `result.json` as the same `ResultT` returned by the DBOS step;
- writing `verification.json`;
- keeping `state.json` private to the current step;
- exposing typed hook methods for concrete domain behavior.

`WorkflowStepCodexBase[InputT, ActionOutputT, ResultT]` owns the Codex-backed lifecycle:

1. prepare declared artifacts;
2. build `InputT`;
3. write `input.json`;
4. run Codex action and validate `ActionOutputT`;
5. build public `ResultT`;
6. write `result.json`;
7. run mechanical validation;
8. run semantic verification;
9. write `verification.json`;
10. return `ResultT`.

Only these base classes own the standard stage-file lifecycle. Concrete stages must not write `input.json`, `result.json`, or `verification.json` manually.

## Prompt Routing
Runtime prompt routing:

- first action attempt receives `input_path`;
- retry action attempt receives `input_path` and `previous_stage_result_path`;
- verification attempt receives `input_path` and `stage_result_path`.

Runtime must not pass `prompt_context_path`, `draft_result_json`, `previous_result_json`, copied action result JSON, or copied stage result JSON into either prompt. `result.json` принадлежит `WorkflowStepBase` / `WorkflowStepCodexBase` lifecycle.

## DBOS Handoff
DBOS step handoff belongs to the successful step return after verified lifecycle. The next DBOS step input is built by workflow Python code from previous public result payloads, declared artifacts, and workflow parameters. A downstream step must never read a previous step `state.json`.

A same-stage owner may read its private `state.json` only to derive declared public result fields or declared artifact references before returning `ResultT`.

## Durable Step Completion
`DBOS` step считается завершенным только после durable записи полного recovery bundle: `input.json`, `result.json`, `verification.json`, declared stage-generated artifacts, optional private `state.json` in the current stage directory when this stage uses one, and materialized external artifact tree files referenced by current stage data and required to rerun validation or verification after restart.

## JSON Payload Naming
Owner-controlled names for JSON payload values must use `_json`.

## Artifact Materialization
Codex-backed action stage различает stage-generated artifacts и external artifact trees.

Stage-generated artifacts принадлежат текущему stage и пишутся самим stage в объявленные stage paths.

External artifact trees принадлежат другой run-owned системе, которая зеркалирует stage-relative paths под одним или несколькими artifact roots. Codex-backed action stage не должен копировать такие деревья сам.

`workflow-container-runtime` должен предоставлять artifact materialization layer с явными generic policy. Materialization timing is owned by `Stage Lifecycle`. Runtime materializes configured external artifact roots by copying the matching stage tree into the current stage directory. Runtime materialization must not expose a second generic API that rewrites arbitrary result reference lists. Default policy MAY include `.playwright-mcp/current` as one artifact root for browser evidence artifacts, but policy fields must stay source-neutral. Disable materialization with an empty artifact root list. Workflow-container projects, prompt templates и Codex stages не должны копировать или переопределять runtime materialization logic.

## Codex Sandbox Boundary
`Codex` subprocess внутри workflow container не должен включать собственный filesystem sandbox. Sandbox workflow определяется контейнером, Kubernetes pod, подключенными `DataSource` snapshot-ами и разрешенными output `DataContainer` path-ами.

`Workflow Source` должен запускать `Codex` так, чтобы он мог записывать stage artifacts и evidence в разрешенную рабочую область без `bubblewrap` или namespace-зависимостей внутри контейнера. Отключение filesystem sandbox не переносит `Codex` в browser/VPN network path.

## Browser Runtime Boundary
Workflow source получает browser runtime как готовый `MCP` URL. Source code workflow может передать этот URL в `Codex`, но не владеет настройками OpenVPN, stealth, browser flags, user agent, locale, timezone, viewport, profile materialization или выбором Playwright `MCP` package.

Workflow source не должен запускать прямые `@playwright/mcp`, `npx`, OpenVPN или альтернативные browser/VPN launchers.

Search queries должны выполняться через внутренний web search `Codex`, а не через browser runtime. `Codex` stage не должен открывать public search-engine result pages через Playwright `MCP`; browser runtime используется только для target source pages, выбранных из internal search results, site navigation, saved evidence или typed stage input.

Каждый browser-backed action stage result, который открывает target URLs, должен иметь schema-valid `browsing_error_list` с объектами `{url, error}`. В этот список записываются все URL, по которым stage получил network error, timeout, DNS/TLS error, HTTP blocker, CAPTCHA, bot-check, access-denied, redirect-loop или другой browser-visible отказ. Такие ошибки нельзя прятать только в screenshots, notes, evidence files или generic `error_list`.

Browser tools могут записывать только browser evidence artifacts под объявленные browser evidence write directories, когда browser tool получает явный filename argument для snapshot, screenshot, download или другого browser-owned artifact.

Browser page JavaScript должен быть чистым browser JavaScript, выполняемым через `browser_evaluate` или эквивалентный `page.evaluate` page context. Он может читать DOM, `window`, `document`, links, tables, visible text и browser-visible state, затем возвращать serializable data. Browser page JavaScript не должен использовать `browser_run_code_unsafe`, Node.js APIs, CommonJS или Node module systems, dynamic `import(...)`, `node:` modules, `fs`, `path`, `process`, `Buffer` или local filesystem access.

Local result artifacts не должны открываться через browser tools с `file://`, `localhost` или `127.0.0.1`. Local artifacts читаются через normal filesystem access outside browser page context.

Semantic verification не должна использовать `jq`, shell one-liners with guessed JSON paths или brittle glob scripts over heterogeneous JSON artifacts. Schema validation уже выполняется workflow, а semantic verification читает current JSON artifacts as data. Если semantic verification inspect-ит JSON artifacts with local code, it must validate each parsed JSON value shape before field access and skip unrelated JSON artifact shapes.

## Проверки
Workflow-container project contract tests must cover the applicable owner sections from this document. For each changed workflow-container artifact, tests or semantic reread must cover every owner section that artifact implements, references, or changes. Проверки должны проверять текущие owner contracts напрямую и не должны опираться на частичный пересказ этих контрактов в этой секции.
