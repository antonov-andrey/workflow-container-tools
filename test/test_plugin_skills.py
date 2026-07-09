"""Tests for workflow-container plugin skill contracts."""

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "plugins" / "workflow-container-tools"
AUDIT_SKILL_PATH = PLUGIN_ROOT / "skills" / "workflow-container-audit" / "SKILL.md"
AUTHORING_REFERENCE_PATH = (
    PLUGIN_ROOT / "skills" / "workflow-container-developer" / "references" / "workflow-container-authoring.md"
)
DEVELOPER_SKILL_PATH = PLUGIN_ROOT / "skills" / "workflow-container-developer" / "SKILL.md"
STAGE_FILE_CONTRACT_DESIGN_PATH = (
    PLUGIN_ROOT / "skills" / "workflow-container-developer" / "references" / "2026-07-09-stage-file-contract-design.md"
)


def _markdown_section_get(text: str, heading: str, next_heading: str | None = None) -> str:
    """Return the Markdown section between two level-2 headings.

    Args:
        text: Markdown text.
        heading: Opening level-2 heading.
        next_heading: Next level-2 heading when the section is not terminal.

    Returns:
        Section body.
    """

    section = text.split(heading, maxsplit=1)[1]
    if next_heading is None:
        return section
    return section.split(next_heading, maxsplit=1)[0]


def test_audit_skill_requires_actionable_findings() -> None:
    """Require audit findings to be concrete enough to implement directly."""

    skill_text = AUDIT_SKILL_PATH.read_text(encoding="utf-8")

    assert "## Finding Contract" in skill_text
    assert "self-contained" in skill_text
    assert "exact artifact path" in skill_text
    assert "why that fragment weakens execution" in skill_text
    assert "one concrete rewrite direction" in skill_text
    assert "Vague findings are forbidden" in skill_text


def test_audit_skill_matches_runtime_owned_stage_artifact_contract() -> None:
    """Require audit guidance to keep standard stage artifact writes runtime-owned."""

    skill_text = AUDIT_SKILL_PATH.read_text(encoding="utf-8")
    stage_boundary_section = _markdown_section_get(skill_text, "## Stage Boundary Review", "## Prompt Refactor Gate")

    assert "action stages must write `result.json`" not in skill_text
    assert "verification stages must write `verification.json`" not in skill_text
    assert (
        "`Codex Stage`, `Stage Lifecycle`, `Prompt Routing`, `DBOS Handoff`, `Durable Step Completion`, "
        "`JSON Payload Naming`, and `Artifact Materialization` from "
        "`../workflow-container-developer/references/workflow-container-authoring.md`" in skill_text
    )
    assert "`Stage Lifecycle` owns only lifecycle order" in skill_text
    assert "write `prompt_context.json`, `result.json`, or `verification.json`" in skill_text
    assert "duplicates Pydantic/schema checks, mechanical validator checks, or `Stage Lifecycle` ordering" in skill_text
    assert "routes runtime prompt paths differently from `Prompt Routing`" in skill_text
    assert "`stage_result_path` to an action prompt" in skill_text
    assert "`previous_stage_result_path` to a verification prompt" in skill_text
    assert stage_boundary_section.count("copied result channel") == 1
    assert "any copied result channel named by `Prompt Routing`" in stage_boundary_section
    assert "copied result JSON instead of runtime-owned path arguments" not in stage_boundary_section
    assert "`draft_result_json`" not in stage_boundary_section
    assert "`previous_result_json`" not in stage_boundary_section
    assert "copied action result JSON" not in stage_boundary_section
    assert "copied stage result JSON" not in stage_boundary_section
    assert "copied result payloads" not in stage_boundary_section
    assert "generic stage instructions, copied result JSON, or generic state-path fields" not in stage_boundary_section
    assert "omits any recovery-bundle member required by `Durable Step Completion`" in skill_text
    assert "materialized external artifact tree files" in skill_text
    assert "required by result/verification recovery" not in skill_text
    assert (
        "referenced by current stage data and required to rerun validation or verification after restart" in skill_text
    )


