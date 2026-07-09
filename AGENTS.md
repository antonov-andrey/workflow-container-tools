# Repository Guidelines

## Scope
- This project owns reusable authoring instructions, design contracts and optional local discovery CLI tooling for adjacent workflow-container projects.
- This project is not a runtime dependency of concrete workflow-container projects.
- Shared workflow-container ecosystem authoring and code quality rules live in the `workflow-container-developer` plugin reference `references/workflow-container-authoring.md`.
- Optional local discovery tooling must discover target workflow-container projects through declared project metadata files.
- Hardcoding concrete target project names in product code is forbidden.
- Target-specific workflow logic, source types, prompts and validators belong only to the target workflow-container project.

## Plugin
- This repository is a Codex plugin marketplace source named `workflow-container-tools`.
- The installable plugin is `workflow-container-tools`.
- Plugin skills live under `plugins/workflow-container-tools/skills/`.
- Current skills inside that plugin are `workflow-container-developer` and `workflow-container-audit`.
- Add future workflow-container skills under the same plugin instead of creating another install path.

## Python
- Python code uses Python 3.14.
- Python code must be formatted with Black using target version `py314` and line length `120`.
- CLI commands must use standard `argparse`.
- Tests must use `pytest`.
- Tests must not verify instruction artifacts by checking that specific prose, headings, phrases, examples, files, or placement rules exist or do not exist. This includes `AGENTS.md`, `SKILL.md`, plugin reference Markdown, design documents, and prompt authoring guidance. Instruction artifacts are verified by semantic reread or semantic audit, not by pytest assertions over text or instruction artifact paths.
