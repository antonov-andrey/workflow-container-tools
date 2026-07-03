# Workflow Container Authoring

## Назначение
Этот документ владеет общим контрактом разработки workflow-container проектов. Он описывает, как писать `DBOS` workflow source, `Codex` stages, prompt templates, validators и artifacts. Runtime platform принадлежит `marketplace-automation`; browser/VPN runtime принадлежит `browser-vpn-runtime`; domain logic принадлежит каждому конкретному workflow-container project.

Канонический путь этого контракта: `doc/design/workflow-container-authoring.md`.

Конкретный workflow-container project может ссылаться на этот документ из своих инструкций и design-документов, но не должен зависеть от `workflow-container-developer` в production runtime, импортировать его product code или требовать его CLI для запуска workflow.

## `DBOS` Workflow Source
`Workflow Source`, который использует `DBOS`, должен оформлять `workflow` и `step` владельцев как `@DBOS.dbos_class` классы с instance-method методами.

Экземпляры таких классов должны быть stateless. Все durable данные запуска должны передаваться явными аргументами `DBOS` метода. `self` может хранить только stateless dependencies: factories, registries, validators, artifact layout, prompt loader, `Codex` runner и другие неизменяемые сервисы без run-specific mutable state.

`DBOS` workflow method владеет deterministic orchestration. `DBOS` step method владеет одной side-effect phase. Browser, network, filesystem writes, `Codex`, secret access и другие external IO должны выполняться только внутри `DBOS` steps или до старта root workflow.

`Workflow Source` должен разделять platform runtime contract, `DBOS` workflow layer, `DBOS` step layer, semantic stage layer, validator layer и artifact layer. Platform владеет запуском контейнера, `DataSource`, `DataContainer`, runtime capabilities, terminal result, input writeback и статусом `WorkflowRun`. `Workflow Source` владеет смыслом своих шагов, prompts, result schemas, validators, artifact paths и интерпретацией данных.

## `Codex` Stage
Codex-backed stage должен состоять из action stage и verification stage. Action stage name должен иметь форму `{object}_{action}`, где `{action}` является глаголом. Verification stage name должен быть action stage name с постфиксом `_verify`.

Action stage пишет `result.json`. Verification stage пишет `verification.json` в тот же stage directory и не владеет отдельным artifact namespace. Verification failure возвращается как feedback в тот же action stage до достижения attempt limit. Отдельные fix stages запрещены.

Prompt каждого Codex-backed stage должен быть одним полным Jinja2 template-файлом. `Workflow Source` должен рендерить template через typed context object и strict undefined handling. Python code не должен хранить human-readable stage instructions в multiline strings; Python code может выбирать template, строить typed context и передавать machine-facing values.

`Codex` output должен валидироваться на границе runner-а через JSON schema, сгенерированную из Pydantic model stage result. Stage code может записывать `result.json` только после успешной schema/model validation.

## Artifact Materialization
Codex-backed action stage различает generated artifacts и external artifact references.

Generated artifacts принадлежат текущему stage. Они создаются самим stage или детерминированно материализуются из validated stage result.

External artifact references указывают на файлы, созданные другой run-owned системой или предыдущим stage. Codex-backed action stage не должен копировать такие файлы. Он должен вернуть references в своем schema-valid result.

`Workflow Source` должен иметь generic artifact materialization layer. Этот layer получает references из validated stage result, проверяет принадлежность каждого source path разрешенному run artifact root, нормализует references для текущего output bundle, копирует файл только когда declarative workflow policy требует stage-owned copy, иначе сохраняет normalized reference. Этот layer не должен содержать browser-specific, Playwright-specific, source-type-specific или domain-specific rules.

`DBOS` step считается завершенным только после durable записи `result.json`, `verification.json` и всех generated artifacts, необходимых для автоматического восстановления после restart с этого или следующего step.

## Codex Sandbox Boundary
`Codex` subprocess внутри workflow container не должен включать собственный filesystem sandbox. Sandbox workflow определяется контейнером, Kubernetes pod, подключенными `DataSource` snapshot-ами и разрешенными output `DataContainer` path-ами.

`Workflow Source` должен запускать `Codex` так, чтобы он мог записывать stage artifacts и evidence в разрешенную рабочую область без `bubblewrap` или namespace-зависимостей внутри контейнера. Отключение filesystem sandbox не переносит `Codex` в browser/VPN network path.

## Browser Runtime Boundary
Workflow source получает browser runtime как готовый `MCP` URL. Source code workflow может передать этот URL в `Codex`, но не владеет настройками OpenVPN, stealth, browser flags, user agent, locale, timezone, viewport, profile materialization или выбором Playwright `MCP` package.

Workflow source не должен запускать прямые `@playwright/mcp`, `npx`, OpenVPN или альтернативные browser/VPN launchers.

Browser tools могут записывать только browser evidence artifacts под объявленные browser evidence write directories, когда browser tool получает явный filename argument для snapshot, screenshot, download или другого browser-owned artifact.

Browser page JavaScript должен быть чистым browser JavaScript, выполняемым через `browser_evaluate` или эквивалентный `page.evaluate` page context. Он может читать DOM, `window`, `document`, links, tables, visible text и browser-visible state, затем возвращать serializable data. Browser page JavaScript не должен использовать `browser_run_code_unsafe`, Node.js APIs, CommonJS или Node module systems, dynamic `import(...)`, `node:` modules, `fs`, `path`, `process`, `Buffer` или local filesystem access.

Local result artifacts не должны открываться через browser tools с `file://`, `localhost` или `127.0.0.1`. Local artifacts читаются через normal filesystem access outside browser page context.

Semantic verification не должна использовать `jq`, shell one-liners with guessed JSON paths или brittle glob scripts over heterogeneous JSON artifacts. Schema validation уже выполняется workflow, а semantic verification читает current JSON artifacts as data. Если semantic verification inspect-ит JSON artifacts with local code, it must validate each parsed JSON value shape before field access and skip unrelated JSON artifact shapes.

## Проверки
Контрактные проверки workflow-container projects должны подтверждать stage naming, наличие полных Jinja2 templates для action и verification stages, отсутствие human-readable stage instructions в Python multiline strings, schema validation на runner boundary, generic artifact materialization без browser-specific копирования внутри `Codex` stage, отключенный `Codex` filesystem sandbox внутри workflow container и browser access только через внешний `MCP` URL.
