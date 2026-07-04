# `workflow-container-contract` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Вынести общий контракт `workflow.yaml`, `versions.yaml` и `WorkflowResult` в отдельный runtime-neutral package `workflow-container-contract`, затем подключить его к `marketplace-automation`, `workflow-container-developer` и `brand-size-chart`.

**Architecture:** `workflow-container-contract` становится единственным владельцем Pydantic v2 моделей и loader-ов для файлов workflow-container contract. `marketplace-automation` импортирует эти модели и сохраняет только platform-specific persistence/API glue. Конкретные workflow-container projects используют общий test helper вместо локальных копий contract-validation logic.

**Tech Stack:** Python 3.14, Pydantic v2, PyYAML, pytest, Black line length 120.

---

## File Structure

- Create `/home/andrey/Projects/workflow-container-contract/pyproject.toml`: package metadata, dependencies and tool settings.
- Create `/home/andrey/Projects/workflow-container-contract/AGENTS.md`: minimal public code-quality contract for this runtime-neutral package.
- Create `/home/andrey/Projects/workflow-container-contract/README.md`: package purpose and usage examples.
- Create `/home/andrey/Projects/workflow-container-contract/workflow_container_contract/__init__.py`: public export surface.
- Create `/home/andrey/Projects/workflow-container-contract/workflow_container_contract/model.py`: Pydantic v2 models, `from_path(path)` loaders and SemVer/project-key helpers.
- Create `/home/andrey/Projects/workflow-container-contract/workflow_container_contract/testing.py`: reusable `workflow_contract_file_validate(project_root: Path)` helper.
- Create `/home/andrey/Projects/workflow-container-contract/test/test_model.py`: behavior tests for contract models.
- Create `/home/andrey/Projects/workflow-container-contract/test/test_testing.py`: behavior tests for the reusable test helper.
- Modify `/home/andrey/Projects/marketplace-automation/pyproject.toml`: add path dependency on `workflow-container-contract`.
- Modify `/home/andrey/Projects/marketplace-automation/backend/workflow_config.py`: import contract models from `workflow-container-contract`, keep platform-local manifest/hash/SemVer helpers only.
- Modify `/home/andrey/Projects/marketplace-automation/backend/workflow_run.py`: replace `WorkflowTerminalResult` finalization with `WorkflowResult` envelope finalization and remove platform-field validation from result payload.
- Modify `/home/andrey/Projects/marketplace-automation/backend/api/workflow.py`: replace request model and endpoint naming from terminal result to workflow result where payload contract is container result.
- Modify `/home/andrey/Projects/marketplace-automation/backend/app.py`: remove OpenAPI field descriptions for obsolete platform result fields.
- Modify `/home/andrey/Projects/marketplace-automation/test/backend/test_workflow_config.py`: import shared models and test new `WorkflowResult` contract.
- Modify `/home/andrey/Projects/marketplace-automation/test/backend/test_workflow_run.py`: update finalization tests for `WorkflowResult(status="success"|"failed")`.
- Modify `/home/andrey/Projects/marketplace-automation/test/backend/test_workflow_api.py`: update API terminal/finalization payloads to the new result contract.
- Modify `/home/andrey/Projects/marketplace-automation/doc/design/backend.md`, `/home/andrey/Projects/marketplace-automation/doc/design/data-storage.md`, `/home/andrey/Projects/marketplace-automation/doc/design/persistence.md`, `/home/andrey/Projects/marketplace-automation/doc/design/workflow-runtime.md`: replace stale terminal-result/platform-field wording.
- Modify `/home/andrey/Projects/workflow-container-developer/workflow_container_developer/cli.py`: delete `audit` subcommand.
- Delete `/home/andrey/Projects/workflow-container-developer/workflow_container_developer/audit.py`.
- Delete `/home/andrey/Projects/workflow-container-developer/test/test_audit.py`.
- Modify `/home/andrey/Projects/workflow-container-developer/test/test_cli.py`: remove audit-subcommand tests and keep `list` behavior.
- Modify `/home/andrey/Projects/workflow-container-developer/README.md`: remove Python CLI audit wording and keep semantic `workflow-container-audit` skill wording.
- Modify `/home/andrey/Projects/workflow-container-developer/plugins/workflow-container-tools/skills/workflow-container-developer/SKILL.md`: remove mechanical audit command requirement from workflow step 4.
- Modify `/home/andrey/Projects/brand-size-chart/pyproject.toml`: add path dependency on `workflow-container-contract`.
- Modify `/home/andrey/Projects/brand-size-chart/test/test_workflow_contract.py`: validate real `workflow.yaml`, `versions.yaml` through shared helper and keep any domain-specific assertions that are still needed.

