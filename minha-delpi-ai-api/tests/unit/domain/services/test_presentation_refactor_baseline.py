"""Snapshot do inventário Playbook 12 — fase R0."""

from __future__ import annotations

import pytest

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_presentation_refactor_baseline_service import (
    ChatPresentationRefactorBaselineService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_stored_baseline_file_exists() -> None:
    path = ChatPresentationRefactorBaselineService.default_stored_baseline_path()

    assert path.is_file()
    assert path.name == "presentation-refactor-baseline-jun2026.json"


def test_playbook12_refactor_vocabulary_loaded_from_json() -> None:
    assert ChatPresentationVocabularyService.playbook12_audit_files()
    assert ChatPresentationVocabularyService.playbook12_tier_a_profile_keys()
    assert ChatPresentationVocabularyService.playbook12_table_assembly_path_fragments()
    assert ChatPresentationVocabularyService.playbook12_targets()
    assert ChatPresentationVocabularyService.playbook12_tier_a_pipeline_cases()


def test_refactor_baseline_matches_stored_snapshot() -> None:
    comparison = ChatPresentationRefactorBaselineService.compare_to_stored()

    assert comparison["ok"], comparison.get("drift")


def test_refactor_baseline_summary_has_expected_debt() -> None:
    report = ChatPresentationRefactorBaselineService.build_report()
    summary = report["summary"]

    assert summary["auditFileCount"] == 4
    assert summary["totalPathConditionals"] == 0
    assert summary["useCaseTableAssemblyPathConditionalCount"] == 0
    assert summary["sectionAvailabilityRouteHandlerCount"] == 0
    assert summary["sectionAvailabilityLineCount"] <= 200
    assert summary["visualBundleDedicatedEnrichCount"] == 0
    assert summary["tierAMissingVisualBuildersCount"] == 0
    assert summary["tierAMissingTableAssemblyCount"] == 0
    assert report["profileGaps"]["tierAMissingSectionRules"] == []


def test_section_rules_has_no_legacy_narrative_template_methods():
    from pathlib import Path

    service_path = (
        Path(__file__).resolve().parents[3]
        / "app/domain/services/chat_presentation_section_rules_service.py"
    )
    source = service_path.read_text(encoding="utf-8")

    assert source.count("def _narrative_order_") == 0


def test_tier_a_profiles_listed_in_vocabulary_cases() -> None:
    fixture_keys = {
        case["profile_key"]
        for case in ChatPresentationVocabularyService.playbook12_tier_a_pipeline_cases()
    }

    assert fixture_keys == set(ChatPresentationRefactorBaselineService.tier_a_profile_keys())


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def _build(case: dict) -> dict:
    envelope = load_api_delpi_fixture_with_meta(case["fixture"])
    return _use_case()._build_presentation_metadata(
        action={"path": case["path"]},
        sanitized_data=envelope,
        resolved_path=case["path"],
        request_parameters={"userMessage": case["user_message"]},
    )


@pytest.mark.parametrize(
    "case",
    ChatPresentationVocabularyService.playbook12_tier_a_pipeline_cases(),
    ids=[
        case["id"]
        for case in ChatPresentationVocabularyService.playbook12_tier_a_pipeline_cases()
    ],
)
def test_playbook_12_tier_a_pipeline_cases(case: dict) -> None:
    meta = _build(case)
    decision = meta.get("presentationDecision") or {}
    plan = meta.get("stackPresentationPlan") or {}

    assert decision.get("layoutMode") == case["expected_layout_mode"]
    assert plan.get("presentationProfile") == case["expected_presentation_profile"]

    for visual in case.get("expected_visuals") or ():
        if visual == "text":
            assert meta.get("textPresentation", {}).get("markdown")
        elif visual == "kpi":
            assert meta.get("kpiPresentation", {}).get("type") == "kpi"
        elif visual == "tree":
            tree = meta.get("treePresentation")
            assert isinstance(tree, dict) and tree.get("type") == "tree"
        elif visual == "chart":
            assert meta.get("chartPresentation", {}).get("type") == "chart"
        elif visual == "dashboard":
            assert meta.get("dashboardPresentation", {}).get("type") == "dashboard"

    min_tables = case.get("expected_min_table_presentations")
    if min_tables is not None:
        assert len(meta.get("tablePresentations") or []) >= min_tables

    expected_views = case.get("expected_available_views")
    if expected_views is not None:
        available = tuple(decision.get("availableViews") or [])
        for view in expected_views:
            assert view in available


def test_audit_script_entrypoint_importable() -> None:
    script = (
        ChatPresentationRefactorBaselineService.package_root()
        / "scripts"
        / "audit_presentation_path_ifs.py"
    )

    assert script.is_file()
