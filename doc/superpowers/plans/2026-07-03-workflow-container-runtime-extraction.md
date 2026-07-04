# Workflow Container Runtime Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract reusable workflow-container Codex runtime mechanics from `<workflow-container-project>` into the new sibling `workflow-container-runtime` project and make `<workflow-container-project>` consume it as a runtime dependency.

**Architecture:** `workflow-container-runtime` owns generic executable runtime code and generic prompt partial resources. `<workflow-container-project>` keeps domain schemas, workflow orchestration, domain prompts, validators, and size-chart semantics. `workflow-container-developer` owns authoring documentation and generic audits only; it is not imported by runtime containers.

**Tech Stack:** Python 3.14, Pydantic v2, Jinja2, pytest, Codex CLI, package resources.

---

### Task 1: Runtime Project Bootstrap

**Files:**
- Create: `/home/andrey/Projects/workflow-container-runtime/AGENTS.md`
- Create: `/home/andrey/Projects/workflow-container-runtime/README.md`
- Create: `/home/andrey/Projects/workflow-container-runtime/pyproject.toml`
- Create: `/home/andrey/Projects/workflow-container-runtime/workflow_container_runtime/__init__.py`
- Create: `/home/andrey/Projects/workflow-container-runtime/test/test_package.py`

- [ ] Clone `git@github.com:antonov-andrey/workflow-container-runtime.git` into `/home/andrey/Projects/workflow-container-runtime`.
- [ ] Add a minimal Python 3.14 package with strict local `AGENTS.md`: runtime code only, no domain workflow logic, no concrete workflow-container names.
- [ ] Add package metadata with dependencies needed by the extracted runtime: `pydantic>=2.0`, `Jinja2>=3.1.0`.
- [ ] Add a package import smoke test.
- [ ] Run `python -m pytest -q` and `python -m compileall workflow_container_runtime` in the runtime project.

### Task 2: Generic Codex Runner Extraction

**Files:**
- Create: `/home/andrey/Projects/workflow-container-runtime/workflow_container_runtime/artifact/writer.py`
- Create: `/home/andrey/Projects/workflow-container-runtime/workflow_container_runtime/codex/runner.py`
- Create: `/home/andrey/Projects/workflow-container-runtime/workflow_container_runtime/codex/schema.py`
- Create: `/home/andrey/Projects/workflow-container-runtime/test/test_codex_runner.py`
- Modify: `/home/andrey/Projects/<workflow-container-project>/<workflow_container_package>/codex/runner.py`
- Modify: `/home/andrey/Projects/<workflow-container-project>/<workflow_container_package>/codex/schema.py`
- Modify: `/home/andrey/Projects/<workflow-container-project>/<workflow_container_package>/codex/__init__.py`
- Modify: `/home/andrey/Projects/<workflow-container-project>/<workflow_container_package>/codex_stage.py`

- [ ] Move generic JSON artifact writing needed by the runner into runtime without importing `<workflow-container-project>`.
- [ ] Move `CodexStageRunner`, `CodexStageError`, `codex_stage_run`, Codex output schema generation, browser JavaScript/tool validation, subprocess timeout, diagnostics writing, and MCP config construction into runtime.
- [ ] Parameterize project-specific system prompt text through constructor or `run(...)` arguments so runtime does not contain `<workflow-container-project>` strings.
- [ ] Keep `<workflow-container-project>` compatibility modules as thin import surfaces only when needed by current tests/callers, or migrate all imports directly to runtime and delete obsolete local modules.
- [ ] Add runtime unit tests ported from current runner tests for command construction, browser tool validation, stale diagnostic cleanup, timeout/activity behavior, and schema validation.

### Task 3: Prompt Resource Extraction

**Files:**
- Create: `/home/andrey/Projects/workflow-container-runtime/workflow_container_runtime/prompt/renderer.py`
- Create: `/home/andrey/Projects/workflow-container-runtime/workflow_container_runtime/prompt/template/partial/runtime_source_access.md.j2`
- Create: `/home/andrey/Projects/workflow-container-runtime/workflow_container_runtime/prompt/template/partial/artifact_reference_contract.md.j2`
- Create: `/home/andrey/Projects/workflow-container-runtime/workflow_container_runtime/prompt/template/partial/stage_verification_contract.md.j2`
- Create: `/home/andrey/Projects/workflow-container-runtime/test/test_prompt_renderer.py`
- Modify: `/home/andrey/Projects/<workflow-container-project>/<workflow_container_package>/prompt/renderer.py`
- Modify: `/home/andrey/Projects/<workflow-container-project>/<workflow_container_package>/prompt/template/*.md.j2`
- Delete: `/home/andrey/Projects/<workflow-container-project>/<workflow_container_package>/prompt/template/partial/runtime_source_access.md.j2`
- Delete: `/home/andrey/Projects/<workflow-container-project>/<workflow_container_package>/prompt/template/partial/artifact_reference_contract.md.j2`

- [ ] Add a runtime Jinja2 renderer that loads runtime package templates and project template directories together with `StrictUndefined`.
- [ ] Move generic source-access and artifact-reference partials to runtime package resources.
- [ ] Add a generic verification preamble partial in runtime and update `<workflow-container-project>` verification templates to include it before domain-specific checks.
- [ ] Leave `size_group_key_contract.md.j2` and `stage_retry_context.md.j2` in `<workflow-container-project>` because they are domain/stage-specific.
- [ ] Update tests to assert generic partials are no longer local to `<workflow-container-project>` and render through runtime resources.

### Task 4: Dependency Wiring And Documentation

**Files:**
- Modify: `/home/andrey/Projects/<workflow-container-project>/pyproject.toml`
- Modify: `/home/andrey/Projects/<workflow-container-project>/AGENTS.md`
- Modify: `/home/andrey/Projects/<workflow-container-project>/doc/design/<workflow-container-project>.md`
- Modify: `/home/andrey/Projects/workflow-container-developer/doc/design/workflow-container-authoring.md`
- Modify: `/home/andrey/Projects/workflow-container-developer/workflow_container_developer/audit.py`
- Modify: `/home/andrey/Projects/workflow-container-developer/test/test_audit.py`

- [ ] Add `workflow-container-runtime` as an explicit `<workflow-container-project>` dependency through a pinned Git commit dependency.
- [ ] Update `<workflow-container-project>` instructions/design so generic Codex runtime and generic prompt partials belong to `workflow-container-runtime`, not to the domain project.
- [ ] Update `workflow-container-developer` design to describe runtime dependency ownership and forbid importing developer tooling from runtime containers.
- [ ] Extend developer audit to warn when a workflow-container has local copies of runtime-owned generic prompt partials or local implementation of `CodexStageRunner`.

### Task 5: Verification

**Files:**
- Test all changed projects.

- [ ] Run runtime tests: `cd /home/andrey/Projects/workflow-container-runtime && python -m pytest -q && python -m compileall workflow_container_runtime`.
- [ ] Run brand tests: `cd /home/andrey/Projects/<workflow-container-project> && python -m pytest -q && python -m compileall <workflow_container_package>`.
- [ ] Run developer tests and audit: `cd /home/andrey/Projects/workflow-container-developer && python -m pytest -q && python -c 'import workflow_container_developer.cli as cli; raise SystemExit(cli.main(["audit", "<workflow-container-project>"]))'`.
- [ ] Run targeted prompt rendering tests in `<workflow-container-project>` and import smoke checks proving `<workflow-container-project>` imports runtime package code.
- [ ] Report any skipped real external workflow run explicitly; this change is runtime extraction, so unit/contract verification is the required direct check unless the user separately requests a full Defacto production run.
