# Workflow Container Developer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `workflow-container-developer` as the shared authoring workspace and generic CLI/tooling owner for adjacent workflow-container projects.

**Architecture:** `workflow-container-developer` owns only reusable authoring contracts and generic developer tools. `marketplace-automation` keeps platform runtime contracts, `browser-vpn-runtime` keeps browser/VPN runtime contracts, and each workflow-container keeps only its domain-specific workflow logic and local specialization. The CLI scans adjacent projects through declared markers such as `workflow.yaml` and `versions.yaml`; it must not hardcode target project names.

**Tech Stack:** Python 3.14, pytest, PyYAML, standard-library `argparse`, standard-library `dataclasses`, Markdown design docs.

---

## File Structure

- Create `AGENTS.md` in `workflow-container-developer`: project-local rules for authoring workflow-container projects.
- Create `README.md` in `workflow-container-developer`: entrypoint documentation for humans.
- Create `pyproject.toml` in `workflow-container-developer`: package metadata, local CLI package and test config.
- Create `workflow_container_developer/__init__.py`: package marker.
- Create `workflow_container_developer/cli.py`: direct CLI entrypoint with `main()`.
- Create `workflow_container_developer/project.py`: adjacent project discovery, target loading and command execution primitives.
- Create `workflow_container_developer/audit.py`: generic contract audits over target workflow-container files.
- Create `test/test_project.py`, `test/test_audit.py`, and `test/test_cli.py`: behavior tests for generic discovery/audit/CLI behavior.
- Create `doc/design/workflow-container-authoring.md`: canonical reusable workflow-container authoring contract.
- Modify `doc/superpowers/specs/2026-07-03-workflow-container-developer-design.md`: keep it aligned with implemented file names.
- Modify `<projects-root>/marketplace-automation/doc/design/workflow-runtime.md`: remove workflow-container authoring ownership and reference `workflow-container-developer`.
- Modify `<projects-root>/<workflow-container-project>/AGENTS.md`: keep only local domain/runtime facts and reference `workflow-container-developer` for common workflow-container authoring rules.
- Modify `<projects-root>/<workflow-container-project>/doc/design/<workflow-container-project>.md`: keep domain-specific rules and replace common authoring paragraphs with references to `workflow-container-developer`.

## Task 1: Bootstrap `workflow-container-developer`

**Files:**
- Create: `AGENTS.md`
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `workflow_container_developer/__init__.py`
- Test: `test/test_cli.py`

- [ ] **Step 1: Write CLI import test**

Create `test/test_cli.py`:

```python
"""Tests for the workflow-container-developer CLI."""

from workflow_container_developer.cli import main


def test_main_is_importable() -> None:
    """Verify the CLI entrypoint can be imported."""

    assert callable(main)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest test/test_cli.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'workflow_container_developer'`.

- [ ] **Step 3: Add package metadata**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling>=1.27"]
build-backend = "hatchling.build"

[project]
name = "workflow-container-developer"
version = "0.1.0"
description = "Developer workspace and generic tooling for adjacent workflow-container projects"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
  "PyYAML>=6.0.2",
  "pytest>=8.4.0",
]


