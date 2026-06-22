"""R12 — suíte consolidada Playbook 12 (entity contract + gates CI)."""

from __future__ import annotations

from app.domain.services.chat_presentation_coverage_service import (
    ChatPresentationCoverageService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)
from tests.fixtures.presentation_playbook12_regression_gate import (
    validate_playbook12_ci_gates,
)


def test_playbook12_ci_gates_are_green() -> None:
    report = validate_playbook12_ci_gates()

    assert report["ok"] is True, "\n".join(report.get("blockingIssues") or [])


def test_entity_contract_covers_routed_entities() -> None:
    cases = ChatPresentationCoverageService.build_entity_contract_cases()

    assert len(cases) >= 40
    assert all(case.get("entity") and case.get("path") for case in cases)


def test_tier_a_pipeline_fixtures_declared() -> None:
    cases = ChatPresentationVocabularyService.playbook12_tier_a_pipeline_cases()

    assert len(cases) >= 14

    for case in cases:
        assert case.get("fixture")
        assert case.get("expected_presentation_profile")
        assert case.get("expected_layout_mode")
