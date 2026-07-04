# Workflow Container Developer

`workflow-container-developer` is a Codex plugin marketplace source for workflow-container development tools.

```text
workflow-container-developer/
  .agents/
    plugins/
      marketplace.json
  plugins/
    workflow-container-tools/
      .codex-plugin/
        plugin.json
      skills/
        workflow-container-developer/
          SKILL.md
          references/
            workflow-container-authoring.md
  workflow_container_developer/
```

The marketplace name is `workflow-container-tools`. The installable plugin is `workflow-container-tools`. The current skill inside that plugin is `workflow-container-developer`. Future workflow-container skills should be added under the same plugin at `plugins/workflow-container-tools/skills/`.

The repository also contains optional Python CLI code for local audits while developing this plugin and adjacent workflow-container projects. Codex plugin installation does not install that Python CLI. Concrete workflow logic stays in the target workflow-container project.

## Local Plugin Install

Run from the `workflow-container-developer` checkout root:

```bash
cd <workflow-container-developer-checkout>
codex plugin marketplace add .
codex plugin add workflow-container-tools@workflow-container-tools
```

Start a new Codex thread after installing or reinstalling the plugin.

## GitHub Plugin Install

```bash
codex plugin marketplace add antonov-andrey/workflow-container-developer --ref main
codex plugin add workflow-container-tools@workflow-container-tools
```

## Update

For a GitHub marketplace source:

```bash
codex plugin marketplace upgrade workflow-container-tools
codex plugin add workflow-container-tools@workflow-container-tools
```

For local development, update the plugin cachebuster when Codex needs to refresh the installed plugin, then reinstall:

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  plugins/workflow-container-tools
codex plugin add workflow-container-tools@workflow-container-tools
```

Start a new Codex thread after reinstalling.

## Optional Local CLI

Run the CLI from the `workflow-container-developer` checkout root without installing the package:

```bash
python -m workflow_container_developer.cli --help
python -m workflow_container_developer.cli list
python -m workflow_container_developer.cli audit <workflow-container-project>
```

The target name is the adjacent project directory name. The CLI discovers workflow-container projects by `workflow.yaml` and `versions.yaml`; it does not know concrete workflow names.

## Development

```bash
python -m pytest -q
python -m compileall workflow_container_developer
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/workflow-container-tools
```
