# Workflow Container Skill Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a semantic workflow-container audit skill and strengthen workflow-container authoring instructions so new containers are written with clear contracts, state handling, and recovery procedures.

**Architecture:** `workflow-container-developer` remains the authoring skill. `workflow-container-audit` becomes a separate semantic review skill in the same `workflow-container-tools` plugin. The shared authoring reference remains the single source for workflow-container prompt-writing principles, and the Python CLI remains only a local helper.

**Tech Stack:** Codex plugin skills, Markdown instruction artifacts, plugin validation script, pytest for existing Python helper coverage.

---

## File Structure

- Modify `plugins/workflow-container-tools/skills/workflow-container-developer/references/workflow-container-authoring.md`: add the shared prompt-authoring contract.
- Modify `plugins/workflow-container-tools/skills/workflow-container-developer/SKILL.md`: require the developer skill to apply that contract when writing workflow-container instructions and remove canonical CLI-audit wording.
- Create `plugins/workflow-container-tools/skills/workflow-container-audit/SKILL.md`: define semantic audit workflow as a separate skill.
- Modify `README.md`: describe the two skills and avoid presenting `python -m workflow_container_developer.cli audit` as the canonical instruction audit.

## Task 1: Shared Prompt Authoring Contract

**Files:**
- Modify: `plugins/workflow-container-tools/skills/workflow-container-developer/references/workflow-container-authoring.md`

- [ ] **Step 1: Insert `Prompt Authoring Contract` after `Code Quality Baseline`**

Add this section after the existing `Code Quality Baseline` section and before `Runtime Package Boundary`:

```markdown
## Prompt Authoring Contract

Workflow-container prompts and instruction artifacts must be written as executable contracts, not as broad advice. The author must first identify the artifact role, then choose the instruction form that makes that role unambiguous.

Use `Contracts` when the text defines boundaries, inputs, outputs, schemas, artifact layout, allowed tools, forbidden tools, naming rules, source access rules, or ownership.

Use `FSM` when the process has states, retry loops, verification loops, blocked states, cancellation, crash recovery, multi-attempt execution, or terminal state transitions.

Use `Workflow` or `Step Sequence` when the process is a linear procedure without meaningful state-machine transitions.

Use `Persistent State` when generated, extracted, normalized, validated, externally loaded, or otherwise significant structured data is needed beyond the current local action.

Use `Recovery` where known failure modes can occur and the next corrective action must be deterministic.

These names are instruction-structure tools, not mandatory universal section headings. A prompt must not contain every section by default. A prompt must use the structure that matches its actual behavior.

Significant structured data must be persisted at the nearest stable boundary when it is needed by a later step, verifier, retry, restart, follow-up, or external consumer. It must not be accumulated only in model memory and written at the end of a long stage.

Ephemeral local context may stay in the current execution when it is limited to the current local action, such as one current identifier, one loop item, or a short local counter. When such values become a list, registry, queue, recovery state, audit state, or cross-step handoff, they become persistent state and must be written explicitly.

The shared authoring contract must avoid domain-specific examples. Examples are allowed only when they are clearly illustrative or belong to a domain-owned prompt in the concrete workflow-container project. A shared workflow-container contract must not turn a domain-specific case into a generic rule.
```

- [ ] **Step 2: Re-read the full reference**

Run:

```bash
sed -n '1,260p' plugins/workflow-container-tools/skills/workflow-container-developer/references/workflow-container-authoring.md
```

Expected: the new section is present once, contains no domain-specific examples, and does not require every prompt to use the same headings.

## Task 2: Developer Skill Contract

**Files:**
- Modify: `plugins/workflow-container-tools/skills/workflow-container-developer/SKILL.md`

- [ ] **Step 1: Replace the `Workflow` section**

Replace the current `## Workflow` section with:

