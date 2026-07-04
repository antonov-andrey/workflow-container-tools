# Repository Guidelines

## Scope
- This project owns reusable authoring instructions, design contracts and generic CLI tooling for adjacent workflow-container projects.
- This project is not a runtime dependency of concrete workflow-container projects.
- Generic tooling must discover target workflow-container projects through declared project files such as `workflow.yaml` and `versions.yaml`.
- Hardcoding concrete target project names in product code is forbidden.
- Target-specific workflow logic, source types, prompts and validators belong only to the target workflow-container project.

## Python
- Python code uses Python 3.14.
- CLI commands must use standard `argparse`.
- Tests must use `pytest`.