### Task 1: Create Runtime-Neutral Contract Package

**Files:**
- Create: `/home/andrey/Projects/workflow-container-contract/pyproject.toml`
- Create: `/home/andrey/Projects/workflow-container-contract/AGENTS.md`
- Create: `/home/andrey/Projects/workflow-container-contract/README.md`
- Create: `/home/andrey/Projects/workflow-container-contract/workflow_container_contract/__init__.py`
- Create: `/home/andrey/Projects/workflow-container-contract/workflow_container_contract/model.py`
- Create: `/home/andrey/Projects/workflow-container-contract/workflow_container_contract/testing.py`
- Create: `/home/andrey/Projects/workflow-container-contract/test/test_model.py`
- Create: `/home/andrey/Projects/workflow-container-contract/test/test_testing.py`

- [ ] **Step 1: Create failing package tests**

Create tests that assert:

```python
from pathlib import Path

import pytest
from pydantic import ValidationError

from workflow_container_contract import (
    WorkflowDefinition,
    WorkflowResult,
    WorkflowVersionDefinition,
    workflow_project_key_get,
    workflow_version_name_key_get,
)
from workflow_container_contract.testing import workflow_contract_file_validate


def test_workflow_definition_loads_current_contract(tmp_path: Path) -> None:
    workflow_path = tmp_path / "workflow.yaml"
    workflow_path.write_text(
        """
name: sample_workflow
image: sample:0.1.0
command:
  - sample-run
data_source_list:
  - name: secret
    prompt: Secret runtime files.
    is_private: true
    mutable_prefix_list:
      - playwright_profile/**
data_container_list:
  - name: sample_output
    prompt: Output data.
    schema_athena:
      columns: []
runtime_capability_list:
  - name: browser_vpn_runtime
    data_source_name: secret
""".strip(),
        encoding="utf-8",
    )

    workflow_definition = WorkflowDefinition.from_path(workflow_path)

    assert workflow_definition.command_list == ["sample-run"]
    assert workflow_definition.data_source_list[0].match_mutable_path(logical_path="playwright_profile/state.json")
    assert not workflow_definition.data_source_list[0].match_mutable_path(logical_path="../state.json")


def test_workflow_definition_rejects_invalid_names() -> None:
    with pytest.raises(ValidationError):
        WorkflowDefinition.model_validate(
            {
                "name": "sample",
                "image": "sample:0.1.0",
                "command": ["sample-run"],
                "data_source_list": [{"name": "secret", "prompt": "A"}, {"name": "secret", "prompt": "B"}],
            }
        )


def test_workflow_version_definition_loads_contracts(tmp_path: Path) -> None:
    version_path = tmp_path / "versions.yaml"
    version_path.write_text(
        """
project: sample-workflow
version: 1.2.3
contracts:
  workflow: 1
  prompt_set: 2
""".strip(),
        encoding="utf-8",
    )

    version_definition = WorkflowVersionDefinition.from_path(version_path)

    assert version_definition.contract_version_by_name_map == {"workflow": 1, "prompt_set": 2}


def test_workflow_result_allows_domain_fields_and_rejects_platform_fields() -> None:
    workflow_result = WorkflowResult.model_validate(
        {
            "status": "success",
            "message": "ok",
            "error_list": [],
            "brand_result_list": [],
        }
    )

    assert workflow_result.model_extra == {"brand_result_list": []}

    for field_name in ("output_container_id_list", "input_writeback_ref_list", "diagnostic_path_list"):
        with pytest.raises(ValidationError):
            WorkflowResult.model_validate({"status": "success", "message": "ok", field_name: []})


def test_workflow_contract_file_validate_accepts_project_key_aliases(tmp_path: Path) -> None:
    (tmp_path / "workflow.yaml").write_text(
        "name: brand_size_chart\nimage: b:0.1.0\ncommand: [brand-size-chart-run]\n",
        encoding="utf-8",
    )
    (tmp_path / "versions.yaml").write_text(
        "project: brand-size-chart\nversion: 0.1.0\ncontracts:\n  workflow: 1\n",
        encoding="utf-8",
    )

    workflow_contract_file_validate(project_root=tmp_path)


def test_workflow_contract_file_validate_rejects_project_mismatch(tmp_path: Path) -> None:
    (tmp_path / "workflow.yaml").write_text("name: one\nimage: x\ncommand: [run]\n", encoding="utf-8")
    (tmp_path / "versions.yaml").write_text("project: two\nversion: 0.1.0\ncontracts:\n  workflow: 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="workflow.yaml name and versions.yaml project must match"):
        workflow_contract_file_validate(project_root=tmp_path)


def test_project_and_version_helpers_are_stable() -> None:
    assert workflow_project_key_get(project_name="Brand Size-Chart") == "brand_size_chart"
    assert workflow_version_name_key_get(version_name="10.2.3") > workflow_version_name_key_get(version_name="2.9.9")
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd /home/andrey/Projects/workflow-container-contract
python -m pytest -q
```

