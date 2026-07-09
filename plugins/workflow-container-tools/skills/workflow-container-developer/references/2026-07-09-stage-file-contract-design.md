# Stage File Contract Design

## Scope
This design defines the target workflow-container stage file contract for Codex-backed stages, DBOS step handoff, private durable stage state, and incremental record persistence.

The design applies to workflow-container ecosystem projects in this order:

- `workflow-container-developer` owns the authoring and audit contract.
- `workflow-container-runtime` owns generic runtime filenames, path helpers, prompt routing, lifecycle writes, and optional generic JSONL helpers.
- Concrete workflow-container projects own domain inputs, domain results, validators, prompt templates, declared artifacts, and domain-specific incremental records.
- `workflow-container-contract` remains limited to runtime-neutral workflow source metadata such as `workflow.yaml` and `versions.yaml`.
- `marketplace-automation` changes only if the platform begins reading stage bundles directly.
- `browser-vpn-runtime` does not own workflow state.

## Stage File Contract
Each stage directory has one standard file bundle:

- `input.json` is the public stage input. Runtime writes it before the action attempt. It contains the strict typed stage input: worklist, execution plan, artifact targets, input handles, stage parameters, and stage-owned instructions.
- `result.json` is the public stage output. Runtime writes it only after the action output passes schema/Pydantic validation and configured artifact materialization for the current attempt succeeds.
- `verification.json` is the public verification verdict. Runtime writes it after mechanical failure or semantic verification.
- `state.json` is private durable state for the current stage. It may be read by the action, retry action, verification prompt, mechanical validator, and same-stage wrapper only. Downstream stages must not read a previous stage `state.json`.

`input.json`, `result.json`, and `verification.json` are the public stage lifecycle contract. `state.json` is the stage-local retry and recovery memory.

## Prompt Routing
Prompt routing uses file paths, not copied JSON payloads:

- first action attempt receives `input_path`;
- retry action attempt receives `input_path` and `previous_stage_result_path`;
- verification attempt receives `input_path` and `stage_result_path`.

Runtime must not pass `prompt_context_path`, `draft_result_json`, `previous_result_json`, copied action result JSON, or copied stage result JSON into prompts.

## Incremental Records
Significant growing collections must be persisted as soon as records are produced instead of being accumulated only in model memory until the end of a long stage.

Private incremental records belong under stage-private state. The standard layout is:

- `state.json` for the private state manifest;
- `state/*.jsonl` for private append-oriented record files referenced from `state.json`.

Public incremental records are declared artifacts, not private state. If a downstream stage, UI, audit consumer, or final result needs a JSONL file, that file must be a declared artifact referenced from `result.json`.

Every JSONL line must be validatable as one strict Pydantic record. The stage validator reconstructs the needed tree view from `input.json`, `state.json`, referenced JSONL files, declared artifacts, and `result.json`, then checks duplicates, terminal states, artifact references, and domain invariants.

JSONL is not mandatory for every stage. If an independent object is already represented by its own declared artifact, that artifact can be the durable per-object state. A stage must not introduce a redundant JSONL ledger only to mirror an existing independent declared artifact.

## Object Model
Workflow-container data objects must be minimal, stable, and tree-shaped.

One semantic object has one owner model at its boundary. Other layers must pass that model, reference it through a handle, or derive a view from it. They must not create a second shape with mirrored fields for the same concept.

When a stage processes independent objects:

- each object needs a stable identity;
- each object needs independently recoverable state;
- terminal per-object facts must not exist only as one aggregate stage summary;
- public handoff data must be represented by the minimal stable result object or declared artifact handle.

## Class Contract
Workflow and step implementations must expose the stage lifecycle through transparent base classes instead of open-coded wrapper chains.

`WorkflowBase` owns workflow-level orchestration mechanics for one concrete workflow family. It may keep stateless dependencies such as artifact layouts, runners, registries, validators, writers, and factories. It must not store run-specific mutable state, hide business decisions, or become a generic orchestration bucket for unrelated workflows.

`WorkflowStepBase[InputT, ResultT]` owns the generic step boundary:

