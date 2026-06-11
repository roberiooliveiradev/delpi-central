"""Contrato API→MFE Playbook 13 P6 (sem reimplementar TypeScript)."""

from __future__ import annotations

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta
from tests.fixtures.presentation_render_plan_gate import (
    P6_EXTENDED_PIPELINE_CASES,
    _validate_render_plan_contract,
    _validate_suppressed_presentations_removed,
    find_render_plan_gaps,
)


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def test_mfe_parity_gate_has_no_render_plan_gaps():
    assert find_render_plan_gaps() == []


def test_mfe_parity_no_latent_dashboard_on_factory_status_auto():
    case = next(
        item for item in P6_EXTENDED_PIPELINE_CASES if item["id"] == "factory_status_auto_reference"
    )
    metadata = _use_case()._build_presentation_metadata(
        action={"path": case["path"]},
        sanitized_data=load_api_delpi_fixture_with_meta(case["fixture"]),
        resolved_path=case["path"],
        request_parameters={},
    )

    assert _validate_render_plan_contract(metadata) == []
    assert _validate_suppressed_presentations_removed(metadata) == []
    assert metadata.get("dashboardPresentation") is None

    render_plan = metadata["renderPlan"]
    segment_kinds = {
        str(item.get("kind") or "").strip().lower()
        for item in render_plan.get("segments") or []
        if isinstance(item, dict)
    }

    assert "dashboard" not in segment_kinds
