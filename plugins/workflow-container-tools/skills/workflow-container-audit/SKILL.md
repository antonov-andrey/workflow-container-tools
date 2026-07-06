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

## Stage Boundary Review

For Codex-backed workflow-container stages, audit the simple action and verification contract before domain details:

- action stages must write `result.json`;
- verification stages must write `verification.json` in the same stage directory;
- batch, retry, or resumable progress must use `state.json`;
- stage-specific public state filenames are invalid;
- verification results must not own artifact namespaces or artifact lists as the source of truth;
- mechanical validators must check paths, duplicates, required files, schema-adjacent invariants, and internal consistency;
- semantic verification must check source or evidence correctness;
- later stages must consume verified `result.json` and declared artifacts instead of reinterpreting previous stage semantics through a separate cross-stage validator layer;
- owner-controlled JSON payload names must use `_json`.

Report a finding when one instruction artifact defines a second public state file, asks a verifier to own artifact selection, duplicates Pydantic/schema checks as prompt text, omits durable `state.json` for retryable batch work, or introduces a custom stage runtime that should belong to `workflow-container-runtime`.

## Prompt Refactor Gate

Before reporting domain-level findings for one prompt template, evaluate whether the prompt itself needs structural refactoring.

Report prompt refactoring as the first finding when a prompt has multiple responsibilities such as boundary contract, workflow sequence, retry, recovery, persistent state, external-source access, and verification handoff, but presents them as one flat instruction block without clear role-specific structure or an explicit execution sequence.

The refactor finding must state the target structure that fits the prompt role, for example contract boundaries, step sequence, persistent state, retry or recovery state machine, and terminal handoff rules. Do not require identical headings in every prompt; require a structure that makes the real workflow executable and reviewable.

Do not bury a prompt-structure problem under narrower domain findings. If the prompt form makes reliable execution, recovery, or later audit unclear, the audit must recommend prompt refactoring before recommending domain-specific wording fixes.

If a clearer, more reliable, or more recoverable alternative formulation exists, report the current text as a finding. Do not accept weaker text only because it is syntactically valid or because a static checker would pass.

## Finding Format

Each finding must be self-contained. The reader must be able to implement the fix without asking what artifact, fragment, failure mode, or rewrite target the finding meant.

Each finding must state:

- the concrete problem;
- why the current text is weaker or ambiguous;
- the rewrite direction or exact replacement when practical;
- the artifact and fragment that must be rechecked after rewriting.

## Finding Clarity Contract

Each finding must include:

- the exact artifact path;
- the concrete artifact role being audited;
- the current fragment or instruction pattern that causes the problem;
- why that fragment weakens execution, recovery, persistence, verification, or future audit;
- one concrete rewrite direction with the target structure, target fields, target state transition, or target step sequence;
- the exact recheck target and the expected property after rewriting.

Vague findings are forbidden. Do not write findings whose fix is only "clarify", "make explicit", "improve", "tighten", "refactor", "document better", or "consider changing" unless the same finding also states the exact artifact change and recheck target.

The audit must not require identical headings in all prompts. It must not reduce review to regex checks, mandatory heading checks, or static lint rules. Mechanical observations may be mentioned only as supporting evidence when the semantic issue is clear.
