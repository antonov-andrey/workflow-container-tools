# Agent Plugins

`agent-plugins` is a Codex marketplace repository with three independently installable providers:

- `agent-workflows` for reusable task workflows and orchestration;
- `marketplace-agent-tools` for explicitly shared marketplace-domain procedures;
- `workflow-container-agent-tools` for workflow-container authoring, audit, and input preparation.

Application-specific logic and reusable opinionated engineering standards are not owned here. Standards are provided separately by `project-standards`.

## Local Plugin Install

Run from the `agent-plugins` checkout root:

```bash
cd <agent-plugins-checkout>
codex plugin marketplace add .
codex plugin add agent-workflows@agent-plugins
codex plugin add marketplace-agent-tools@agent-plugins
codex plugin add workflow-container-agent-tools@agent-plugins
```

Start a new Codex thread after installing or reinstalling the plugin.

## GitHub Plugin Install

```bash
codex plugin marketplace add antonov-andrey/agent-plugins --ref main
codex plugin add agent-workflows@agent-plugins
codex plugin add marketplace-agent-tools@agent-plugins
codex plugin add workflow-container-agent-tools@agent-plugins
```

## Update

For a GitHub marketplace source:

```bash
codex plugin marketplace upgrade agent-plugins
codex plugin add agent-workflows@agent-plugins
codex plugin add marketplace-agent-tools@agent-plugins
codex plugin add workflow-container-agent-tools@agent-plugins
```

For local development, update the affected plugin cachebuster, then reinstall that plugin:

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  plugins/agent-workflows
codex plugin add agent-workflows@agent-plugins
```

Start a new Codex thread after reinstalling.

## Development

```bash
pytest -q
python ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/agent-workflows
python ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/marketplace-agent-tools
python ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/workflow-container-agent-tools
```
