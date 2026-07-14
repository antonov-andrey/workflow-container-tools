# Workflow Container Tools

`workflow-container-tools` is a Codex plugin marketplace source for generic design and goal brainstorming plus workflow-container authoring, audit, and input-creation skills.

```text
workflow-container-tools/
  .agents/
    plugins/
      marketplace.json
  plugins/
    workflow-container-tools/
      .codex-plugin/
        plugin.json
      skills/
        goal-brainstorm/
          SKILL.md
          references/
            specification-contract.md
        workflow-container-audit/
          SKILL.md
        workflow-container-developer/
          SKILL.md
          references/
            workflow-container-authoring.md
        workflow-container-input-create/
          SKILL.md
          references/
            input-workflow.md
  workflow_container_tools/
```

The marketplace name is `workflow-container-tools`. The installable plugin is `workflow-container-tools`. Current skills inside that plugin are `goal-brainstorm`, `workflow-container-audit`, `workflow-container-developer`, and `workflow-container-input-create`. Future workflow-container skills should be added under the same plugin at `plugins/workflow-container-tools/skills/`.

The repository also contains optional Python CLI helper code for local project discovery while developing this plugin and adjacent workflow-container projects. Codex plugin installation does not install that Python CLI. Generic design clarification, document selection, specification and goal authoring, and optional persistent-goal activation stay in `goal-brainstorm`; concrete workflow logic stays in the target workflow-container project; semantic instruction review stays in `workflow-container-audit`; and interactive complete input preparation stays in `workflow-container-input-create`.

## Local Plugin Install

Run from the `workflow-container-tools` checkout root:

```bash
cd <workflow-container-tools-checkout>
codex plugin marketplace add .
codex plugin add workflow-container-tools@workflow-container-tools
```

Start a new Codex thread after installing or reinstalling the plugin.

## GitHub Plugin Install

```bash
codex plugin marketplace add antonov-andrey/workflow-container-tools --ref main
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

Run the CLI from the `workflow-container-tools` checkout root without installing the package:

```bash
python -m workflow_container_tools.cli --help
python -m workflow_container_tools.cli list
```

The `list` command discovers adjacent workflow-container projects by `workflow.yaml` and `versions.yaml`; it does not know concrete workflow names.

The Python CLI is only a local helper for discovery. Canonical workflow-container instruction review is the semantic `workflow-container-audit` skill, not a Python subcommand in this repository.

## Development

```bash
uv venv --python 3.14
source .venv/bin/activate
uv pip install -e ".[test]"
python -m pytest -q
python -m compileall workflow_container_tools
python ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/workflow-container-tools
```