def test_authoring_reference_matches_runtime_owned_stage_artifact_contract() -> None:
    """Require authoring guidance to match runtime-owned stage artifacts and tree materialization."""

    reference_text = AUTHORING_REFERENCE_PATH.read_text(encoding="utf-8")

    assert "Action stage пишет `result.json`" not in reference_text
    assert "Stage code может записывать `result.json`" not in reference_text
    assert "references из validated stage result" not in reference_text
    assert "копирует только referenced" not in reference_text
    assert "`Codex` action возвращает schema-valid JSON" in reference_text
    assert "Runtime materializes configured external artifact roots" in reference_text
    assert "copying the matching stage tree into the current stage directory" in reference_text


def test_authoring_reference_requires_minimal_stable_contracts() -> None:
    """Require authoring guidance to prefer minimal stable data and simplification."""

    reference_text = AUTHORING_REFERENCE_PATH.read_text(encoding="utf-8")

    assert "## Minimal Stable Contract" in reference_text
    assert "one minimal stable model" in reference_text
    assert "Simplification is the default correction path" in reference_text
    assert "changed or directly affected boundary" in reference_text


def test_authoring_reference_names_workflow_container_contract_boundary() -> None:
    """Require shared workflow YAML contracts to have one runtime-neutral owner."""

    reference_text = AUTHORING_REFERENCE_PATH.read_text(encoding="utf-8")

    assert "## Workflow Source Contract Boundary" in reference_text
    assert reference_text.index("## Workflow Source Contract Boundary") < reference_text.index(
        "## Runtime Package Boundary"
    )
    contract_section = _markdown_section_get(
        reference_text,
        "## Workflow Source Contract Boundary",
        "## Runtime Package Boundary",
    )
    assert "`workflow-container-contract`" in reference_text
    assert "`WorkflowDefinition`" in contract_section
    assert "`WorkflowVersionsDefinition`" in contract_section
    assert "`workflow.yaml`" in contract_section
    assert "`versions.yaml`" in contract_section
    assert "runtime-neutral" in contract_section


def test_authoring_reference_has_single_stage_lifecycle_block() -> None:
    """Keep detailed Codex stage lifecycle in one owner section."""

    reference_text = AUTHORING_REFERENCE_PATH.read_text(encoding="utf-8")

    assert "## Stage Lifecycle" in reference_text
    lifecycle_section = _markdown_section_get(reference_text, "## Stage Lifecycle", "## Prompt Routing")
    assert "1. Runtime writes typed `prompt_context.json`" in lifecycle_section
    assert "passes only `prompt_context_path`" not in lifecycle_section
    assert (
        "4. Only runtime writes `result.json` after successful schema/model validation and successful "
        "materialization of configured external artifact roots for the current attempt." in lifecycle_section
    )
    assert "after successful schema/model validation." not in lifecycle_section
    assert (
        "Semantic verification checks current result correctness against prompt context, declared artifacts, and "
        "stage-relevant source/evidence when present" in lifecycle_section
    )
    assert "correctness относительно prompt context, evidence и source data" not in lifecycle_section
    assert "8. Runtime writes `verification.json`" in lifecycle_section
    assert "Verification prompt получает `stage_result_path`" not in lifecycle_section
    assert "Межшаговый `DBOS` handoff" not in lifecycle_section
    assert "Owner-controlled names for JSON payload values" not in lifecycle_section
    assert "`DBOS` step считается завершенным" not in lifecycle_section
    assert (
        "Runtime materializes configured artifacts, writes `result.json`, runs mechanical validation and semantic verification"
        not in reference_text
    )