- build and persist `InputT` as `input.json`;
- guarantee that public `result.json` and the DBOS step return payload are the same `ResultT`;
- write `verification.json` through the runtime-owned lifecycle;
- keep `state.json` private to the current step;
- expose only typed hook methods that concrete steps implement for domain behavior.

`WorkflowStepCodexBase[InputT, ActionOutputT, ResultT]` owns Codex-backed step lifecycle:

1. prepare declared artifacts;
2. build `InputT`;
3. write `input.json`;
4. run Codex action and validate `ActionOutputT`;
5. deterministically build public `ResultT` from `InputT`, `ActionOutputT`, declared artifacts, and same-step private state when needed;
6. write `result.json` as `ResultT`;
7. run mechanical validation against `ResultT`;
8. run semantic verification against `input.json`, `result.json`, and declared artifacts;
9. write `verification.json`;
10. return `ResultT`.

Concrete Codex-backed steps must contain only domain hooks such as input construction, artifact preparation, action-output finalization, and result validation. They must not reimplement the lifecycle order, write standard stage files manually, or return a different public payload than the object written to `result.json`.

Additional base classes are allowed only when at least two concrete implementations share real lifecycle behavior that cannot stay clear in `WorkflowStepBase` or `WorkflowStepCodexBase`. A new base class must remove duplication or clarify ownership; it must not exist only as a naming layer.

## Refactor Target Structure
The migration must leave a concrete class structure. A refactor that only renames files, leaves lifecycle code open-coded in concrete steps, or keeps both old and new lifecycle APIs is incomplete.

`workflow-container-runtime` target structure:

- `workflow_container_runtime/stage/file.py` owns standard stage filenames and path helpers: `STAGE_INPUT_FILENAME`, `STAGE_RESULT_FILENAME`, `STAGE_VERIFICATION_FILENAME`, `STAGE_STATE_FILENAME`, `stage_input_path_get(...)`, `stage_result_path_get(...)`, `stage_verification_path_get(...)`, and `stage_state_path_get(...)`.
- `workflow_container_runtime/stage/step.py` owns `WorkflowStepBase[InputT, ResultT]` and `WorkflowStepCodexBase[InputT, ActionOutputT, ResultT]`.
- `workflow_container_runtime/stage/runner.py` must stop being the public verified lifecycle owner. Its current `VerifiedCodexStageRunner` lifecycle must move into `WorkflowStepCodexBase`, and the old public lifecycle API must be removed instead of kept as a bridge.
- `workflow_container_runtime/codex/runner.py` remains the low-level Codex subprocess boundary. It must not know domain stages, DBOS step handoff, or stage file semantics beyond parameters passed by `WorkflowStepCodexBase`.
- `workflow_container_runtime/artifact/*` remains the generic artifact writer/materializer owner. Artifact materialization is called by `WorkflowStepCodexBase`, not by concrete workflow-container stages.

Concrete workflow-container target structure for `brand-size-chart`:

- `brand_size_chart/model/stage_input.py` owns stage input models and replaces `brand_size_chart/model/stage_context.py`. Models must use `*Input` names, not `*PromptContext` names.
- `brand_size_chart/stage/base.py` may contain `BrandSizeChartCodexStepBase` only if it owns real shared domain behavior such as common prompt renderer setup, artifact layout access, prompt-scope instruction lookup, or shared schema writing. It must not contain proxy helpers around runtime base classes.
- `brand_size_chart/stage/workflow_run_prompt_apply.py` must expose `WorkflowRunPromptApplyStep(WorkflowStepCodexBase[WorkflowRunPromptApplyInput, PromptScope, PromptScope])` or a deterministic `WorkflowStepBase` implementation if Codex is not needed for empty prompt handling. It must not manually write standard stage files.
- `brand_size_chart/stage/source_discovery.py` must expose `SourceDiscoveryStep(WorkflowStepCodexBase[SourceDiscoveryInput, BrowserActionResult, SourceDiscoveryResult])`. `SourceDiscoveryResult` is the public result and DBOS handoff. It must contain the verified source discovery list and any non-fatal no-table warnings needed by the source-type workflow, so no later DBOS step reads `source_discover/state.json`.
- `brand_size_chart/stage/table_extraction.py` must expose `TableExtractionStep(WorkflowStepCodexBase[TableExtractionInput, TableExtractionDeltaBatchResult, TableExtractionResult])`. `TableExtractionResult` is the public result and DBOS handoff. Python finalization from extraction delta to `TableExtractionArtifact` belongs inside this step.
- `brand_size_chart/stage/coverage_decision.py` must expose `CoverageDecisionStep(WorkflowStepCodexBase[CoverageDecisionInput, CoverageDecisionResult, CoverageDecisionResult])` because Codex action output and public result are the same object.
- `brand_size_chart/stage/canonical_selection.py` must expose `CanonicalSelectionStep(WorkflowStepCodexBase[CanonicalSelectionInput, CanonicalSelectionResult, CanonicalSelectionResult])` for non-empty candidates and a deterministic `WorkflowStepBase` path for empty candidates. Both paths must write the same public `CanonicalSelectionResult` contract.
- `brand_size_chart/workflow/*.py` DBOS classes remain durable workflow/step boundaries. Their methods must only validate incoming DBOS payloads, instantiate concrete step classes, call `run()`, and return `ResultT.model_dump(mode="json")`. They must not build next-stage inputs by reading previous private state, manually write standard stage files, or duplicate stage lifecycle logic.

