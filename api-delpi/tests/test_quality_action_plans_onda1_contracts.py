"""Contratos Onda 1 — rotas PAC expostas pela api-delpi (fonte de verdade para homologação local)."""

from __future__ import annotations

from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

ONDA1_OPERATION_IDS = frozenset(
    {
        "get_quality_action_plans_dashboard",
        "list_quality_action_plans_overdue",
        "list_quality_action_plans",
        "get_quality_action_plan_detail",
        "create_quality_action_plan",
        "update_quality_action_plan",
        "update_quality_action_plan_status",
        "upsert_quality_action_plan_ishikawa",
        "upsert_quality_action_plan_five_whys",
        "create_quality_action_plan_actions",
        "update_quality_action_plan_action",
        "record_quality_action_plan_effectiveness",
        "upsert_quality_action_plan_rnc_8d",
        "export_quality_action_plan_rnc_8d",
        "list_quality_action_plan_evidences",
        "attach_quality_action_plan_evidence",
        "download_quality_action_plan_evidence",
        "get_quality_action_plan_evidence_content",
        "update_quality_action_plan_evidence",
        "delete_quality_action_plan_evidence",
    }
)


def test_onda1_pac_operation_ids_registered() -> None:
    missing = sorted(ONDA1_OPERATION_IDS - ROUTE_CONTRACTS.keys())
    assert not missing, f"operation_id Onda 1 ausente em ROUTE_CONTRACTS: {missing}"


def test_onda1_evidence_and_8d_contract_entities() -> None:
    assert ROUTE_CONTRACTS["attach_quality_action_plan_evidence"].entity == "quality_action_plan_evidence"
    assert ROUTE_CONTRACTS["export_quality_action_plan_rnc_8d"].entity == "quality_action_plan_export"
    assert ROUTE_CONTRACTS["upsert_quality_action_plan_rnc_8d"].entity == "quality_action_plan"