```markdown
## Workflow

1. Identify the target repository from the current working directory and its files such as `workflow.yaml`, `versions.yaml`, `pyproject.toml`, `AGENTS.md`, and `doc/design/*.md`.
2. Before changing workflow contracts, prompt contracts, artifact layout, runtime boundaries, code quality rules, prompt templates, stage instructions, validator instructions, or recovery instructions, read `references/workflow-container-authoring.md`.
3. Keep ownership boundaries intact:
   - concrete workflow domain logic stays in the target workflow-container project,
   - generic runtime code and generic prompt partials stay in `workflow-container-runtime`,
   - browser/VPN process launch and profile handling stay in `browser-vpn-runtime`,
   - developer-only guidance and audit tooling stay in this plugin/repository.
4. When writing or rewriting one workflow-container prompt or instruction artifact:
   - identify the artifact role before writing it,
   - choose the appropriate instruction form from `Prompt Authoring Contract`,
   - write exact inputs, outputs, state boundaries, and terminal behavior when the artifact defines a boundary,
   - write state transitions explicitly when the artifact contains retries, verification loops, blocked states, or recovery,
   - persist significant structured data at the nearest stable boundary instead of relying on model memory,
   - describe recovery next steps near the failure mode that triggers them,
   - avoid broad suggestions when an exact action or transition is required.
5. Do not require a fixed set of headings for every prompt. Require the instruction form that matches the prompt's role.

Do not add `workflow-container-developer` as a production runtime dependency of a concrete workflow-container project.
```

- [ ] **Step 2: Verify there is no canonical CLI audit wording**

Run:

```bash
rg -n "workflow_container_developer.cli audit|CLI.*audit|mechanical check|static checker" plugins/workflow-container-tools/skills/workflow-container-developer/SKILL.md
```

Expected: no matches.

## Task 3: Semantic Audit Skill

**Files:**
- Create: `plugins/workflow-container-tools/skills/workflow-container-audit/SKILL.md`

- [ ] **Step 1: Create `workflow-container-audit` skill**

Create `plugins/workflow-container-tools/skills/workflow-container-audit/SKILL.md` with this content:

```markdown
---
name: workflow-container-audit
description: Use when semantically auditing workflow-container instructions, prompt templates, workflow docs, stage contracts, verification prompts, recovery instructions, or workflow-container authoring changes for clarity, reliability, persistence boundaries, and recoverability.
---

# Workflow Container Audit

Use this skill to semantically audit workflow-container instruction artifacts. This skill is not a wrapper around any Python CLI command or static checker.

## Required Reading

Before auditing, read:

1. this `SKILL.md`;
2. `../workflow-container-developer/SKILL.md`;
3. `../workflow-container-developer/references/workflow-container-authoring.md`;
4. the target workflow-container project's instruction-bearing artifacts.

## Audit Scope

Instruction-bearing artifacts include:

- `AGENTS.md`;
- `doc/design/**`;
- prompt templates;
- stage prompts;
- verification prompts;
- validator instructions;
- recovery instructions;
- workflow documentation that defines behavior.

## Semantic Review Workflow

For each artifact, first determine the artifact role:

- boundary contract;
- workflow sequence;
- FSM, retry, or recovery procedure;
- generated or persisted data handling;
- external-source handling;
- verification or checking guidance.

Then evaluate whether the instruction form is strong enough for that role:

- boundary contracts must make inputs, outputs, ownership, and forbidden behavior clear;
- stateful processes must have explicit states and transitions;
- linear procedures must have an unambiguous step sequence;
- significant structured data flow must have clear persistence boundaries;
- recovery must be deterministic where known errors can occur;
- instructions must not depend on model memory for durable handoff data;
- another agent must be able to execute the instruction consistently without hidden chat context.

If a clearer, more reliable, or more recoverable alternative formulation exists, report the current text as a finding. Do not accept weaker text only because it is syntactically valid or because a static checker would pass.

## Finding Format

Each finding must state:

- the concrete problem;
- why the current text is weaker or ambiguous;
- the rewrite direction or exact replacement when practical;
- the artifact and fragment that must be rechecked after rewriting.

The audit must not require identical headings in all prompts. It must not reduce review to regex checks, mandatory heading checks, or static lint rules. Mechanical observations may be mentioned only as supporting evidence when the semantic issue is clear.
```

- [ ] **Step 2: Verify skill discovery shape**

Run:

```bash
find plugins/workflow-container-tools/skills -maxdepth 2 -name SKILL.md -print | sort
```

Expected output includes exactly these two skill files:

```text
plugins/workflow-container-tools/skills/workflow-container-audit/SKILL.md
plugins/workflow-container-tools/skills/workflow-container-developer/SKILL.md
```

## Task 4: README Boundary Cleanup

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the plugin summary**

Replace the paragraph that starts with `The marketplace name is` with:

```markdown
The marketplace name is `workflow-container-tools`. The installable plugin is `workflow-container-tools`. Current skills inside that plugin are `workflow-container-developer` and `workflow-container-audit`. Future workflow-container skills should be added under the same plugin at `plugins/workflow-container-tools/skills/`.
```

- [ ] **Step 2: Remove CLI audit from the local CLI example**

Replace the `Optional Local CLI` command block with:

```markdown
```bash
python -m workflow_container_developer.cli --help
python -m workflow_container_developer.cli list
```
```

- [ ] **Step 3: Add canonical audit note**

Add this paragraph after the `Optional Local CLI` command block:

```markdown
The Python CLI is only a local helper. Canonical workflow-container instruction review is the semantic `workflow-container-audit` skill, not the Python CLI.
```

- [ ] **Step 4: Verify README wording**

Run:

```bash
rg -n "workflow_container_developer.cli audit|canonical.*CLI|mechanical audit" README.md
```

Expected: no matches.

## Task 5: Verification And Commit

**Files:**
- Test: `plugins/workflow-container-tools/.codex-plugin/plugin.json`
- Test: `plugins/workflow-container-tools/skills/workflow-container-audit/SKILL.md`
- Test: `plugins/workflow-container-tools/skills/workflow-container-developer/SKILL.md`
- Test: `README.md`

- [ ] **Step 1: Validate plugin**

Run:

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py plugins/workflow-container-tools
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/workflow-container-tools
```

Expected: cachebuster updates and plugin validation passes.

- [ ] **Step 2: Run repository tests**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Run text guards**

Run:

```bash
rg -n "workflow_container_developer.cli audit|canonical.*CLI|mechanical audit|plugins/workflow-container-developer|workflow-container-developer@workflow-container-tools" README.md AGENTS.md plugins doc workflow_container_developer test || true
git diff --check
```

Expected: the `rg` command has no output for old plugin paths or canonical CLI audit wording, and `git diff --check` exits `0`.

- [ ] **Step 4: Commit implementation**

Run:

```bash
git add README.md plugins/workflow-container-tools doc/superpowers/plans/2026-07-04-workflow-container-skill-audit.md
git commit -m "Add semantic workflow container audit skill"
```

Expected: one implementation commit is created after the already committed design spec.
