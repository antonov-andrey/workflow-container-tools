# Workflow Container Stage Runtime Design

## Purpose

Workflow-container projects need one simple, reusable contract for action stages, verification stages, retry feedback, persistent state, and stage artifacts.

The shared semantic authoring rules belong to the `workflow-container-tools` plugin reference `references/workflow-container-authoring.md`. The reusable executable mechanics belong to `workflow-container-runtime`. Concrete workflow-container projects keep only domain workflows, domain result models, domain validators, and domain prompt templates.

## Approved Contract

Each Codex-backed stage uses one action stage and one verification stage.

The action stage writes `result.json` and any stage-owned generated artifacts. The verification stage writes `verification.json` in the same stage directory and does not own a separate artifact namespace.

Batch, retry, or resumable progress uses one optional `state.json` in the same stage directory. Stage-specific public state filenames are forbidden. Existing domain meanings such as source inventories or batch execution plans must become typed contents of `state.json`.

The action stage may return external artifact references in its schema-valid `result.json`. It must not copy external artifacts itself. Generic artifact materialization belongs to runtime code.

Browser artifact copy is a runtime-owned default materialization policy. It stays isolated behind one policy object and can be disabled by stage config when one workflow container does not need browser artifact copy.

The verification result is intentionally small. It reports verification status and feedback. It does not become the source of truth for stage artifact ownership.

Mechanical validators check schema-adjacent invariants, paths, duplicates, required files, and internal consistency. Semantic verification checks whether the result is correct relative to prompt context, evidence, and source data.

If verification fails, feedback returns to the same action stage. Separate fix stages are forbidden.

The next stage reads verified `result.json` and declared artifacts. It must not implement a separate cross-stage reinterpretation layer for the previous stage.

Owner-controlled names that carry JSON text or JSON payloads must use the suffix `_json`.

## Runtime Extraction

`workflow-container-runtime` must own the generic verified stage lifecycle:

- render action and verification prompts;
- run Codex for action;
- validate Codex output with the supplied Pydantic model schema;
- write `result.json`;
- materialize stage artifacts through explicit runtime policies when configured;
- run Codex verification;
- run the optional mechanical validator hook;
- write `verification.json`;
- feed verification errors back into the action stage until the attempt limit is reached.

`workflow-container-runtime` must not know domain source types, chart schemas, size-group rules, coverage decisions, or canonical-selection semantics.

`brand-size-chart` must replace its local generic stage lifecycle with the runtime-owned implementation. It keeps stage wrappers that build domain prompt context and pass domain models and validators to the runtime.

## Plugin Instruction Updates

`workflow-container-developer` must teach this contract as the default authoring model for future workflow-container projects.

`workflow-container-audit` must review instruction artifacts against this contract and report redundant public state files, verifier-owned artifact namespaces, duplicated schema checks in prompts, missing durable state for retry loops, and cross-stage validator layers that reinterpret earlier results instead of trusting verified typed boundaries.

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
- `brand-size-chart` uses `state.json` for source discovery state and table extraction state;
- owner-controlled JSON payload variable names use `_json`;
- relevant tests pass in `workflow-container-developer`, `workflow-container-runtime`, and `brand-size-chart`.
