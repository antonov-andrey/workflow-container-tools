# workflow-container-developer

Developer workspace and reusable authoring contract for workflow-container projects located beside this repository.

```text
/home/andrey/Projects/
  workflow-container-developer/
  brand-size-chart/
  browser-vpn-runtime/
  marketplace-automation/
  <other-workflow-container>/
```

The project provides generic CLI tools. Concrete workflow logic stays in the target workflow-container project.

## Commands

```bash
workflow-container-dev --help
```

## Typical Flow

```bash
workflow-container-dev list
workflow-container-dev audit brand-size-chart
```

The target name is the adjacent project directory name. The CLI discovers workflow-container projects by `workflow.yaml` and `versions.yaml`; it does not know concrete workflow names.

## Development

```bash
python -m pytest -q
python -m compileall workflow_container_developer
```
