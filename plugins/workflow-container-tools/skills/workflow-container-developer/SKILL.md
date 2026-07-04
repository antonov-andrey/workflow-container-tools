---
name: workflow-container-developer
description: Use when developing, auditing, refactoring, or reviewing workflow-container projects, workflow-container runtime packages, browser/VPN runtime integration, DBOS workflow source structure, Codex stage prompts, artifact contracts, or shared workflow-container code quality rules.
---

# Workflow Container Developer

Use this skill for workflow-container ecosystem work. The ecosystem includes concrete workflow containers, `workflow-container-runtime`, `browser-vpn-runtime`, and generic developer tooling.

Before changing workflow contracts, prompt contracts, artifact layout, runtime boundaries, or code quality rules, read `references/workflow-container-authoring.md`.

## Workflow

1. Identify the target repository from the current working directory and its files such as `workflow.yaml`, `versions.yaml`, `pyproject.toml`, `AGENTS.md`, and `doc/design/*.md`.
2. Before changing workflow contracts, prompt contracts, artifact layout, runtime boundaries, code quality rules, prompt templates, stage instructions, validator instructions, or recovery instructions, read `references/workflow-container-authoring.md`.
3. Keep ownership boundaries intact:
   - concrete workflow domain logic stays in the target workflow-container project,
   - generic runtime code and generic prompt partials stay in `workflow-container-runtime`,
   - browser/VPN process launch and profile handling stay in `browser-vpn-runtime`,
   - developer-only guidance and audit tooling stay in this plugin/repository.
4. When writing or rewriting one workflow-container prompt or instruction artifact:
   - identify the artifact role before writing it,
   - choose the appropriate instruction form from `Prompt Authoring Contract`,
   - write exact inputs, outputs, state boundaries, and terminal behavior when the artifact defines a boundary,
   - write state transitions explicitly when the artifact contains retries, verification loops, blocked states, or recovery,
   - persist significant structured data at the nearest stable boundary instead of relying on model memory,
   - describe recovery next steps near the failure mode that triggers them,
   - avoid broad suggestions when an exact action or transition is required.
5. Do not require a fixed set of headings for every prompt. Require the instruction form that matches the prompt's role.
6. Use the semantic `workflow-container-audit` skill for instruction audits; do not require a Python CLI audit command from this repository.

Do not add `workflow-container-developer` as a production runtime dependency of a concrete workflow-container project.
