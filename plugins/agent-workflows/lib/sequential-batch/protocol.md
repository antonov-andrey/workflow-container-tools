# Sequential Batch Parent Protocol

This file owns parent-side batch assignment for reusable subagents that process ordered batches. Parent-side transport and recovery are owned by the `agent-workflows` plugin support owner `lib/subagent-transport/protocol.md` in `agent_pool` mode.

## Run State
- Each run directory MUST contain `agent.json`.
- `agent.json` MUST be a flat JSON object whose keys are current active `agent_id` values.
- `agent.json` values are workflow-local metadata owned by this protocol; each current value MUST include the current `batch_id`.
- A parent MUST NOT keep more than one current batch assigned to one active subagent.
- A parent MUST NOT assign a new batch to a subagent until the previous batch has passed the skill-local validation, dry-run apply, and apply gates.

## Assignment
1. Spawn at most `agent_count` reusable subagents.
2. Before sending one batch task, write the current `agent_id` key and current `batch_id` metadata to `agent.json`.
3. Send only the prepared `batch/<batch_id>/task.md` to that subagent.
4. When one batch applies successfully, remove or replace that subagent binding before closing, idling, or assigning the next batch.

## Recovery
- Use the `agent-workflows` plugin support owner `lib/subagent-transport/protocol.md` in `agent_pool` mode.
- The current `batch_id` is workflow-local metadata owned by this protocol.
- If current batch output is missing, malformed, fails validation, or needs clarification while the selected transport protocol keeps the current agent, send corrective feedback to the same current agent for the same batch.
