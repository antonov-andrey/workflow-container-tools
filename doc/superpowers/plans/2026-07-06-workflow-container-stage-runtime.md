# Workflow Container Stage Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Move the generic verified Codex stage lifecycle into `workflow-container-runtime` and align `workflow-container-tools` instructions plus `brand-size-chart` with the simple action/verification/state contract.

**Architecture:** `workflow-container-developer` owns the semantic authoring and audit contract. `workflow-container-runtime` owns the reusable executable verified-stage lifecycle. `brand-size-chart` keeps domain stage wrappers, domain models, domain validators, and domain prompts, and uses the runtime stage runner.

**Tech Stack:** Python 3.14, Pydantic v2, Jinja2 prompt rendering, Codex CLI runner, pytest, Black line length 120.

---

## File Structure

- Modify `plugins/workflow-container-tools/skills/workflow-container-developer/references/workflow-container-authoring.md`: add the simple stage boundary and runtime extraction contract.
- Modify `plugins/workflow-container-tools/skills/workflow-container-audit/SKILL.md`: add audit criteria for the simple stage boundary.
- Modify `workflow_container_runtime/codex/runner.py`: keep raw Codex execution only.
- Create or modify runtime stage modules under `workflow_container_runtime/stage/`: add `StageVerificationResult`, stage config, and verified stage runner.
- Modify `workflow_container_runtime/artifact/`: keep generic JSON writing and generic materialization.
- Modify `brand_size_chart/stage/semantic.py`: remove local generic lifecycle or turn it into a thin deleted import replacement.
- Modify `brand_size_chart/stage/*.py`: call runtime verified stage runner and pass domain prompt context, result model, and mechanical validator hooks.
- Remove the domain-owned verification result model.
- Modify `brand_size_chart/prompt/template/*.j2`: use `*_json` template variables and replace special public state filenames with declared stage artifacts or private `state.json`.
- Modify `brand_size_chart/validator/*.py`: validate `state.json` where source inventory is required and validate declared stage artifacts where they own durable progress.
- Modify tests in all touched projects to cover the new ownership and filenames.

## Task 1: Plugin Contract Update

- [x] Update `workflow-container-authoring.md` with the simple stage contract, `state.json`, minimal verification result, runtime ownership, and `_json` naming rule.
- [x] Update `workflow-container-audit/SKILL.md` so semantic audit reports violations of this contract with concrete rewrite targets.
- [x] Re-read both files and remove duplicate, contradictory, or weaker wording.
- [x] Run `python -m pytest -q` in `workflow-container-developer`.

## Task 2: Runtime Verified Stage Owner

- [x] Add runtime-owned strict Pydantic models for verification result and stage runtime config.
- [x] Add a runtime verified stage runner that receives prompt templates, prompt context, result model class, result directory, stage directory, optional browser settings, optional mechanical validator, and optional artifact materialization policy.
- [x] Ensure the runtime runner writes only `result.json` and `verification.json` as standard public stage files and treats `state.json` as stage-owned optional data.
- [x] Rename runtime and prompt lifecycle variables to `*_json`.
- [x] Add tests that exercise action success, mechanical validation feedback, verification retry, and `_json` naming.
- [x] Run `python -m pytest -q` and `python -m compileall workflow_container_runtime` in `workflow-container-runtime`.

## Task 3: Brand Size Chart Runtime Adoption

- [x] Replace local generic verified stage usage with `workflow-container-runtime` verified stage runner.
- [x] Keep `SourceDiscoveryStage`, `TableExtractionStage`, `CoverageDecisionStage`, `CanonicalSelectionStage`, and `WorkflowRunPromptApplyStage` as domain wrappers only.
- [x] Move source discovery inventory to `source_discover/state.json`.
- [x] Move table extraction durable progress to declared chart artifact targets.
- [x] Remove manual `verification_artifact_path_list` plumbing when the runtime can derive standard stage files.
- [x] Ensure all owner-controlled JSON payload variables and template context names use `*_json`.
- [x] Remove the domain-owned verification result and import the runtime-owned verification result.
- [x] Update tests for state filenames, verification result ownership, and prompt variable names.
- [x] Run `uv run pytest -q`, `uv run black --target-version py314 --line-length 120 --check brand_size_chart test`, and `python -m compileall brand_size_chart` in `brand-size-chart`.

## Task 4: Cross-Project Consistency Check

- [x] Search all active projects for legacy JSON payload suffixes, special public state filenames, and domain-owned verification results.
- [x] Confirm remaining matches are either removed or explicitly outside tracked source.
- [x] Run `git diff --check` in each touched project.
- [x] Report changed files, verification commands, and any remaining blockers.
