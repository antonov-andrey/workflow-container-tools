# Explain Skill Protocol

This file owns the shared protocol for `explain-*` skills. Each concrete explain skill owns only its trigger, goal, domain-specific coverage rules, and output specialization.

## Shared Rules
- Explain skills are read-only.
- Current repository code is the source of truth.
- Apply `AGENTS.md` `Language Zones` to all user-facing output, including response headings, labels, and explanatory prose.
- Keep code identifiers, paths, flags, table names, API names, and other machine-facing tokens literal.
- If the requested scope is ambiguous, infer the narrowest likely script, module, class, or function from the user request and state that inspected scope.
- Report only behavior, interfaces, symbols, or side effects supported by current code evidence.
- Do not print placeholder sections, placeholder fields, or absent boundary categories.

## Shared Output Rules
- Start with the exact code scope inspected.
- Include assumptions or unknowns only when current code does not make the requested behavior clear.