Expected: fail because the package does not exist yet.

- [ ] **Step 3: Implement package**

Implement:

- strict Pydantic v2 models with `extra="forbid"` for YAML contract models;
- `WorkflowResult` with `extra="allow"` plus a model validator that rejects `output_container_id_list`, `input_writeback_ref_list` and `diagnostic_path_list`;
- `from_path(path)` classmethods on `WorkflowDefinition` and `WorkflowVersionDefinition`;
- `workflow_contract_file_validate(project_root: Path)`;
- stable project-key and SemVer key helpers.

- [ ] **Step 4: Verify package**

Run:

```bash
cd /home/andrey/Projects/workflow-container-contract
black --target-version py314 --line-length 120 workflow_container_contract test
python -m pytest -q
python -m compileall workflow_container_contract
```

Expected: all commands pass.

- [ ] **Step 5: Commit package**

Run:

```bash
cd /home/andrey/Projects/workflow-container-contract
git add AGENTS.md README.md pyproject.toml workflow_container_contract test
git commit -m "Create workflow container contract package"
```

### Task 2: Replace `marketplace-automation` Local Workflow Contract Models

**Files:**
- Modify: `/home/andrey/Projects/marketplace-automation/pyproject.toml`
- Modify: `/home/andrey/Projects/marketplace-automation/backend/workflow_config.py`
- Modify: `/home/andrey/Projects/marketplace-automation/backend/workflow_run.py`
- Modify: `/home/andrey/Projects/marketplace-automation/backend/api/workflow.py`
- Modify: `/home/andrey/Projects/marketplace-automation/backend/app.py`
- Modify: `/home/andrey/Projects/marketplace-automation/test/backend/test_workflow_config.py`
- Modify: `/home/andrey/Projects/marketplace-automation/test/backend/test_workflow_run.py`
- Modify: `/home/andrey/Projects/marketplace-automation/test/backend/test_workflow_api.py`
- Modify: `/home/andrey/Projects/marketplace-automation/doc/design/backend.md`
- Modify: `/home/andrey/Projects/marketplace-automation/doc/design/data-storage.md`
- Modify: `/home/andrey/Projects/marketplace-automation/doc/design/persistence.md`
- Modify: `/home/andrey/Projects/marketplace-automation/doc/design/workflow-runtime.md`

- [ ] **Step 1: Add failing marketplace tests**

Update tests so they assert:

- `backend.workflow_config.WorkflowDefinition` and `WorkflowResult` are imported from `workflow_container_contract`;
- `WorkflowResult(status="success", message="ok")` is accepted;
- `WorkflowResult` rejects the three obsolete platform fields;
- workflow run finalization with `status="success"` marks the run done;
- workflow run finalization with `status="failed"` marks the run failed and stores `message`/`error_list` in the existing error fields without expecting output/writeback/diagnostic payload lists;
- API finalization payload no longer accepts or requires `output_container_id_list`, `input_writeback_ref_list` or `diagnostic_path_list`.

- [ ] **Step 2: Run targeted tests to verify failure**

Run:

```bash
cd /home/andrey/Projects/marketplace-automation
python -m pytest test/backend/test_workflow_config.py test/backend/test_workflow_run.py test/backend/test_workflow_api.py -q
```

