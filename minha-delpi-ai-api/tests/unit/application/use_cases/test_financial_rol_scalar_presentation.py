"""Regressão — ROL escalar exibe valores e não classifica como lista vazia."""

from __future__ import annotations

from app.application.services.chat_tool_context_external_action_formatter import (
    ChatToolContextExternalActionFormatter,
)
from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def _rol_envelope() -> dict:
    return {
        "success": True,
        "message": "ROL consultado com sucesso.",
        "data": {
            "branch": "01",
            "start_date": "20260611",
            "end_date": "20260611",
            "gross_revenue": 13027.76,
            "other_values": 0,
            "items_without_tes": 0,
            "returns": 0.0,
            "discounts": 0.0,
            "icms": 911.75,
            "iss": 0,
            "pis": 920.61,
            "cofins": 199.74,
            "ipi_separated": 0,
            "rol_taxes": 2032.1,
            "rol": 10995.66,
            "rol_with_ipi": 10995.66,
            "financial_titles": 0,
            "financial_balance": 0,
        },
        "meta": {
            "operationId": "get_financial_rol",
            "entity": "financial_rol",
            "shape": "scalar",
            "fields": {
                "gross_revenue": "Receita bruta",
                "rol": "ROL",
                "icms": "ICMS",
            },
            "fieldFormats": {
                "gross_revenue": "currency",
                "rol": "currency",
                "icms": "currency",
            },
        },
    }


def _build_metadata(*, session_format: str = "") -> dict:
    use_case = ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )
    params = {"userMessage": "qual o rol da filial 01 hoje"}

    if session_format:
        params["sessionResponseFormat"] = session_format

    return use_case._build_presentation_metadata(
        action={"path": "/financial/rol"},
        sanitized_data=_rol_envelope(),
        resolved_path="/financial/rol",
        request_parameters=params,
    )


def test_financial_rol_scalar_data_answer_has_metric_highlights():
    meta = _build_metadata()
    data_answer = meta.get("dataAnswer") or {}
    summary = str((data_answer.get("summary") or {}).get("answer") or "")

    assert data_answer.get("profileKey") == "generic_kpi_series"
    assert "retornou registros" not in summary.lower()
    assert any(
        isinstance(item, dict) and item.get("type") == "empty_list"
        for item in (data_answer.get("anomalies") or [])
    ) is False


def test_financial_rol_text_presentation_includes_rol_value():
    meta = _build_metadata(session_format="text")
    markdown = str((meta.get("textPresentation") or {}).get("markdown") or "")
    data_answer = str((meta.get("dataAnswer") or {}).get("summary", {}).get("answer") or "")
    humanized = meta.get("humanizedSummary") or {}
    linhas = humanized.get("linhas") or []

    assert "retornou registros" not in markdown.lower()
    assert (
        "10995" in markdown
        or "13.027" in markdown
        or "ROL" in markdown
        or "10995" in data_answer
        or "ROL" in data_answer
        or any("ROL" in str(line) for line in linhas)
    )


def test_financial_rol_dashboard_builds_dashboard_presentation():
    meta = _build_metadata(session_format="dashboard")
    dashboard = meta.get("dashboardPresentation") or meta.get("kpiPresentation") or {}
    decision = meta.get("presentationDecision") or {}
    render_plan = meta.get("renderPlan") or {}
    segment_kinds = {
        str(item.get("kind") or "").strip().lower()
        for item in (render_plan.get("segments") or [])
        if isinstance(item, dict)
    }

    assert decision.get("selected") == "dashboard"
    assert dashboard.get("type") in {"dashboard", "kpi"} or "kpi" in segment_kinds
    assert "dashboard" in segment_kinds or "kpi" in segment_kinds
    assert "sem dados tabulares" not in str(decision.get("reason") or "").lower()


def test_financial_rol_auto_prefers_kpi_over_empty_table_reason():
    meta = _build_metadata()
    decision = meta.get("presentationDecision") or {}

    assert decision.get("selected") in {"kpi", "text", "dashboard"}
    assert "sem dados tabulares" not in str(decision.get("reason") or "").lower()
    kpi_or_dashboard = (meta.get("kpiPresentation") or meta.get("presentation") or {}).get(
        "type"
    ) in {"kpi", "dashboard"} or (
        meta.get("dashboardPresentation") or {}
    ).get("type") == "dashboard"
    assert kpi_or_dashboard


def test_formatter_does_not_downgrade_scalar_data_answer_without_api_meta():
    meta = _build_metadata(session_format="text")
    meta.pop("dataAnswer", None)
    meta.pop("dataCommentary", None)
    meta.pop("apiDelpiResponseMeta", None)

    formatter = ChatToolContextExternalActionFormatter(ExternalActionResultPresenter())
    safe = formatter._build_safe_tool_metadata(
        "execute_external_action",
        meta,
        _rol_envelope(),
    )

    data_answer = safe.get("dataAnswer") or {}
    summary = str((data_answer.get("summary") or {}).get("answer") or "")

    assert data_answer.get("profileKey") == "generic_kpi_series"
    assert "retornou registros" not in summary.lower()

    humanized = safe.get("humanizedSummary") or {}
    joined = "\n".join(humanized.get("linhas") or [])

    assert "retornou registros" not in joined.lower()
    assert (
        "ROL" in joined
        or "Receita bruta" in joined
        or "ROL" in summary
        or "Receita bruta" in summary
    )
