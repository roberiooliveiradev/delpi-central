"""Sprint 4 — programação do dia com códigos auditáveis na tabela e no texto."""

from __future__ import annotations

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import (
    load_api_delpi_fixture_with_meta,
)


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def test_production_schedule_today_table_preserves_product_codes() -> None:
    envelope = load_api_delpi_fixture_with_meta("production_schedule_today_20260622.json")
    metadata = _use_case()._build_presentation_metadata(
        action={"path": "/production/schedule/today"},
        sanitized_data=envelope,
        resolved_path="/production/schedule/today",
        request_parameters={"userMessage": "programação de hoje"},
    )

    table = metadata.get("tablePresentation")

    if not isinstance(table, dict) or table.get("type") != "table":
        primary = metadata.get("presentation")
        table = primary if isinstance(primary, dict) and primary.get("type") == "table" else None

    assert table is not None
    rows = table.get("rows") or []
    codes = {
        str(row.get("product_code") or "").strip()
        for row in rows
        if isinstance(row, dict)
    }

    assert "90260140" in codes
    assert "90261255" in codes


def test_production_schedule_today_text_lists_codes_with_descriptions() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("production_schedule_today_20260622.json")
    result = presenter.present(envelope, path="/production/schedule/today")
    joined = "\n".join(str(line) for line in result.get("linhas") or [])

    assert "90260140" in joined
    assert "90261255" in joined
    assert "PA HOMOLOGADO REF" in joined


def test_production_schedule_today_automatic_omits_redundant_dashboard() -> None:
    envelope = load_api_delpi_fixture_with_meta("production_schedule_today_20260622.json")
    metadata = _use_case()._build_presentation_metadata(
        action={"path": "/production/schedule/today"},
        sanitized_data=envelope,
        resolved_path="/production/schedule/today",
        request_parameters={
            "userMessage": "quais produtos estão programados para produzir hoje",
        },
    )

    render_plan = metadata.get("renderPlan") or {}
    segments = render_plan.get("segments") or []
    kinds = {str(item.get("kind") or "").strip().lower() for item in segments if isinstance(item, dict)}
    decision = metadata.get("presentationDecision") or {}
    suppressed = (
        ((metadata.get("stackPresentationPlan") or {}).get("renderHints") or {}).get(
            "suppressedKinds"
        )
        or []
    )

    assert metadata.get("dashboardPresentation") is None
    assert "dashboard" not in kinds
    assert decision.get("selected") == "table"
    assert metadata.get("preferredFormat") == "table"
    assert "table" not in suppressed

    table_segments = [item for item in segments if isinstance(item, dict) and item.get("kind") == "table"]

    assert len(table_segments) == 1


def test_production_schedule_today_text_first_respects_table_when_available() -> None:
    """Regressão: entidade OpenAPI sem metadata não pode forçar texto e ocultar tabela."""
    from app.domain.services.chat_presentation_text_first_policy_service import (
        ChatPresentationTextFirstPolicyService,
    )

    assert not ChatPresentationTextFirstPolicyService.should_default_to_text_only(
        path="/production/schedule/today",
        entity="production_schedule_today",
        user_message="produtos programados para produzir hoje",
    )
