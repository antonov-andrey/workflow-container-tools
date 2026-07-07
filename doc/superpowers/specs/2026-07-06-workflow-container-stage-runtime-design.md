# Workflow Container Stage Runtime Design

## Purpose

Workflow-container projects need one simple, reusable contract for action stages, verification stages, retry feedback, persistent state, and stage artifacts.

The shared semantic authoring rules belong to the `workflow-container-tools` plugin reference `references/workflow-container-authoring.md`. The reusable executable mechanics belong to `workflow-container-runtime`. Concrete workflow-container projects keep only domain workflows, domain result models, domain validators, and domain prompt templates.

## Approved Contract

Each Codex-backed stage uses one action stage and one verification stage.

The Codex action returns schema-valid JSON and writes only explicitly declared stage-owned generated artifacts or optional `state.json`. Runtime writes `result.json`; the verification stage writes only a `StageVerificationResult`, and runtime writes `verification.json` in the same stage directory. Verification does not own a separate artifact namespace.

Batch, retry, or resumable progress must be durable through declared stage artifacts or through one optional `state.json` in the same stage directory when separate state is needed. Stage-specific public state filenames are forbidden. Existing domain meanings such as source inventories, batch execution plans, queues, or resumable item lists must become typed contents of declared stage artifacts or `state.json`.

External artifact trees belong to another run-owned system that mirrors stage-relative paths under configured artifact roots. The action stage must not copy those trees itself.

Artifact materialization is runtime-owned and source-neutral. Runtime copies the matching stage tree from each configured artifact root into the current stage directory after action output validation and before mechanical validation. The default materialization policy may include `.playwright-mcp/current` as one artifact root for browser evidence, and a workflow container disables materialization by passing an empty artifact root list.

The verification result is intentionally small. It reports only verification status and feedback. It does not become the source of truth for stage artifact ownership, and it does not define a second failure channel.

Mechanical validators check schema-adjacent invariants, paths, duplicates, required files, and internal consistency. They return normally on success and raise `RuntimeError` with actionable feedback on failure. Semantic verification checks whether the result is correct relative to prompt context, evidence, and source data.

The verification prompt receives `stage_result_path` and must read current `result.json` from disk. The action prompt receives `previous_stage_result_path` only on retry attempts and must read previous `result.json` from disk when previous action result data is needed. Runtime must not copy draft result JSON, previous result JSON, action-stage result JSON, or state JSON into prompt context.

If verification fails, feedback returns to the same action stage. Separate fix stages are forbidden.

`result.json` belongs to the Codex action lifecycle. Cross-stage DBOS handoff belongs to the successful step return after the verified lifecycle and may be a Python-built payload derived from `result.json`, declared artifacts, prompt context, and private stage state. The next stage reads the declared handoff payload and declared artifacts. It must not revalidate previous-stage semantic correctness.

Owner-controlled names that carry JSON text or JSON payloads must use the suffix `_json`.

## Runtime Extraction

`workflow-container-runtime` must own the generic verified stage lifecycle:

- render action and verification prompts;
- run Codex for action;
- validate Codex output with the supplied Pydantic model schema;
- materialize stage artifacts through explicit runtime policies when configured;
- write `result.json`;
- run the mechanical validator hook;
- run Codex verification;
- write `verification.json`;
- feed verification errors back into the action stage until the attempt limit is reached.

`workflow-container-runtime` must not know domain source types, chart schemas, size-group rules, coverage decisions, or canonical-selection semantics.

`brand-size-chart` must replace its local generic stage lifecycle with the runtime-owned implementation. It keeps stage wrappers that build domain prompt context and pass domain models and validators to the runtime.

## Plugin Instruction Updates

`workflow-container-developer` must teach this contract as the default authoring model for future workflow-container projects.

`workflow-container-audit` must review instruction artifacts against this contract and report redundant public state files, verifier-owned artifact namespaces, duplicated schema checks in prompts, missing durable declared artifacts or private state for retry loops, and cross-stage validator layers that reinterpret earlier results instead of trusting verified typed boundaries.

## Non-Goals

This change does not move domain validators to `workflow-container-runtime`.

This change does not move `brand-size-chart` prompt templates to `workflow-container-runtime`.

This change does not introduce a new workflow platform layer.

This change does not add a second schema source beside Pydantic models.

## Verification

Implementation must verify:

- plugin instructions are internally consistent and point to the shared contract;
- `workflow-container-runtime` owns the reusable stage lifecycle;
- `brand-size-chart` no longer owns a generic verified stage runner;
- `brand-size-chart` uses `state.json` for source discovery state and declared chart artifact targets for table extraction state;
- owner-controlled JSON payload variable names use `_json`;
- relevant tests pass in `workflow-container-developer`, `workflow-container-runtime`, and `brand-size-chart`.
