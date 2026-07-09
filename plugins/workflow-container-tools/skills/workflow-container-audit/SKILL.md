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

Use one audit order: role detection -> minimality review -> stage boundary review -> prompt refactor gate -> domain findings.

1. role detection: determine whether each artifact is a boundary contract, workflow sequence, FSM/retry/recovery procedure, generated or persisted data handler, external-source handler, verification guidance, or checking guidance.
2. minimality review: apply `Minimality Review` before reporting domain-level wording or behavior findings.
3. stage boundary review: apply `Stage Boundary Review` before domain details for Codex-backed workflow-container stages.
4. prompt refactor gate: apply `Prompt Refactor Gate` before narrower domain findings for prompt templates.
5. domain findings: report remaining role-specific semantic findings after the earlier gates. Use these role criteria:
   - boundary contracts must make inputs, outputs, ownership, and forbidden behavior clear;
   - stateful processes must have explicit states and transitions;
   - linear procedures must have an unambiguous step sequence;
   - significant structured data flow must have clear persistence boundaries;
   - recovery must be deterministic where known errors can occur;
   - instructions must not depend on model memory for durable handoff data;
   - another agent must be able to execute the instruction consistently without hidden chat context.

## Minimality Review

Before reporting domain-level wording or behavior findings, check the artifact against `Minimal Stable Contract` from `../workflow-container-developer/references/workflow-container-authoring.md`.

Report a minimality finding when the artifact introduces or preserves:

- two objects for one semantic concept;
- mirrored fields across result, typed stage input, private state, artifact handles, audit views, or DBOS handoff payloads;
- duplicated status, error, message, note, priority, identity, path, applicability, or evidence channels;
- prompt schema text that duplicates Pydantic models or mechanical validators;
- validator logic that reconstructs the next handoff object instead of only validating the current boundary;
- compatibility bridges, proxy layers, alias payloads, or translation layers that exist only to keep an older contract shape alive;
- private stage state that later stages consume as public handoff data;
- a new abstraction that does not remove duplication, stabilize one boundary, or simplify validation and recovery.

The recommended fix must prefer simplification first: remove the duplicate field or object, reuse the existing stable model, move the data to the single owner, derive the value from an existing stable handle, or make one boundary the only source of truth. If simplification is impossible, the finding must propose the smallest idiomatic change that satisfies `KISS`, `DRY`, single source of truth and explicit ownership.

Keep the finding scoped to the changed or directly affected boundary. Do not ask for unrelated broad refactoring unless the duplicated contract crosses that boundary and prevents a correct fix.

## Stage Boundary Review

For Codex-backed workflow-container stages, use `Codex Stage`, `Stage Lifecycle`, `Prompt Routing`, `DBOS Handoff`, `Durable Step Completion`, `JSON Payload Naming`, and `Artifact Materialization` from `../workflow-container-developer/references/workflow-container-authoring.md` as the stage-boundary source of truth. `Stage Lifecycle` owns the base-class lifecycle contract and its ordered file-writing flow. Audit whether the artifact violates those owner sections or adds a second owner for one of their boundaries.

Report a stage-boundary finding when one artifact:

- defines a second public state file or makes a later stage depend on a previous stage's private `state.json`;
- asks an action stage, verification stage, prompt template, or domain wrapper to write `input.json`, `result.json`, or `verification.json`;
- concrete stages write `input.json`, `result.json`, or `verification.json` manually instead of using `WorkflowStepBase` or `WorkflowStepCodexBase`;
- asks a verifier to own artifact selection, artifact namespaces, artifact lists, or a second failure channel;
- duplicates Pydantic/schema checks, mechanical validator checks, or `Stage Lifecycle` ordering as prompt text;
- prompts use `prompt_context_path`, copied result JSON, `draft_result_json`, or `previous_result_json` instead of `input_path`, `previous_stage_result_path`, and `stage_result_path`;
- routes runtime prompt paths differently from `Prompt Routing`, such as passing `stage_result_path` to an action prompt, `previous_stage_result_path` to a verification prompt, or any copied result channel named by `Prompt Routing` instead of runtime-owned path arguments;
- omits any recovery-bundle member required by `Durable Step Completion`, including materialized external artifact tree files referenced by current stage data and required to rerun validation or verification after restart;
- requires private `state.json` when declared stage artifacts already own durable progress;
- DBOS code reads a previous stage `state.json`;
- a concrete stage has a second data shape for the same semantic object instead of one minimal stable object;
- an implementation adds compatibility aliases for both prompt-context and input terminology;
- adds generic prompt channels outside typed stage input, such as template-name fields, generic shared instructions, generic stage instructions, or generic state-path fields;
- introduces a custom stage runtime that should belong to `workflow-container-runtime`;
- lets owner-controlled JSON payload names avoid the `_json` suffix.

## Prompt Refactor Gate

Before reporting domain-level findings for one prompt template, evaluate whether the prompt itself needs structural refactoring.

Report prompt refactoring as the first finding when a prompt has multiple responsibilities such as boundary contract, workflow sequence, retry, recovery, persistent state, external-source access, and verification handoff, but presents them as one flat instruction block without clear role-specific structure or an explicit execution sequence.

The refactor finding must state the target structure that fits the prompt role, for example contract boundaries, step sequence, persistent state, retry or recovery state machine, and terminal handoff rules. Do not require identical headings in every prompt; require a structure that makes the real workflow executable and reviewable.

Do not bury a prompt-structure problem under narrower domain findings. If the prompt form makes reliable execution, recovery, or later audit unclear, the audit must recommend prompt refactoring before recommending domain-specific wording fixes.

If a clearer, more reliable, or more recoverable alternative formulation exists, report the current text as a finding. Do not accept weaker text only because it is syntactically valid or because a static checker would pass.

## Finding Contract

Each finding must be self-contained. The reader must be able to implement the fix without asking what artifact, fragment, failure mode, or rewrite target the finding meant.

Each finding must include:

- the exact artifact path;
- the concrete artifact role being audited;
- the current fragment or instruction pattern that causes the problem;
- why that fragment weakens execution, recovery, persistence, verification, or future audit;
- one concrete rewrite direction with the target structure, target fields, target state transition, or target step sequence;
- the exact recheck target and the expected property after rewriting.

Vague findings are forbidden. Do not write findings whose fix is only "clarify", "make explicit", "improve", "tighten", "refactor", "document better", or "consider changing" unless the same finding also states the exact artifact change and recheck target.

The audit must not require identical headings in all prompts. It must not reduce review to regex checks, mandatory heading checks, or static lint rules. Mechanical observations may be mentioned only as supporting evidence when the semantic issue is clear.