Expected: fail on stale `WorkflowTerminalResult` imports and obsolete platform fields.

- [ ] **Step 3: Replace local models**

In `backend/workflow_config.py`:

- import `WorkflowDataContainerDefinition`, `WorkflowDataSourceDefinition`, `WorkflowDataSourceManifest`, `WorkflowDefinition`, `WorkflowResult`, `WorkflowRuntimeCapabilityDefinition`, `WorkflowVersionDefinition`, `workflow_project_key_get` and `workflow_version_name_key_get` from `workflow_container_contract`;
- keep only marketplace-local manifest JSON/SHA helpers when they are still needed by platform persistence;
- delete local definitions that duplicate the new package models;
- delete `WorkflowTerminalResult`.

- [ ] **Step 4: Update workflow run finalization**

In `backend/workflow_run.py`:

- rename terminal-result parameter types and local wording to `WorkflowResult`;
- remove result-payload validation for output container ids and input writeback refs;
- map `WorkflowResult.status == "success"` to `WORKFLOW_RUN_STATUS_DONE`;
- map `WorkflowResult.status == "failed"` to `WORKFLOW_RUN_STATUS_FAILED`;
- populate platform error fields from `WorkflowResult.message` and `WorkflowResult.error_list` using the existing storage shape already used for failed runs.

- [ ] **Step 5: Update API and docs**

In `backend/api/workflow.py` and docs:

- replace request model import with `WorkflowResult`;
- keep endpoint behavior aligned with current route names unless tests show the public route itself already uses obsolete naming;
- remove docs that say the container result owns `output_container_id_list`, `input_writeback_ref_list` or `diagnostic_path_list`;
- keep platform writeback/storage responsibility documented as executor/platform behavior, not container result payload behavior.

- [ ] **Step 6: Verify marketplace changes**

Run:

```bash
cd /home/andrey/Projects/marketplace-automation
black --target-version py314 --line-length 120 backend/workflow_config.py backend/workflow_run.py backend/api/workflow.py backend/app.py test/backend/test_workflow_config.py test/backend/test_workflow_run.py test/backend/test_workflow_api.py
python -m pytest test/backend/test_workflow_config.py test/backend/test_workflow_run.py test/backend/test_workflow_api.py -q
```

Expected: all commands pass.

- [ ] **Step 7: Commit marketplace changes**

Run:

```bash
cd /home/andrey/Projects/marketplace-automation
git add pyproject.toml backend/workflow_config.py backend/workflow_run.py backend/api/workflow.py backend/app.py test/backend/test_workflow_config.py test/backend/test_workflow_run.py test/backend/test_workflow_api.py doc/design/backend.md doc/design/data-storage.md doc/design/persistence.md doc/design/workflow-runtime.md
git commit -m "Use workflow container contract models"
```

### Task 3: Remove Python CLI Audit From `workflow-container-developer`

**Files:**
- Delete: `/home/andrey/Projects/workflow-container-developer/workflow_container_developer/audit.py`
- Delete: `/home/andrey/Projects/workflow-container-developer/test/test_audit.py`
- Modify: `/home/andrey/Projects/workflow-container-developer/workflow_container_developer/cli.py`
- Modify: `/home/andrey/Projects/workflow-container-developer/test/test_cli.py`
- Modify: `/home/andrey/Projects/workflow-container-developer/README.md`
- Modify: `/home/andrey/Projects/workflow-container-developer/plugins/workflow-container-tools/skills/workflow-container-developer/SKILL.md`

- [ ] **Step 1: Update tests for removed audit command**

Remove audit behavior tests. Keep or add CLI tests that verify:

- `workflow-container-dev --help` lists only supported commands;
- `workflow-container-dev list` still discovers adjacent workflow-container projects;
- `workflow-container-dev audit ...` is not a supported command.

- [ ] **Step 2: Run tests to verify failure before implementation**

Run:

```bash
cd /home/andrey/Projects/workflow-container-developer
python -m pytest test/test_cli.py -q
```

Expected: fail until CLI and tests agree on removed audit behavior.

- [ ] **Step 3: Remove audit implementation**

Delete `workflow_container_developer/audit.py` and `test/test_audit.py`. Remove `WorkflowContainerAudit` import and `audit` subparser from `workflow_container_developer/cli.py`.

- [ ] **Step 4: Update docs and skill wording**

