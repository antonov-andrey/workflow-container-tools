"""Tests for workflow-container plugin skill contracts."""

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "plugins" / "workflow-container-tools"
AUDIT_SKILL_PATH = PLUGIN_ROOT / "skills" / "workflow-container-audit" / "SKILL.md"


def test_audit_skill_requires_actionable_findings() -> None:
    """Require audit findings to be concrete enough to implement directly."""

    skill_text = AUDIT_SKILL_PATH.read_text(encoding="utf-8")

    assert "## Finding Clarity Contract" in skill_text
    assert "self-contained" in skill_text
    assert "exact artifact path" in skill_text
    assert "why that fragment weakens execution" in skill_text
    assert "one concrete rewrite direction" in skill_text
    assert "Vague findings are forbidden" in skill_text
