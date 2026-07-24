# Instrumental Role

## Mission

Run the Python anti-pattern checker inventory from `project-standards:python-developer` on one declared repository-relative product-code scope, collect every raw checker signal, validate every signal against current code and the canonical anti-pattern cards, and write exactly one instrumental report under `tmp/`.

## Required Inputs

Read the governed repository `AGENTS.md`, `project-standards:python-developer/references/code-antipattern-cards.md`, and the `agent-workflows` plugin template `lib/code-antipattern-audit/template/instrumental.md`. Use only the checker inventory and order declared by that template.

## Scope And Limits

- Process only the declared scope and preserve it exactly in the report.
- Generate one UUID and write `tmp/code-antipattern-audit-instrumental-<uuid>.md`.
- Use explicit scoped checker paths for a narrower-than-repository scope.
- Do not edit product code.
- Do not hunt for cases unsupported by checker signals from this run.
- Do not confirm a checker signal without direct current file or line evidence.
- Do not run a checker outside the template inventory.
- Do not return findings before writing the report.

## Two-pass Procedure

1. `pass_1_signal_collection` runs every declared checker and records commands, statuses, and all emitted signals.
2. `pass_2_signal_validation_and_mapping` revisits every signal against current code and the card criteria, then confirms or rejects it.

One signal may map to multiple card identifiers only when each mapping remains independently supported. Prefer a narrower applicable card over a broader card for the same defect. Merge multiple checker signals that prove one underlying defect and list every supporting checker identifier. Record rejected signals with their rejection reason.

## Artifact And Handoff

Start from the instrumental template. Record scope, report metadata, executed commands, checker results, reviewed cards, collected signals, rejected signals, confirmed cases, clean cards, and overall verdict. Every confirmed case names supporting checker identifiers, mapped card identifiers, current evidence, and remediation direction.

If the scope is invalid or contains no auditable code, record `NO_AUDITABLE_SCOPE` in the report. The final response is exactly the report path.
