# Workflow Container Skill Audit

## Purpose

`workflow-container-tools` must provide two complementary skills for workflow-container work:

- `workflow-container-developer` creates and changes workflow-container projects and must guide Codex to write instructions correctly from the start.
- `workflow-container-audit` reviews existing workflow-container instructions semantically and identifies rewrites that make those instructions more reliable, clearer, and easier to recover from failures.

Both skills use the shared authoring contract at `references/workflow-container-authoring.md`. The developer skill applies that contract during authoring. The audit skill uses that contract as review criteria.

## Ownership

The installable plugin remains `workflow-container-tools`.

The existing skill `workflow-container-developer` remains responsible for workflow-container creation, modification, refactoring, and design work.

The new skill `workflow-container-audit` owns semantic review of workflow-container instruction artifacts. It must not be a wrapper around any Python CLI command or static checker.

The Python CLI in `workflow-container-developer` may remain an optional local helper, but it is not the canonical instruction audit and must not be presented as the quality gate for workflow-container instructions.

## Authoring Contract Additions

`references/workflow-container-authoring.md` must define a prompt-authoring contract for workflow-container projects.

Workflow-container prompts and instruction artifacts must be written as executable contracts, not as broad advice. They must choose the instruction form that matches the real task:

- `Contracts` when the text defines boundaries, inputs, outputs, schemas, artifact layout, allowed tools, forbidden tools, naming rules, source access rules, or ownership.
- `FSM` when the process has states, retry loops, verification loops, blocked states, cancellation, crash recovery, multi-attempt execution, or terminal state transitions.
- `Workflow` or `Step Sequence` when the process is a linear procedure without meaningful state-machine transitions.
- `Persistent State` when generated, extracted, normalized, validated, externally loaded, or otherwise significant structured data is needed beyond the current local action.
- `Recovery` where known failure modes can occur and the next corrective action must be deterministic.

These names are instruction-structure tools, not mandatory universal section headings. One prompt must not contain every section by default. A prompt must use the structure that makes its actual behavior unambiguous.

Significant structured data must be persisted at the nearest stable boundary when it is needed by a later step, verifier, retry, restart, follow-up, or external consumer. It must not be accumulated only in model memory and written at the end of a long stage. Ephemeral local context may stay in the current execution when it is limited to the current local action, such as one current identifier, one loop item, or a short local counter. When such values become a list, registry, queue, recovery state, audit state, or cross-step handoff, they become persistent state and must be written explicitly.

The shared authoring contract must avoid domain-specific examples. Examples are allowed only when they are clearly illustrative or belong to a domain-owned prompt in the concrete workflow-container project. A shared workflow-container contract must not turn a domain-specific case into a generic rule.

## Developer Skill Behavior

`workflow-container-developer` must require Codex to read `references/workflow-container-authoring.md` before creating or changing workflow-container instructions, prompt templates, workflow docs, stage contracts, validator instructions, or recovery instructions.

When authoring a workflow-container prompt or instruction artifact, the developer skill must guide Codex to:

- identify the role of the artifact before writing it;
- choose the appropriate instruction form from the authoring contract;
- write exact inputs, outputs, state boundaries, and terminal behavior when the artifact defines a boundary;
- write state transitions explicitly when the artifact contains retries, verification loops, blocked states, or recovery;
- persist significant structured data at the nearest stable boundary instead of relying on model memory;
- describe recovery next steps near the failure mode that triggers them;
- avoid broad suggestions when an exact action or transition is required.

The developer skill must not require a fixed set of sections for every prompt. It must require the instruction form that matches the prompt's role.

## Audit Skill Behavior

`workflow-container-audit` is a semantic review skill.

The audit skill must read:

- its own `SKILL.md`;
- `workflow-container-developer` `SKILL.md`;
- `references/workflow-container-authoring.md`;
- the target workflow-container project's instruction-bearing artifacts.

Instruction-bearing artifacts include:

- `AGENTS.md`;
- `doc/design/**`;
- prompt templates;
- stage prompts;
- verification prompts;
- validator instructions;
- recovery instructions;
- workflow documentation that defines behavior.

For each artifact, the audit skill must determine the artifact's role before judging it. The audit must evaluate whether the current instruction form is strong enough for that role:

- boundary contracts must make inputs, outputs, ownership, and forbidden behavior clear;
- stateful processes must have explicit states and transitions;
- linear procedures must have an unambiguous step sequence;
- significant structured data flow must have clear persistence boundaries;
- recovery must be deterministic where known errors can occur;
- instructions must not depend on model memory for durable handoff data;
- another agent must be able to execute the instruction consistently without hidden chat context.

If a clearer, more reliable, or more recoverable alternative formulation exists, the audit skill must treat the current text as a finding. It must not accept weaker text only because it is syntactically valid or because a static checker would pass.

Findings must state:

- the concrete problem;
- why the current text is weaker or ambiguous;
- the rewrite direction or exact replacement when practical;
- the artifact and fragment that must be rechecked after rewriting.

The audit skill must not reduce review to regex checks, mandatory heading checks, or static lint rules. It may mention mechanical observations as supporting evidence only when the semantic issue is clear.

## Non-Goals

This change does not add scaffold scripts.

This change does not make any Python CLI command the canonical audit.

This change does not require all prompts to use identical headings.

This change does not introduce domain-specific prompt examples into the shared authoring contract.

## Verification

The implementation plan must verify:

- `workflow-container-developer` still points authors to the shared authoring reference.
- `workflow-container-audit` exists as a separate skill in the `workflow-container-tools` plugin.
- `workflow-container-audit` describes semantic review and does not delegate canonical review to the Python CLI.
- `references/workflow-container-authoring.md` contains the prompt-authoring contract.
- Plugin validation passes for `plugins/workflow-container-tools`.
- The repository no longer presents `python -m workflow_container_developer.cli audit` as the canonical workflow-container instruction audit.
