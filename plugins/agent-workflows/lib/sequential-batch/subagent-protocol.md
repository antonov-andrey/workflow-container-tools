# Sequential Batch Subagent Protocol

This file is the canonical subagent-side protocol for sequential batch workers. Skill-local files own domain-specific rules and result schemas.

## Batch Ownership
- Each subagent owns exactly one assigned `batch_id` at a time for one run.
- A subagent MUST NOT self-select, start, inspect, or prepare another batch.
- A subagent may start another batch only after receiving a new parent task for that concrete batch.
- If the parent task conflicts with this protocol, stop and report the conflict.

## Input And Output
- Read only the current assigned `batch/<batch_id>/task.md`, `batch/<batch_id>/input.json`, and the skill-local reference files named by that task.
- Write output only under paths explicitly assigned by the task for the current batch.
- Do not write to the database.
- Do not edit files outside the assigned batch output paths.

## Sequential Processing
1. Load the assigned `input.json`.
2. Process input items in exact listed order.
3. For the current item, inspect only the source files needed for that current item.
4. Decide and write exactly the current item's result file before starting the next item.
5. Confirm the just-written result file is valid JSON and matches the current item identity.
6. Start the next item only after the current result file exists and passes the local shape check.

## Forbidden Shortcuts
- Do not inspect later items before the current item result file exists.
- Do not collect several item decisions before writing result files.
- Do not postpone negative, incomplete, or blocking files.
- Do not write one batch summary or combined result as a substitute for per-item files.
- Do not rewrite earlier valid files unless parent validation feedback explicitly names that file.

## Resume Rule
- On resume, scan the input items in order and continue from the first missing or malformed result file.

## Completion
- Every input item has one result JSON in the assigned output path.
- Every result JSON satisfies the skill-local schema contract named by the task.
- After completion, report the completed `batch_id` to the parent and stop.