Update README and `plugins/workflow-container-tools/skills/workflow-container-developer/SKILL.md` so they do not instruct users to run the removed Python CLI audit. Keep `workflow-container-audit` as a semantic skill, not a Python subcommand.

- [ ] **Step 5: Verify developer changes**

Run:

```bash
cd /home/andrey/Projects/workflow-container-developer
black --target-version py314 --line-length 120 workflow_container_developer test
python -m pytest -q
python -m compileall workflow_container_developer
rg -n "workflow_container_developer\\.audit|WorkflowContainerAudit|workflow-container-dev audit| cli audit|audit <" README.md AGENTS.md plugins workflow_container_developer test
```

Expected: tests and compileall pass; `rg` has no stale Python CLI audit references except semantic `workflow-container-audit` skill names.

- [ ] **Step 6: Commit developer changes and spec/plan**

Run:

```bash
cd /home/andrey/Projects/workflow-container-developer
git add README.md plugins workflow_container_developer test doc/superpowers/specs/2026-07-04-workflow-container-contract-design.md doc/superpowers/plans/2026-07-04-workflow-container-contract.md
git add -u
git commit -m "Remove workflow container CLI audit"
```

### Task 4: Add Contract File Validation To `brand-size-chart`

**Files:**
- Modify: `/home/andrey/Projects/brand-size-chart/pyproject.toml`
- Modify: `/home/andrey/Projects/brand-size-chart/test/test_workflow_contract.py`

- [ ] **Step 1: Add dependency and test**

Update `pyproject.toml` to depend on adjacent `workflow-container-contract`. Update `test/test_workflow_contract.py` to call:

```python
from pathlib import Path

from workflow_container_contract.testing import workflow_contract_file_validate


def test_workflow_contract_file_validate() -> None:
    workflow_contract_file_validate(project_root=Path.cwd())
```

Keep any existing `brand-size-chart`-specific test assertions that are not duplicate YAML contract validation.

- [ ] **Step 2: Run brand tests**

Run:

```bash
cd /home/andrey/Projects/brand-size-chart
black --target-version py314 --line-length 120 test/test_workflow_contract.py
python -m pytest test/test_workflow_contract.py -q
python -m pytest -q
```

Expected: all commands pass.

- [ ] **Step 3: Commit brand changes**

Run:

```bash
cd /home/andrey/Projects/brand-size-chart
git add pyproject.toml test/test_workflow_contract.py
git commit -m "Validate workflow contract files"
```

### Task 5: Cross-Project Verification

**Files:**
- No expected source edits.

- [ ] **Step 1: Verify stale terms across active projects**

Run:

```bash
for project in workflow-container-contract marketplace-automation workflow-container-developer brand-size-chart; do
  cd "/home/andrey/Projects/${project}"
  printf '%s\n' "== ${project} =="
  rg -n "WorkflowTerminalResult|terminal_result\\.json|workflow_container_developer\\.audit|WorkflowContainerAudit" backend workflow_container_developer plugins README.md AGENTS.md test || true
  rg -n "output_container_id_list|input_writeback_ref_list|diagnostic_path_list" workflow_container_contract backend plugins README.md AGENTS.md || true
done
```

Expected: no stale runtime references. `output_container_id_list`, `input_writeback_ref_list` and `diagnostic_path_list` may appear only in `workflow-container-contract` and marketplace negative tests that assert they are forbidden.

- [ ] **Step 2: Run project test suites**

Run:

```bash
cd /home/andrey/Projects/workflow-container-contract && python -m pytest -q && python -m compileall workflow_container_contract
cd /home/andrey/Projects/workflow-container-developer && python -m pytest -q && python -m compileall workflow_container_developer
cd /home/andrey/Projects/marketplace-automation && python -m pytest test/backend/test_workflow_config.py test/backend/test_workflow_run.py test/backend/test_workflow_api.py -q
cd /home/andrey/Projects/brand-size-chart && python -m pytest -q
```

Expected: all commands pass.

- [ ] **Step 3: Verify git state**

Run:

```bash
for project in workflow-container-contract marketplace-automation workflow-container-developer brand-size-chart; do
  cd "/home/andrey/Projects/${project}"
  git status --short --branch
done
```

Expected: each project is clean or only has intentional untracked local runtime files ignored by git.
