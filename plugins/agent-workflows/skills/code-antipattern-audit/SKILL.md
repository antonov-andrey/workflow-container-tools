---
name: code-antipattern-audit
description: Use when the user explicitly requests the code-antipattern-audit workflow or one merged anti-pattern audit report path under tmp/.
---

# Code Anti-pattern Audit

Run one two-perspective audit of an explicitly declared Python product-code scope. This skill owns orchestration, source-report validation, deterministic merge, and final handoff. Python rules, anti-pattern cards, and instrumental checkers are owned by `project-standards:python-developer`.

## Required Owners

Read completely before execution:

- the governed repository `AGENTS.md`;
- `project-standards:python-developer`, including `references/code-antipattern-cards.md`;
- `references/instrumental-role.md`;
- `references/semantic-role.md`;
- `agent-workflows` plugin support owner `lib/subagent-role-contract.md`;
- `agent-workflows` plugin support owner `lib/subagent-transport/protocol.md`;
- both templates under `lib/code-antipattern-audit/template/`.

Fail closed if either provider or required owner is unavailable. Do not fall back to a consumer-local copy or named-agent TOML.

## Workflow

1. Normalize one repository-relative auditable Python scope.
2. State transport mode `agent_pool`.
3. Create two default subagents concurrently:
   - the instrumental subagent receives the complete `references/instrumental-role.md` contract, declared scope, resolved provider paths, and report template;
   - the semantic subagent receives the complete `references/semantic-role.md` contract, declared scope, resolved provider paths, and report template.
4. Record both current agent identifiers in one run-local `agent.json` as required by the transport owner.
5. Wait for both source report paths and apply transport recovery without changing either fixed role.
6. Validate both source reports with `lib/code-antipattern-audit/tool/code_antipattern_audit_report_check.py --expected-scope <scope>`.
7. Send malformed or incomplete report feedback to the same current role subagent while it remains current; replacement is transport-owned recovery only.
8. Merge the two validated reports with `lib/code-antipattern-audit/tool/code_antipattern_audit_report_merge.py`.
9. Return exactly the merged report path under `tmp/`.

Every parent-to-subagent task must be idempotent or restart-resumable. The parent owns scope, role assignment, source-report validation, merge, and final path handoff. Subagents must not edit product code.

## Perspective Separation

The instrumental role runs only the checker inventory declared by the instrumental template, collects raw signals, and confirms them against current code and the canonical cards in a second pass.

The semantic role independently reviews every current card in document order, collects evidence directly from current code, and confirms or rejects each candidate in a second pass. It must not consume checker output or the instrumental report during discovery or confirmation.

## Completion

Completion requires two valid role-specific source reports, one deterministic merged report, closure of obsolete subagents, and a final response containing only the merged report path.