def test_authoring_reference_splits_stage_support_contracts() -> None:
    """Keep routing, handoff and JSON naming outside lifecycle order."""

    reference_text = AUTHORING_REFERENCE_PATH.read_text(encoding="utf-8")

    assert "## Prompt Routing" in reference_text
    assert "## DBOS Handoff" in reference_text
    assert "## Durable Step Completion" in reference_text
    assert "## JSON Payload Naming" in reference_text
    assert reference_text.index("## Stage Lifecycle") < reference_text.index("## Prompt Routing")
    assert reference_text.index("## Prompt Routing") < reference_text.index("## DBOS Handoff")
    assert reference_text.index("## DBOS Handoff") < reference_text.index("## Durable Step Completion")
    assert reference_text.index("## Durable Step Completion") < reference_text.index("## JSON Payload Naming")
    assert reference_text.index("## JSON Payload Naming") < reference_text.index("## Artifact Materialization")

    prompt_routing_section = _markdown_section_get(reference_text, "## Prompt Routing", "## DBOS Handoff")
    dbos_handoff_section = _markdown_section_get(reference_text, "## DBOS Handoff", "## Durable Step Completion")
    durable_completion_section = _markdown_section_get(
        reference_text,
        "## Durable Step Completion",
        "## JSON Payload Naming",
    )
    json_payload_naming_section = _markdown_section_get(
        reference_text,
        "## JSON Payload Naming",
        "## Artifact Materialization",
    )

    assert "`stage_result_path`" in prompt_routing_section
    assert "`previous_stage_result_path`" in prompt_routing_section
    assert "first action attempt receives only `prompt_context_path`" in prompt_routing_section
    assert (
        "retry action attempt receives `prompt_context_path` and `previous_stage_result_path`" in prompt_routing_section
    )
    assert "verification attempt receives `prompt_context_path` and `stage_result_path`" in prompt_routing_section
    assert "passes only `prompt_context_path` to action and verification prompts" not in prompt_routing_section
    assert (
        "Runtime must not pass `draft_result_json`, `previous_result_json`, copied action result JSON, "
        "or copied stage result JSON into either prompt" in prompt_routing_section
    )
    assert "Межшаговый `DBOS` handoff" in dbos_handoff_section
    assert "построенным из `result.json`, declared artifacts и prompt context" in dbos_handoff_section
    assert "prompt context и private stage state" not in dbos_handoff_section
    assert "private `state.json` may be read only by the same stage owner" in dbos_handoff_section
    assert "must not include private state paths or private state contents" in dbos_handoff_section
    assert "must not require a downstream stage to read a previous `state.json`" in dbos_handoff_section
    assert "`DBOS` step считается завершенным" in durable_completion_section
    assert "`prompt_context.json`" in durable_completion_section
    assert "`result.json`" in durable_completion_section
    assert "`verification.json`" in durable_completion_section
    assert "declared stage-generated artifacts" in durable_completion_section
    assert (
        "optional private `state.json` in the current stage directory when this stage uses one"
        in durable_completion_section
    )
    assert "optional private `state.json` when used" not in durable_completion_section
    assert "materialized external artifact tree files" in durable_completion_section
    assert "required by result/verification recovery" not in durable_completion_section
    assert (
        "referenced by current stage data and required to rerun validation or verification after restart"
        in durable_completion_section
    )
    assert "Owner-controlled names for JSON payload values must use `_json`" in json_payload_naming_section


def test_authoring_reference_keeps_checklist_from_becoming_second_owner() -> None:
    """Keep verification guidance from duplicating owner-section contracts."""

    reference_text = AUTHORING_REFERENCE_PATH.read_text(encoding="utf-8")
    checks_section = _markdown_section_get(reference_text, "## Проверки")

    assert "contract tests must cover the applicable owner sections from this document" in checks_section
    assert (
        "For each changed workflow-container artifact, tests or semantic reread must cover every owner section "
        "that artifact implements, references, or changes" in checks_section
    )
    assert "stage naming" not in checks_section
    assert "наличие полных Jinja2 templates" not in checks_section
    assert "schema validation на runner boundary" not in checks_section
    assert "browser access только через внешний `MCP` URL" not in checks_section