The implementation must delete or rewrite obsolete wrappers in the same change. Public helpers whose only job is forwarding unchanged arguments into runtime lifecycle, writing standard stage files manually, or rebuilding an object that the new step result already owns are forbidden.

## DBOS Handoff
DBOS step handoff belongs to the successful step return after the verified lifecycle. It can be Python-built from `input.json`, `result.json`, declared artifacts, and same-stage private `state.json`.

The handoff must not include private state paths or private state contents. Downstream stages consume declared handoff payloads and declared artifacts only.

If data from private state is needed downstream, the same-stage owner must turn it into a declared result field or declared artifact reference before returning the DBOS step result.

## Migration Plan
The implementation must be a coordinated steady-state migration with no compatibility bridge.

1. Update `workflow-container-developer` authoring and audit contracts.
2. Update `workflow-container-runtime`:
   - rename `prompt_context.json` to `input.json`;
   - rename `prompt_context_path` to `input_path`;
   - rename prompt-context helpers, constants, config fields, and tests to stage input terminology.
   - introduce `WorkflowStepBase` and `WorkflowStepCodexBase` as the owners of standard stage lifecycle and Codex-backed stage lifecycle.
   - split stage file helpers into `workflow_container_runtime/stage/file.py` and stage lifecycle bases into `workflow_container_runtime/stage/step.py`.
   - remove `VerifiedCodexStageRunner` as a public lifecycle API after concrete stages migrate.
3. Update concrete workflow-container projects:
   - rename `*PromptContext` models that are real stage inputs to `*Input`;
   - update prompts to read `input_path`;
   - migrate concrete Codex-backed stages to `WorkflowStepCodexBase`;
   - introduce explicit public result models for source discovery and table extraction so `result.json` and DBOS step return payloads match.
   - remove downstream reads of previous stage `state.json`;
   - move downstream-needed private state data into `result.json`, DBOS step return payloads, or declared artifacts.
4. Update design docs, prompt tests, and contract tests.
5. Run targeted tests for affected packages.
6. Run semantic workflow-container audit against the changed container and shared contracts.

## Verification Criteria
The migrated contract is correct when all of these are true:

- runtime writes `input.json`, `result.json`, and `verification.json`;
- prompts no longer use `prompt_context_path`;
- prompts use `input_path`;
- downstream stages never read a previous stage `state.json`;
- private state references stay inside the same stage boundary;
- public JSONL artifacts are referenced from `result.json`;
- private JSONL records are referenced from `state.json`;
- Codex-backed concrete steps inherit from `WorkflowStepCodexBase` and do not manually reimplement the standard lifecycle order;
- each DBOS step returns the same public `ResultT` object that is written to `result.json`;
- concrete `brand-size-chart` stage classes match the target names and generic result relationships listed in `Refactor Target Structure`;
- `VerifiedCodexStageRunner` and unchanged-argument lifecycle forwarding wrappers are absent from public production call sites;
- no compatibility aliases accept both prompt-context and input terminology;
- tests or semantic reread cover each changed owner section.
