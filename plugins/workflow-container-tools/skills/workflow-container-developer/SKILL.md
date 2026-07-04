---
name: workflow-container-developer
description: Use when developing, auditing, refactoring, or reviewing workflow-container projects, workflow-container runtime packages, browser/VPN runtime integration, DBOS workflow source structure, Codex stage prompts, artifact contracts, or shared workflow-container code quality rules.
---

# Workflow Container Developer

Use this skill for workflow-container ecosystem work. The ecosystem includes concrete workflow containers, `workflow-container-runtime`, `browser-vpn-runtime`, and generic developer tooling.

Before changing workflow contracts, prompt contracts, artifact layout, runtime boundaries, or code quality rules, read `references/workflow-container-authoring.md`.

## Workflow

1. Identify the target repository from the current working directory and its files such as `workflow.yaml`, `versions.yaml`, `pyproject.toml`, `AGENTS.md`, and `doc/design/*.md`.
2. Keep ownership boundaries intact:
   - concrete workflow domain logic stays in the target workflow-container project,
   - generic runtime code and generic prompt partials stay in `workflow-container-runtime`,
   - browser/VPN process launch and profile handling stay in `browser-vpn-runtime`,
   - developer-only guidance and audit tooling stay in this plugin/repository.
3. Apply the code quality baseline from `references/workflow-container-authoring.md`.
4. When the `workflow-container-developer` checkout is available, run `python -m workflow_container_developer.cli audit <target-project>` from that checkout root as a mechanical check. If the checkout is not available, use the reference document checklist directly.

Do not add `workflow-container-developer` as a production runtime dependency of a concrete workflow-container project.
