---
name: workflow-container-developer
description: Use when developing, auditing, refactoring, or reviewing workflow-container projects, workflow-container runtime packages, browser/VPN runtime integration, DBOS workflow source structure, Codex step prompts, artifact contracts, or shared workflow-container code quality rules.
---

# Workflow Container Developer

Use this skill for workflow-container ecosystem work. The ecosystem includes concrete workflow containers, `workflow-container-contract`, `workflow-container-runtime`, `browser-runtime`, `vpn-runtime`, authoring guidance, semantic audit and input-creation skills, the generic `goal-brainstorm` documentation skill, and optional local discovery CLI.

## Workflow

1. Identify the target repository from the current working directory and its declared metadata, package, instruction, and design files.
2. Before changing workflow contracts, prompt contracts, artifact layout, runtime boundaries, code quality rules, prompt templates, step instructions, validator instructions, or recovery instructions, read `references/workflow-container-authoring.md`.
   - Read `1. Назначение и краткая модель` and `3.1. Протоколы типов` before designing data flow.
   - Read `2.4. Публичный вход и форма настроек` and `2.5. Миграция публичного входа` before changing `WorkflowInputT`, run settings, `input.schema.json`, platform forms, saved Workflow/WorkflowRun input, or input migrations.
   - Read `3.3. Иерархия классов`, `3.4. Граница DBOS`, and `Приложение A. Публичные интерфейсы` before writing workflow or step classes.
   - Read `4. Файлы и передача данных` and `5. Выполнение и восстановление` before changing persistence, retries, verification, or handoff behavior.
   - Use `6.5. Полный пример простого workflow` as an end-to-end illustration, not as a second API owner.
3. Keep ownership boundaries intact:
   - concrete workflow domain logic stays in the target workflow-container project,
   - runtime-neutral workflow source models and loaders stay in `workflow-container-contract`,
   - generic runtime code and generic prompt partials stay in `workflow-container-runtime`,
   - browser process launch and profile handling stay in `browser-runtime`,
   - VPN gateway, protocol adapters, SOCKS5, tunnel lifecycle, and validation stay in `vpn-runtime`,
   - authoring guidance and audit tooling stay in this plugin/repository,
   - the generic `goal-brainstorm` skill stays in this plugin while it is incubated and owns only design clarification, document selection, specification and goal authoring, and optional persistent-goal activation,
   - the interactive `workflow-container-input-create` skill stays in this plugin and creates or migrates one complete validated `input.json` without launching a workflow or mutating marketplace state.
4. When writing or rewriting one workflow-container prompt or instruction artifact:
   - identify the artifact role before writing it,
   - use the canonical terms from `1.3. Основные термины`,
   - apply `6.1. Минимальный стабильный контракт` before introducing or changing data objects, result payloads, typed step input, state files, artifact handles, validators, or handoff payloads,
   - keep request and all run-owned settings in one concrete `WorkflowInputT`; do not add a second settings payload, runtime merge chain, hidden default, arbitrary step-config map, or copied step config,
   - choose the appropriate instruction form from `6.3. Правила prompt`,
   - write exact inputs, outputs, state boundaries, and completion behavior when the artifact defines a boundary,
   - write state transitions explicitly when the artifact contains retries, verification loops, blocked states, or recovery,
   - use `4.5. Инкрементальные данные` when significant structured collections are produced item by item,
   - use `5.7. Атомарная публикация и восстановление` for atomic publication, exact snapshot validation, restart, and digest/revision-bound `result.json`/`verification.json` pairing,
   - describe recovery next steps near the failure mode that triggers them,
   - avoid broad suggestions when an exact action or transition is required.
5. After changing workflow-container code or instructions, review the changed or directly affected boundary against `6.1. Минимальный стабильный контракт`:
   - verify the applicable public class, DBOS handoff, artifact tree, validator, transient verification decision, digest/revision-bound `result.json`/`verification.json` pair, incremental state, recovery, contract evolution, and container execution owners,
   - verify that schema, saved Workflow input, saved WorkflowRun input, workflow `input.json`, exact DBOS step config argument, and input migrations preserve one complete typed input contract,
   - remove duplicate owners for the same semantic data, redundant lifecycle or domain decision channels, proxy layers, bridge states, copied schema text, duplicated prompt instructions, validator-owned object reconstruction, and unclear ownership,
   - keep the cleanup scoped to the changed or directly affected boundary unless the user explicitly asks for wider refactoring.
6. Do not require a fixed set of headings for every prompt. Require the instruction form that matches the prompt's role.
7. Use the semantic `workflow-container-audit` skill for instruction audits; do not require a Python CLI audit command from this repository.

Do not add `workflow-container-agent-tools` as a production runtime dependency of a concrete workflow-container project.
