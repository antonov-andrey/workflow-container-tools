---
name: code-audit
description: Use when the user explicitly requests the code-audit workflow or one validated code-audit report path under tmp/.
---

# Code Audit

Produce one evidence-backed semantic audit of current code against its actual owners. This skill owns generic scope derivation, section orchestration, report assembly, and handoff. It does not own reusable engineering checklist semantics or product-specific rules.

## Owners

Read completely:

- the governed repository `AGENTS.md` chain;
- every applicable provider skill selected in `Required Standards`;
- applicable project `DESIGN.md`, `design/**`, and project-local retained skill contracts;
- `agent-workflows` plugin support owners `lib/section-audit/protocol.md`, `lib/subagent-role-contract.md`, and `lib/subagent-transport/protocol.md`.

Fail closed when a selected provider is unavailable. Do not use a stale consumer-local copy.

## Scope

Use the user's explicit repository-relative code scope when supplied. Otherwise derive `default-changed` from current Git changes and include directly affected owner contracts and call sites. Report an explicit no-auditable-scope result when no code is in scope.

Build ordered checklist sections from the actual applicable owners:

- each selected reusable engineering standard that governs the code scope;
- each applicable project-local code, architecture, security, persistence, runtime, or verification contract;
- direct regression and integration behavior affected by the scope.

Do not copy product-specific checklist sections from another project or invent checklist cards from textual similarity.

## Workflow

1. State transport mode `agent_pool` when multiple checklist sections run concurrently, otherwise `direct_agent`.
2. Create one task per checklist section with exact scope entries, reviewed owner sources, role mission, limits, evidence requirements, result path, and handoff rules.
3. Require current file or line evidence for every finding and direct verification evidence where behavior is in question.
4. Validate each result with `lib/section-audit/tool/audit_section_result_check.py`.
5. Send corrective feedback to the same current subagent while transport keeps it current.
6. Merge validated section results in canonical owner order with `lib/section-audit/tool/audit_report_merge.py`.
7. Validate the final `tmp/code-audit-<uuid>.md` with `lib/section-audit/tool/audit_report_check.py`.
8. Return exactly the validated report path.

The audit is read-only. A clean report requires every applicable section to be reviewed; passing mechanical checks never replaces semantic review.
