---
name: instruction-audit
description: Use when the user explicitly requests the instruction-audit workflow or one validated instruction-audit report path under tmp/.
---

# Instruction Audit

Produce one evidence-backed semantic audit of current instruction artifacts against their real owner and precedence model. This skill owns generic scope derivation, section orchestration, report assembly, and handoff. Instruction structure and wording rules belong to `project-standards:project-instruction-developer`; project-specific contracts stay project-local.

## Owners

Read completely:

- the governed repository `AGENTS.md` chain;
- `project-standards:project-instruction-developer`;
- every provider skill named by `Required Standards` whose selection or reference is in scope;
- applicable project `DESIGN.md` and nested instruction owners;
- `agent-workflows` plugin support owners `lib/section-audit/protocol.md`, `lib/subagent-role-contract.md`, and `lib/subagent-transport/protocol.md`.

Fail closed when a selected provider is unavailable. Do not use consumer-local copies of provider contracts.

## Scope

Use explicit repository-relative instruction paths when supplied. Otherwise derive `default-changed` from changed canonical instruction artifacts and include every owner whose precedence, reference, or dependency is affected.

Build ordered checklist sections from actual concerns in scope: owner placement, precedence, provider selection, external references, wording and ambiguity, duplication, path scope, retained project overlay, and affected design or task-artifact boundaries. Do not assert exact prose or file presence as a surrogate for semantic review.

## Workflow

1. State transport mode `agent_pool` when multiple checklist sections run concurrently, otherwise `direct_agent`.
2. Create one task per checklist section with exact scope, owner sources, role mission, limits, evidence requirements, result path, and handoff rules.
3. Require concrete current artifact evidence for every finding.
4. Validate each result with `lib/section-audit/tool/audit_section_result_check.py`.
5. Send corrective feedback to the same current subagent while transport keeps it current.
6. Merge validated section results in canonical owner order with `lib/section-audit/tool/audit_report_merge.py`.
7. Validate the final `tmp/instruction-audit-<uuid>.md` with `lib/section-audit/tool/audit_report_check.py`.
8. Return exactly the validated report path.

The audit is read-only. Mechanical validators may support structure checks but never replace semantic instruction review.