[tool.hatch.build.targets.wheel]
packages = ["workflow_container_developer"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["test"]
```

- [ ] **Step 4: Add package and CLI skeleton**

Create `workflow_container_developer/__init__.py`:

```python
"""Developer tooling for workflow-container projects."""
```

Create `workflow_container_developer/cli.py`:

```python
"""Command line interface for workflow-container developer tooling."""

import argparse


def main() -> int:
    """Run the workflow-container developer CLI.

    Returns:
        Process exit code.
    """

    parser = argparse.ArgumentParser(prog="python -m workflow_container_developer.cli")
    parser.add_argument("--version", action="version", version="workflow-container-developer cli 0.1.0")
    parser.parse_args()
    return 0
```

- [ ] **Step 5: Add project instructions and README**

Create `AGENTS.md`:

```markdown
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
```

Create `README.md`:

```markdown
# workflow-container-developer

Developer workspace and reusable authoring contract for workflow-container projects located beside this repository.

```text
<projects-root>/
  workflow-container-developer/
  <workflow-container-project>/
  browser-vpn-runtime/
  marketplace-automation/
  <other-workflow-container>/
```

The project provides generic CLI tools. Concrete workflow logic stays in the target workflow-container project.

## Commands

```bash
python -m workflow_container_developer.cli --help
```

## Development

```bash
python -m pytest -q
python -m compileall workflow_container_developer
```
```

- [ ] **Step 6: Run verification**

Run:

```bash
python -m pytest test/test_cli.py -q
python -m compileall workflow_container_developer
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```bash
git add AGENTS.md README.md pyproject.toml workflow_container_developer test/test_cli.py
git commit -m "Bootstrap workflow container developer tooling"
```

## Task 2: Generic Adjacent Project Discovery

**Files:**
- Create: `workflow_container_developer/project.py`
- Modify: `workflow_container_developer/cli.py`
- Test: `test/test_project.py`
- Test: `test/test_cli.py`

- [ ] **Step 1: Write discovery tests**

Create `test/test_project.py`:

```python
"""Tests for adjacent workflow-container project discovery."""

from pathlib import Path

from workflow_container_developer.project import WorkflowContainerProjectFinder


def _project_create(root: Path, name: str) -> Path:
    project_path = root / name
    project_path.mkdir()
    (project_path / "workflow.yaml").write_text("name: sample\n", encoding="utf-8")
    (project_path / "versions.yaml").write_text("project: sample\nversion: 0.1.0\n", encoding="utf-8")
    return project_path


def test_project_list_get_finds_adjacent_workflow_container(tmp_path: Path) -> None:
    """Find projects through workflow markers without hardcoded names."""

    developer_path = tmp_path / "workflow-container-developer"
    developer_path.mkdir()
    target_path = _project_create(tmp_path, "sample-container")
    (tmp_path / "ordinary-project").mkdir()

    finder = WorkflowContainerProjectFinder(developer_path=developer_path)

    assert [project.path for project in finder.project_list_get()] == [target_path]


def test_project_get_rejects_unknown_target(tmp_path: Path) -> None:
    """Reject target names that do not resolve to adjacent workflow-container projects."""

    developer_path = tmp_path / "workflow-container-developer"
    developer_path.mkdir()
    finder = WorkflowContainerProjectFinder(developer_path=developer_path)

    try:
        finder.project_get("missing")
    except ValueError as error:
        assert "Unknown workflow-container project" in str(error)
    else:
        raise AssertionError("Expected ValueError")
```

Append to `test/test_cli.py`:

```python
from pathlib import Path


def test_cli_list_outputs_adjacent_project(tmp_path: Path, capsys) -> None:
    """List adjacent workflow-container projects."""

    developer_path = tmp_path / "workflow-container-developer"
    developer_path.mkdir()
    target_path = tmp_path / "sample-container"
    target_path.mkdir()
    (target_path / "workflow.yaml").write_text("name: sample\n", encoding="utf-8")
    (target_path / "versions.yaml").write_text("project: sample\nversion: 0.1.0\n", encoding="utf-8")

    assert main(["--developer-path", str(developer_path), "list"]) == 0

    captured = capsys.readouterr()
    assert "sample-container" in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest test/test_project.py test/test_cli.py -q
```

Expected: FAIL because `WorkflowContainerProjectFinder` and CLI arguments are not implemented.

- [ ] **Step 3: Implement discovery model**

Create `workflow_container_developer/project.py`:

```python
"""Workflow-container project discovery and command configuration."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkflowContainerProject:
    """Adjacent workflow-container project metadata."""

    name: str
    path: Path


class WorkflowContainerProjectFinder:
    """Find workflow-container projects adjacent to this developer workspace."""

    def __init__(self, *, developer_path: Path) -> None:
        """Initialize the finder.

        Args:
            developer_path: Path to the workflow-container-developer checkout.
        """

        self._developer_path = developer_path.resolve()
        self._workspace_path = self._developer_path.parent

    def project_get(self, name: str) -> WorkflowContainerProject:
        """Return one adjacent workflow-container project by directory name.

        Args:
            name: Target project directory name.

        Returns:
            Matching workflow-container project.

        Raises:
            ValueError: No adjacent workflow-container project has that name.
        """

        for project in self.project_list_get():
            if project.name == name:
                return project
        raise ValueError(f"Unknown workflow-container project: {name}")

    def project_list_get(self) -> list[WorkflowContainerProject]:
        """Return adjacent workflow-container projects sorted by name.

        Returns:
            Sorted adjacent workflow-container project list.
        """

        project_list: list[WorkflowContainerProject] = []
        for path in sorted(self._workspace_path.iterdir()):
            if path == self._developer_path or not path.is_dir():
                continue
            if (path / "workflow.yaml").is_file() and (path / "versions.yaml").is_file():
                project_list.append(WorkflowContainerProject(name=path.name, path=path))
        return project_list
```

- [ ] **Step 4: Update CLI**

Replace `workflow_container_developer/cli.py` with:

```python
"""Command line interface for workflow-container developer tooling."""

import argparse
from pathlib import Path

from workflow_container_developer.project import WorkflowContainerProjectFinder


def main(argv: list[str] | None = None) -> int:
    """Run the workflow-container developer CLI.

    Args:
        argv: Optional argument list for tests.

    Returns:
        Process exit code.
    """

    parser = argparse.ArgumentParser(prog="python -m workflow_container_developer.cli")
    parser.add_argument("--developer-path", default=Path.cwd(), type=Path)
    parser.add_argument("--version", action="version", version="workflow-container-developer cli 0.1.0")
    subparser = parser.add_subparsers(dest="command", required=True)
    subparser.add_parser("list")
    args = parser.parse_args(argv)

    finder = WorkflowContainerProjectFinder(developer_path=args.developer_path)
    if args.command == "list":
        for project in finder.project_list_get():
            print(f"{project.name}\t{project.path}")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run verification**

Run:

```bash
python -m pytest test/test_project.py test/test_cli.py -q
python -m compileall workflow_container_developer
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add workflow_container_developer test
git commit -m "Add adjacent workflow container discovery"
```

## Task 3: Generic Contract Audit CLI

**Files:**
- Create: `workflow_container_developer/audit.py`
- Modify: `workflow_container_developer/cli.py`
- Test: `test/test_audit.py`
- Test: `test/test_cli.py`

- [ ] **Step 1: Write audit tests**

Create `test/test_audit.py`:

```python
"""Tests for generic workflow-container contract audits."""

from pathlib import Path

from workflow_container_developer.audit import WorkflowContainerAudit
from workflow_container_developer.project import WorkflowContainerProject


def _target_create(tmp_path: Path) -> Path:
    target_path = tmp_path / "target"
    target_path.mkdir()
    (target_path / "workflow.yaml").write_text("name: target\ncommand:\n  - target-run\n", encoding="utf-8")
    (target_path / "versions.yaml").write_text("project: target\nversion: 0.1.0\n", encoding="utf-8")
    (target_path / "AGENTS.md").write_text("# Repository Guidelines\n", encoding="utf-8")
    (target_path / "doc" / "design").mkdir(parents=True)
    (target_path / "doc" / "design" / "target.md").write_text("# Target\n", encoding="utf-8")
    return target_path


def test_audit_result_success_for_valid_project(tmp_path: Path) -> None:
    """Accept a target with required project-owned contract files."""

    target_path = _target_create(tmp_path)
    project = WorkflowContainerProject(name="target", path=target_path)

    result = WorkflowContainerAudit(project=project).result_get()

    assert result.is_ok
    assert result.error_list == []


def test_audit_result_fails_when_agents_missing(tmp_path: Path) -> None:
    """Report missing project-local instructions."""

    target_path = _target_create(tmp_path)
    (target_path / "AGENTS.md").unlink()
    project = WorkflowContainerProject(name="target", path=target_path)

    result = WorkflowContainerAudit(project=project).result_get()

    assert not result.is_ok
    assert "Missing AGENTS.md" in result.error_list
```

Append to `test/test_cli.py`:

```python
def test_cli_audit_reports_success(tmp_path: Path, capsys) -> None:
    """Audit a selected adjacent workflow-container project."""

    developer_path = tmp_path / "workflow-container-developer"
    developer_path.mkdir()
    target_path = tmp_path / "sample-container"
    target_path.mkdir()
    (target_path / "workflow.yaml").write_text("name: sample\ncommand:\n  - sample-run\n", encoding="utf-8")
    (target_path / "versions.yaml").write_text("project: sample\nversion: 0.1.0\n", encoding="utf-8")
    (target_path / "AGENTS.md").write_text("# Repository Guidelines\n", encoding="utf-8")
    (target_path / "doc" / "design").mkdir(parents=True)
    (target_path / "doc" / "design" / "sample.md").write_text("# Sample\n", encoding="utf-8")

    assert main(["--developer-path", str(developer_path), "audit", "sample-container"]) == 0

    captured = capsys.readouterr()
    assert "OK sample-container" in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest test/test_audit.py test/test_cli.py -q
```

Expected: FAIL because audit code and CLI subcommand do not exist.

- [ ] **Step 3: Implement generic audit**

Create `workflow_container_developer/audit.py`:

```python
"""Generic workflow-container project audit."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from workflow_container_developer.project import WorkflowContainerProject


@dataclass(frozen=True)
class WorkflowContainerAuditResult:
    """Workflow-container audit result."""

    error_list: list[str] = field(default_factory=list)
    warning_list: list[str] = field(default_factory=list)

    @property
    def is_ok(self) -> bool:
        """Return whether the audit has no errors.

        Returns:
            True when no errors exist.
        """

        return not self.error_list


class WorkflowContainerAudit:
    """Run generic contract checks for one workflow-container project."""

    def __init__(self, *, project: WorkflowContainerProject) -> None:
        """Initialize the audit.

        Args:
            project: Target workflow-container project.
        """

        self._project = project

    def result_get(self) -> WorkflowContainerAuditResult:
        """Run audit checks.

        Returns:
            Audit result.
        """

        error_list: list[str] = []
        warning_list: list[str] = []
        self._required_file_check("workflow.yaml", error_list)
        self._required_file_check("versions.yaml", error_list)
        self._required_file_check("AGENTS.md", error_list)
        self._design_check(error_list)
        self._workflow_yaml_check(error_list)
        self._prompt_duplicate_check(warning_list)
        return WorkflowContainerAuditResult(error_list=error_list, warning_list=warning_list)

    def _design_check(self, error_list: list[str]) -> None:
        design_path = self._project.path / "doc" / "design"
        if not design_path.is_dir() or not list(design_path.glob("*.md")):
            error_list.append("Missing doc/design/*.md")

    def _prompt_duplicate_check(self, warning_list: list[str]) -> None:
        prompt_path = self._project.path / self._project.name.replace("-", "_") / "prompt"
        if prompt_path.is_dir() and list(prompt_path.glob("*.md")):
            warning_list.append("Root-level prompt markdown files found; use template tree")

    def _required_file_check(self, relative_path: str, error_list: list[str]) -> None:
        if not (self._project.path / relative_path).is_file():
            error_list.append(f"Missing {relative_path}")

    def _workflow_yaml_check(self, error_list: list[str]) -> None:
        workflow_path = self._project.path / "workflow.yaml"
        if not workflow_path.is_file():
            return
        payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            error_list.append("workflow.yaml must be a mapping")
            return
        for key in ["name", "command"]:
            if key not in payload:
                error_list.append(f"workflow.yaml missing {key}")
```

- [ ] **Step 4: Add audit subcommand**

Update `workflow_container_developer/cli.py` to import `WorkflowContainerAudit` and add:

```python
from workflow_container_developer.audit import WorkflowContainerAudit
```

Add subparser:

```python
audit_parser = subparser.add_parser("audit")
audit_parser.add_argument("target")
```

Add command branch before the final assertion:

```python
if args.command == "audit":
    project = finder.project_get(args.target)
    result = WorkflowContainerAudit(project=project).result_get()
    for warning in result.warning_list:
        print(f"WARNING {warning}")
    if result.is_ok:
        print(f"OK {project.name}")
        return 0
    for error in result.error_list:
        print(f"ERROR {error}")
    return 1
```

- [ ] **Step 5: Run verification**

Run:

```bash
python -m pytest test/test_audit.py test/test_cli.py -q
python -m compileall workflow_container_developer
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add workflow_container_developer test
git commit -m "Add generic workflow container audit"
```

## Task 4: Move Common Authoring Contract To `workflow-container-developer`

**Files:**
- Create: `doc/design/workflow-container-authoring.md`
- Modify: `doc/superpowers/specs/2026-07-03-workflow-container-developer-design.md`
- Modify: `<projects-root>/marketplace-automation/doc/design/workflow-runtime.md`
- Modify: `<projects-root>/<workflow-container-project>/AGENTS.md`
- Modify: `<projects-root>/<workflow-container-project>/doc/design/<workflow-container-project>.md`

- [ ] **Step 1: Create authoring design document**

Create `doc/design/workflow-container-authoring.md` with the reusable authoring contract:

```markdown
# Workflow Container Authoring

## Назначение
Этот документ владеет общим контрактом разработки workflow-container проектов. Он описывает, как писать `DBOS` workflow source, `Codex` stages, prompt templates, validators and artifacts. Runtime platform belongs to `marketplace-automation`; browser/VPN runtime belongs to `browser-vpn-runtime`; domain logic belongs to each concrete workflow-container project.

## `DBOS` Workflow Source
`Workflow Source`, который использует `DBOS`, должен оформлять `workflow` и `step` владельцев как `@DBOS.dbos_class` классы с instance-method методами.

Экземпляры таких классов должны быть stateless. Все durable данные запуска должны передаваться явными аргументами `DBOS` метода. `self` может хранить только stateless dependencies: factories, registries, validators, artifact layout, prompt loader, `Codex` runner и другие неизменяемые сервисы без run-specific mutable state.

`DBOS` workflow method владеет deterministic orchestration. `DBOS` step method владеет одной side-effect phase. Browser, network, filesystem writes, `Codex`, secret access и другие external IO должны выполняться только внутри `DBOS` steps или до старта root workflow.

`Workflow Source` должен разделять platform runtime contract, `DBOS` workflow layer, `DBOS` step layer, semantic stage layer, validator layer и artifact layer.

## `Codex` Stage
Codex-backed stage должен состоять из action stage и verification stage. Action stage name должен иметь форму `{object}_{action}`, где `{action}` является глаголом. Verification stage name должен быть action stage name с постфиксом `_verify`.

Action stage пишет `result.json`. Verification stage пишет `verification.json` в тот же stage directory и не владеет отдельным artifact namespace. Verification failure возвращается как feedback в тот же action stage до достижения attempt limit. Отдельные fix stages запрещены.

Prompt каждого Codex-backed stage должен быть одним полным Jinja2 template-файлом. `Workflow Source` должен рендерить template через typed context object и strict undefined handling. Python code не должен хранить human-readable stage instructions в multiline strings.

`Codex` output должен валидироваться на границе runner-а через JSON schema, сгенерированную из Pydantic model stage result. Stage code может записывать `result.json` только после успешной schema/model validation.

## Artifact Materialization
Codex-backed action stage различает generated artifacts и external artifact references.

Generated artifacts принадлежат текущему stage. Они создаются самим stage или детерминированно материализуются из validated stage result.

External artifact references указывают на файлы, созданные другой run-owned системой или предыдущим stage. Codex-backed action stage не должен копировать такие файлы. Он должен вернуть references в своем schema-valid result.

`Workflow Source` должен иметь generic artifact materialization layer. Этот layer получает references из validated stage result, проверяет принадлежность каждого source path разрешенному run artifact root, нормализует references для текущего output bundle, копирует файл только когда declarative workflow policy требует stage-owned copy, иначе сохраняет normalized reference.

`DBOS` step считается завершенным только после durable записи `result.json`, `verification.json` и всех generated artifacts, необходимых для автоматического восстановления после restart с этого или следующего step.

## Browser Runtime Boundary
Workflow source получает browser runtime как готовый `MCP` URL. Source code workflow может передать этот URL в `Codex`, но не владеет настройками OpenVPN, stealth, browser flags, user agent, locale, timezone, viewport, profile materialization или выбором Playwright `MCP` package.

Workflow source не должен запускать прямые `@playwright/mcp`, `npx`, OpenVPN или альтернативные browser/VPN launchers.

## Проверки
Contract tests for workflow-container projects should verify stage naming, complete Jinja2 templates for action and verification stages, absence of human-readable stage instructions in Python multiline strings, schema validation on runner boundary and generic artifact materialization without browser-specific copies inside `Codex` stage.
```

- [ ] **Step 2: Trim platform runtime design**

In `<projects-root>/marketplace-automation/doc/design/workflow-runtime.md`, keep sections `Назначение`, `Сетевой Контракт`, `secret DataSource`, and `Граница Реализации`. Replace sections `Структура DBOS Workflow Source`, `Контракт Codex Stage`, `Контракт Artifact Materialization`, and related checks with:

```markdown
## Граница Authoring Contract
Внутренний контракт написания workflow-container projects принадлежит `workflow-container-developer/doc/design/workflow-container-authoring.md`. `marketplace-automation` не владеет структурой `DBOS` классов, `Codex` stage loop, prompt templates, semantic validators, artifact materialization rules или domain-specific workflow logic.

`marketplace-automation` проверяет только platform-facing contract: `workflow.yaml`, snapshots `DataSource`, output `DataContainer`, runtime capabilities, terminal result, input writeback и статус `WorkflowRun`.
```

- [ ] **Step 3: Trim `<workflow-container-project>` instructions**

Replace `<projects-root>/<workflow-container-project>/AGENTS.md` with:

```markdown
# Repository Guidelines

## Scope
- This project owns the `<workflow-container-project>` workflow-container domain logic.
- Shared workflow-container authoring rules belong to `workflow-container-developer/doc/design/workflow-container-authoring.md`.
- Browser/VPN runtime behavior belongs to `browser-vpn-runtime`.
- This project must not depend on `workflow-container-developer` at runtime.

## Workflow Container Domain
- Runtime chart output lives under `<workflow_container_package>/brand/<parsed_brand_key>/`.
- Audit output lives under `<workflow_container_package>_audit/brand/<parsed_brand_key>/`.
- Static prompts live under `<workflow_container_package>/prompt/template/` with shared partials under `<workflow_container_package>/prompt/template/partial/`.
- Root-level Markdown prompt copies under `<workflow_container_package>/prompt/*.md` are forbidden.
```

- [ ] **Step 4: Trim `<workflow-container-project>` design**

In `<projects-root>/<workflow-container-project>/doc/design/<workflow-container-project>.md`, keep domain sections and replace common production runtime paragraphs about DBOS, `.secret`, Codex sandbox, prompt template placement and artifact materialization with one section:

```markdown
## Общий Workflow-Container Contract
Общие правила `DBOS` workflow source, action/verification stage loop, prompt templates, schema validation, artifact materialization and browser runtime boundary belong to `workflow-container-developer/doc/design/workflow-container-authoring.md`. This document defines only `<workflow-container-project>` domain behavior: source types, source discovery semantics, table extraction semantics, `size_group_key`, mechanical domain guards and output paths.
```

- [ ] **Step 5: Run semantic text checks**

Run:

```bash
rg -n "Структура DBOS Workflow Source|Контракт Codex Stage|Контракт Artifact Materialization" <projects-root>/marketplace-automation/doc/design/workflow-runtime.md <projects-root>/<workflow-container-project>/doc/design/<workflow-container-project>.md
```

Expected: no matches.

Run:

```bash
rg -n "workflow-container-authoring" <projects-root>/marketplace-automation/doc/design/workflow-runtime.md <projects-root>/<workflow-container-project>/AGENTS.md <projects-root>/<workflow-container-project>/doc/design/<workflow-container-project>.md
```

Expected: matches in all three files.

- [ ] **Step 6: Commit docs in each repository**

Run in `<projects-root>/workflow-container-developer`:

```bash
git add doc
git commit -m "Own workflow container authoring contract"
```

Run in `<projects-root>/marketplace-automation`:

```bash
git add doc/design/workflow-runtime.md
git commit -m "Reference external workflow authoring contract"
```

Run in `<projects-root>/<workflow-container-project>`:

```bash
git add AGENTS.md doc/design/<workflow-container-project>.md
git commit -m "Keep workflow container docs domain-specific"
```

## Task 5: Generic Verification Against `<workflow-container-project>`

**Files:**
- Modify: `README.md`
- Modify: `doc/superpowers/specs/2026-07-03-workflow-container-developer-design.md`

- [ ] **Step 1: Run generic CLI against real adjacent target**

Run in `<projects-root>/workflow-container-developer`:

```bash
python -m workflow_container_developer.cli list
python -m workflow_container_developer.cli audit <workflow-container-project>
```

Expected:

```text
<workflow-container-project>	<projects-root>/<workflow-container-project>
OK <workflow-container-project>
```

Additional adjacent workflow-container projects may also appear in `list`; `audit <workflow-container-project>` must exit `0`.

- [ ] **Step 2: Run target project verification**

Run in `<projects-root>/<workflow-container-project>`:

```bash
python -m pytest -q
python -m compileall <workflow_container_package>
```

Expected: PASS.

- [ ] **Step 3: Run platform and runtime documentation checks**

Run in `<projects-root>/marketplace-automation`:

```bash
rg -n "workflow-container-authoring|WorkflowRun|DataSource|DataContainer" doc/design/workflow-runtime.md
git diff --check
```

Expected: command exits `0`.

Run in `<projects-root>/browser-vpn-runtime`:

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 4: Update README with verified command examples**

Add to `README.md`:

```markdown
## Typical Flow

```bash
python -m workflow_container_developer.cli list
python -m workflow_container_developer.cli audit <workflow-container-project>
```

The target name is the adjacent project directory name. The CLI discovers workflow-container projects by `workflow.yaml` and `versions.yaml`; it does not know concrete workflow names.
```

- [ ] **Step 5: Run final verification**

Run in `<projects-root>/workflow-container-developer`:

```bash
python -m pytest -q
python -m compileall workflow_container_developer
git diff --check
```

Expected: PASS.

- [ ] **Step 6: Commit README/spec updates**

Run:

```bash
git add README.md doc/superpowers/specs/2026-07-03-workflow-container-developer-design.md
git commit -m "Document workflow container developer usage"
```

## Task 6: Push And Synchronize

**Files:**
- No source changes.

- [ ] **Step 1: Push repositories**

Run:

```bash
git -C <projects-root>/workflow-container-developer push origin main
git -C <projects-root>/marketplace-automation push origin main
git -C <projects-root>/<workflow-container-project> push origin main
```

Expected: all pushes succeed.

- [ ] **Step 2: Synchronize worktrees**

For each project with worktrees, run:

```bash
git -C <projects-root>/marketplace-automation worktree list --porcelain
git -C <projects-root>/<workflow-container-project> worktree list --porcelain
```

Fast-forward clean worktree branches to their project `main`. Do not reset or overwrite dirty worktrees.

- [ ] **Step 3: Final status check**

Run:

```bash
git -C <projects-root>/workflow-container-developer status --short --branch
git -C <projects-root>/marketplace-automation status --short --branch
git -C <projects-root>/<workflow-container-project> status --short --branch
git -C <projects-root>/browser-vpn-runtime status --short --branch
```

Expected: no dirty tracked changes. `main` branches that were changed are aligned with `origin/main`.
