"""Tests for workflow-container plugin skill contracts."""

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "plugins" / "workflow-container-tools"
AUDIT_SKILL_PATH = PLUGIN_ROOT / "skills" / "workflow-container-audit" / "SKILL.md"
AUTHORING_REFERENCE_PATH = (
    PLUGIN_ROOT / "skills" / "workflow-container-developer" / "references" / "workflow-container-authoring.md"
)


def test_audit_skill_requires_actionable_findings() -> None:
    """Require audit findings to be concrete enough to implement directly."""

    skill_text = AUDIT_SKILL_PATH.read_text(encoding="utf-8")

    assert "## Finding Clarity Contract" in skill_text
    assert "self-contained" in skill_text
    assert "exact artifact path" in skill_text
    assert "why that fragment weakens execution" in skill_text
    assert "one concrete rewrite direction" in skill_text
    assert "Vague findings are forbidden" in skill_text


def test_audit_skill_matches_runtime_owned_stage_artifact_contract() -> None:
    """Require audit guidance to keep standard stage artifact writes runtime-owned."""

    skill_text = AUDIT_SKILL_PATH.read_text(encoding="utf-8")

    assert "action stages must write `result.json`" not in skill_text
    assert "verification stages must write `verification.json`" not in skill_text
    assert "action stages return schema-valid JSON" in skill_text
    assert "runtime writes `prompt_context.json`, `result.json`, and `verification.json`" in skill_text
    assert "verification stages return `StageVerificationResult`" in skill_text


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