def test_authoring_reference_keeps_artifact_materialization_timing_in_lifecycle() -> None:
    """Keep artifact materialization mechanics separate from lifecycle order."""

    reference_text = AUTHORING_REFERENCE_PATH.read_text(encoding="utf-8")
    artifact_section = _markdown_section_get(reference_text, "## Artifact Materialization", "## Codex Sandbox Boundary")

    assert "Materialization timing is owned by `Stage Lifecycle`" in artifact_section
    assert "after action and before mechanical validation" not in artifact_section
    assert "`DBOS` step считается завершенным" not in artifact_section
    assert "copying the matching stage tree into the current stage directory" in artifact_section


def test_stage_file_contract_design_requires_concrete_refactor_structure() -> None:
    """Keep the stage-file design tied to concrete refactor target classes."""

    design_text = STAGE_FILE_CONTRACT_DESIGN_PATH.read_text(encoding="utf-8")
    refactor_section = _markdown_section_get(design_text, "## Refactor Target Structure", "## DBOS Handoff")
    verification_section = _markdown_section_get(design_text, "## Verification Criteria")

    assert "A refactor that only renames files" in refactor_section
    assert "`workflow_container_runtime/stage/file.py`" in refactor_section
    assert "`workflow_container_runtime/stage/step.py`" in refactor_section
    assert "`WorkflowStepBase[InputT, ResultT]`" in refactor_section
    assert "`WorkflowStepCodexBase[InputT, ActionOutputT, ResultT]`" in refactor_section
    assert "Its current `VerifiedCodexStageRunner` lifecycle must move into `WorkflowStepCodexBase`" in refactor_section
    assert "`brand_size_chart/model/stage_input.py`" in refactor_section
    assert "replaces `brand_size_chart/model/stage_context.py`" in refactor_section
    assert "Models must use `*Input` names, not `*PromptContext` names" in refactor_section
    assert (
        "SourceDiscoveryStep(WorkflowStepCodexBase[SourceDiscoveryInput, BrowserActionResult, SourceDiscoveryResult])"
        in refactor_section
    )
    assert (
        "TableExtractionStep(WorkflowStepCodexBase[TableExtractionInput, TableExtractionDeltaBatchResult, TableExtractionResult])"
        in refactor_section
    )
    assert (
        "CoverageDecisionStep(WorkflowStepCodexBase[CoverageDecisionInput, CoverageDecisionResult, CoverageDecisionResult])"
        in refactor_section
    )
    assert (
        "CanonicalSelectionStep(WorkflowStepCodexBase[CanonicalSelectionInput, CanonicalSelectionResult, CanonicalSelectionResult])"
        in refactor_section
    )
    assert "They must not build next-stage inputs by reading previous private state" in refactor_section
    assert "Public helpers whose only job is forwarding unchanged arguments" in refactor_section
    assert "concrete `brand-size-chart` stage classes match the target names" in verification_section
    assert (
        "`VerifiedCodexStageRunner` and unchanged-argument lifecycle forwarding wrappers are absent"
        in verification_section
    )


