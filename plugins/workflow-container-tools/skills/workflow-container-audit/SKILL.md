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