def test_authoring_reference_splits_codex_stage_prompt_owners() -> None:
    """Keep Codex stage prompt ownership rules in separate blocks."""

    reference_text = AUTHORING_REFERENCE_PATH.read_text(encoding="utf-8")
    codex_stage_section = _markdown_section_get(reference_text, "## `Codex` Stage", "## Stage Lifecycle")
    prompt_routing_section = _markdown_section_get(reference_text, "## Prompt Routing", "## DBOS Handoff")

    assert "Action output and artifacts:" in codex_stage_section
    assert "Verification output:" in codex_stage_section
    assert "Input worklist and progress state:" in codex_stage_section
    assert "Private state boundary:" in codex_stage_section
    assert "Template naming:" in codex_stage_section
    assert "Typed prompt context:" in codex_stage_section
    assert "Retry prompt inputs:" in codex_stage_section
    assert "Python prompt text placement:" in codex_stage_section
    assert "Runtime пишет этот объект в `prompt_context.json`" not in codex_stage_section
    assert "передает action и verification prompt-ам только `prompt_context_path`" not in codex_stage_section
    assert "runtime передает verification prompt-у `stage_result_path`" not in codex_stage_section
    assert "action prompt получает только retry-only `previous_stage_result_path`" not in codex_stage_section
    assert "copied result payload" not in codex_stage_section
    assert "copied action result JSON" not in codex_stage_section
    assert "copied stage result JSON" not in codex_stage_section
    assert "`draft_result_json`" not in codex_stage_section
    assert "`previous_result_json`" not in codex_stage_section
    assert reference_text.count("copied action result JSON") == 1
    assert reference_text.count("copied stage result JSON") == 1
    assert reference_text.count("`draft_result_json`") == 1
    assert reference_text.count("`previous_result_json`") == 1
    assert "copied action result JSON" in prompt_routing_section
    assert "copied stage result JSON" in prompt_routing_section
    assert "`draft_result_json`" in prompt_routing_section
    assert "`previous_result_json`" in prompt_routing_section
    assert (
        "retry data may be read only from typed prompt context, declared stage artifacts, optional private "
        "`state.json` in the current stage directory when this stage uses one, and runtime-provided retry paths "
        "owned by `Prompt Routing`" in codex_stage_section
    )
    assert "private state when used" not in codex_stage_section
    assert (
        "Runtime config не должен принимать отдельные поля с именами template. Runtime config должен принимать"
        not in codex_stage_section
    )


def test_audit_skill_reviews_minimality_before_domain_findings() -> None:
    """Require semantic audits to catch redundant data contracts before domain wording."""

    skill_text = AUDIT_SKILL_PATH.read_text(encoding="utf-8")

    assert "## Minimality Review" in skill_text
    assert "two objects for one semantic concept" in skill_text
    assert "mirrored fields" in skill_text
    assert "duplicated status" in skill_text


def test_audit_skill_sets_single_review_gate_order() -> None:
    """Require one explicit semantic audit order instead of competing gates."""

    skill_text = AUDIT_SKILL_PATH.read_text(encoding="utf-8")

    assert (
        "role detection -> minimality review -> stage boundary review -> prompt refactor gate -> domain findings"
        in skill_text
    )
    assert "1. role detection" in skill_text
    assert "2. minimality review" in skill_text
    assert "3. stage boundary review" in skill_text
    assert "4. prompt refactor gate" in skill_text
    assert "5. domain findings" in skill_text
    assert "Then evaluate whether the instruction form is strong enough for that role:" not in skill_text


def test_audit_skill_uses_one_finding_contract() -> None:
    """Avoid duplicate finding format contracts in audit guidance."""

    skill_text = AUDIT_SKILL_PATH.read_text(encoding="utf-8")

    assert "## Finding Contract" in skill_text
    assert "## Finding Format" not in skill_text
    assert "## Finding Clarity Contract" not in skill_text
    assert "the exact artifact path" in skill_text
    assert "the concrete artifact role being audited" in skill_text
    assert "the exact recheck target and the expected property after rewriting" in skill_text


def test_developer_skill_applies_minimal_stable_contracts_after_changes() -> None:
    """Require developer guidance to review changed boundaries for simplification."""

    skill_text = DEVELOPER_SKILL_PATH.read_text(encoding="utf-8")

    assert "Minimal Stable Contract" in skill_text
    assert "changed or directly affected boundary" in skill_text
    assert "proxy layers" in skill_text


def test_developer_skill_scope_matches_current_project_role() -> None:
    """Keep developer skill scope limited to current project ownership."""

    skill_text = DEVELOPER_SKILL_PATH.read_text(encoding="utf-8")

    assert "generic developer tooling" not in skill_text
    assert "`workflow-container-contract`" in skill_text
    assert "runtime-neutral workflow source models and loaders stay in `workflow-container-contract`" in skill_text
    assert "developer-only guidance, semantic audit tooling, and optional local discovery CLI" in skill_text


def test_developer_skill_references_authoring_reference_once() -> None:
    """Keep authoring reference loading in one workflow step."""

    skill_text = DEVELOPER_SKILL_PATH.read_text(encoding="utf-8")

    assert skill_text.count("references/workflow-container-authoring.md") == 1
