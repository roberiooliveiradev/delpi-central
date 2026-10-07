"""Portal × TÉO 100% capability-parity closure — structural + behavioral tests.

Covers the parity wave that closed the catalog gaps:
- analyze extended views (dashboard live, revision comparison, decomposition
  compute, diagram/BPMN, impact-effort matrix, revision merges)
- meeting_minute_workflow refuse action (authenticated refusal)
- instance contexto write via prepare_record_change
- update_signature_profile / import_diagram_bpmn_xml governed operations
- signature_profile read folded into get_my_context
- exposure_classification accounting: parity_gap == 0
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)

from tm_app.application.gpt_actions.capability_descriptors import (
    build_capability_surface_catalog,
)
from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
)
from tm_app.application.gpt_actions.entities import (
    GptAnalysisView,
    GptMeetingMinuteWorkflow,
)
from tm_app.application.governed_writes.confirmation_policy import (
    AUTO_ACT,
    CONFIRM_BEFORE_ACT,
    execution_policy_for_capability,
)
from tm_app.application.governed_writes.orchestrator import (
    GOVERNED_OPERATION_ACTION_TO_CAPABILITY,
    MEETING_MINUTE_ACTION_TO_CAPABILITY,
    WRITE_CAPABILITIES,
)
from tm_app.application.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from tm_app.interface.mcp.server import create_mcp_server
from tm_app.interface.mcp import tool_bridge


def _tools() -> dict[str, dict]:
    tools = asyncio.run(create_mcp_server().list_tools())
    return {t.name: t for t in tools}


def _input_schema(tool) -> dict:
    schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", {})
    return dict(schema or {})


def _user_context(*, permissions: list[str] | None = None):
    user_token = set_current_user(
        SimpleNamespace(
            id="u1",
            email="teo@example.com",
            name="Téo",
            roles=[],
            groups=[],
            permissions=(
                permissions
                if permissions is not None
                else ["transformometro.access"]
            ),
            is_superadmin=False,
        )
    )
    auth_token = set_request_authorization("Bearer test")
    return user_token, auth_token


def _reset_context(tokens) -> None:
    user_token, auth_token = tokens
    reset_request_authorization(auth_token)
    reset_current_user(user_token)
    reset_proposal_store_for_tests()


def _payload(result):
    return result.structured_content


# --------------------------------------------------------- catalog accounting


def test_catalog_parity_gap_is_zero() -> None:
    for transport in ("gpt_actions", "mcp"):
        ec = build_capability_surface_catalog(transport)[
            "exposure_classification"
        ]
        assert ec["parity_gap"] == []
        for bucket in (
            "exposed",
            "platform_blocked",
            "technical_only",
            "public_token_flow",
            "intentionally_not_applicable",
        ):
            assert bucket in ec


def test_classification_ids_are_unique_and_closed() -> None:
    ec = build_capability_surface_catalog("mcp")["exposure_classification"]
    seen: dict[str, str] = {}
    for bucket, items in ec.items():
        for item in items:
            iid = item["id"]
            assert iid not in seen, f"duplicate capability id {iid}"
            seen[iid] = bucket
            assert iid not in {"unknown", "unclassified", "to_inventory"}
    for gap_id in (
        "dashboard.extended_views",
        "decomposition.suggest_validate",
        "processo.comparativo_revisoes",
        "instance.contexto",
        "meeting_minute.sign_refuse",
        "process_file.metadata_write",
        "signature_profile",
        "diagram.bpmn_xml",
    ):
        assert seen.get(gap_id) == "exposed", gap_id


def test_closed_gap_justifications_reference_real_surface() -> None:
    ec = build_capability_surface_catalog("mcp")["exposure_classification"]
    exposed = {item["id"]: item["via"] for item in ec["exposed"]}
    assert "analyze" in exposed["dashboard.extended_views"]
    assert "meeting_minute_workflow" in exposed["meeting_minute.sign_refuse"]
    assert "manage_evidence" in exposed["process_file.metadata_write"]
    assert "prepare_record_change" in exposed["instance.contexto"]
    assert "changes.contexto" in exposed["instance.contexto"]
    assert "data.contexto" not in exposed["instance.contexto"]
    assert "update_signature_profile" in exposed["signature_profile"]
    assert "import_diagram_bpmn_xml" in exposed["diagram.bpmn_xml"]


def test_instance_contexto_published_in_entity_schema() -> None:
    from tm_app.application.gpt_actions.registration_guide import (
        build_registration_guide,
    )

    for transport in ("gpt_actions", "mcp"):
        guide = build_registration_guide(transport)
        schema = guide["entity_schemas"]["instance"]
        assert "contexto" in schema["optional"]
        assert any(
            "instancia_contexto_v1" in note for note in schema["notes"]
        )


# -------------------------------------------------------------- MCP schemas


def test_mcp_analyze_view_enum_projects_canonical() -> None:
    schema = _input_schema(_tools()["analyze"])
    enum = set(schema["properties"]["view"]["enum"])
    assert enum == {v.value for v in GptAnalysisView}


def test_mcp_minute_change_enum_projects_canonical() -> None:
    schema = _input_schema(_tools()["prepare_meeting_minute_change"])
    enum = set(schema["properties"]["action"]["enum"])
    assert enum == set(MEETING_MINUTE_ACTION_TO_CAPABILITY)
    assert "refuse" in enum


def test_mcp_governed_operation_enum_projects_canonical() -> None:
    schema = _input_schema(_tools()["prepare_governed_operation"])
    enum = set(schema["properties"]["action"]["enum"])
    assert enum == set(GOVERNED_OPERATION_ACTION_TO_CAPABILITY)
    assert {"update_signature_profile", "import_diagram_bpmn_xml"} <= enum


# ------------------------------------------------------- capability registry


def test_new_governed_operations_are_write_capabilities() -> None:
    assert GOVERNED_OPERATION_ACTION_TO_CAPABILITY[
        "update_signature_profile"
    ] == "update_signature_profile"
    assert GOVERNED_OPERATION_ACTION_TO_CAPABILITY[
        "import_diagram_bpmn_xml"
    ] == "import_diagram_bpmn_xml"
    assert {"update_signature_profile", "import_diagram_bpmn_xml"} <= (
        WRITE_CAPABILITIES
    )


def test_refuse_is_meeting_minute_workflow_capability() -> None:
    assert (
        MEETING_MINUTE_ACTION_TO_CAPABILITY["refuse"]
        == "meeting_minute_workflow"
    )
    assert GptMeetingMinuteWorkflow.REFUSE.value == "refuse"
    # Refusal is a recorded rejection — confirm_before_act like the rest
    # of the workflow family.
    assert (
        execution_policy_for_capability("meeting_minute_workflow")
        == CONFIRM_BEFORE_ACT
    )


def test_new_governed_operation_policies() -> None:
    # Own-profile display name — additive personal metadata.
    assert (
        execution_policy_for_capability("update_signature_profile")
        == AUTO_ACT
    )
    # Replaces the whole macro diagram — consequential overwrite.
    assert (
        execution_policy_for_capability("import_diagram_bpmn_xml")
        == CONFIRM_BEFORE_ACT
    )


# --------------------------------------------------------- PREPARE / ACT


def test_minute_refuse_requires_reason_at_prepare() -> None:
    tokens = _user_context()
    try:
        with patch.object(
            tool_bridge._dispatch._minutes, "_load", return_value={"id": "m1"}
        ), patch.object(
            tool_bridge._dispatch, "get_record", return_value={"id": "m1"}
        ):
            prep = tool_bridge.tool_prepare_meeting_minute_change(
                action="refuse", minute_id="m1"
            )
        data = _payload(prep)["data"]
        assert data["proposal"]["ready"] is False
        handle = data["proposal"]["handle"]
        denied = tool_bridge.tool_commit_proposal(handle, confirmation=True)
        assert _payload(denied)["success"] is False
    finally:
        _reset_context(tokens)


def test_minute_refuse_confirm_before_act_chain() -> None:
    tokens = _user_context()
    try:
        write_result = {
            "minute": {"id": "m1", "status": "in_review"},
            "verified": True,
        }
        with patch.object(
            tool_bridge._dispatch._minutes, "_load", return_value={"id": "m1"}
        ), patch.object(
            tool_bridge._dispatch, "get_record", return_value={"id": "m1"}
        ), patch.object(
            tool_bridge._dispatch,
            "meeting_minute_workflow",
            return_value=write_result,
        ) as write:
            prep = tool_bridge.tool_prepare_meeting_minute_change(
                action="refuse", minute_id="m1", reason="discordo do teor"
            )
            data = _payload(prep)["data"]
            assert data["persisted"] is False
            assert (
                data["proposal"]["execution_policy"] == "confirm_before_act"
            )
            denied = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=False
            )
            assert _payload(denied)["success"] is False
            committed = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=True
            )
            assert _payload(committed)["success"] is True
            write.assert_called_once()
            assert (
                write.call_args.kwargs.get("action")
                or write.call_args[1].get("action")
            ) == "refuse"
    finally:
        _reset_context(tokens)


def test_signature_profile_auto_act_chain() -> None:
    tokens = _user_context()
    try:
        profile = {"user_id": "u1", "display_name": "Ana", "has_signature": True}
        updated = {"user_id": "u1", "display_name": "Ana Paula"}
        with patch.object(
            tool_bridge._dispatch,
            "get_my_signature_profile",
            # PREPARE → profile; commit-time fingerprint recompute → still
            # profile (unchanged); verify read-back → updated.
            side_effect=[profile, profile, updated],
        ), patch.object(
            tool_bridge._dispatch,
            "update_signature_profile",
            return_value={
                "updated": updated,
                "persisted": True,
                "verified": True,
            },
        ) as write:
            prep = tool_bridge.tool_prepare_governed_operation(
                action="update_signature_profile", display_name="Ana Paula"
            )
            data = _payload(prep)["data"]
            assert data["persisted"] is False
            assert data["proposal"]["execution_policy"] == "auto_act"
            committed = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=False
            )
            assert _payload(committed)["success"] is True
            write.assert_called_once()
    finally:
        _reset_context(tokens)


def test_bpmn_import_requires_confirmation() -> None:
    tokens = _user_context()
    try:
        validation = {
            "processo_id": "p1",
            "current_diagram": {"conteudo": {"nodes": []}},
            "parsed_nodes": 3,
            "parsed_edges": 2,
        }
        with patch.object(
            tool_bridge._dispatch,
            "validate_bpmn_import",
            return_value=validation,
        ), patch.object(
            tool_bridge._dispatch,
            "read_process_diagram",
            return_value={"conteudo": {"nodes": [{"id": "n"}]}},
        ), patch.object(
            tool_bridge._dispatch,
            "import_diagram_bpmn_xml",
            return_value={"verified": True, "nodes": 3},
        ):
            prep = tool_bridge.tool_prepare_governed_operation(
                action="import_diagram_bpmn_xml",
                processo_id="p1",
                xml="<definitions/>",
            )
            data = _payload(prep)["data"]
            assert data["persisted"] is False
            assert (
                data["proposal"]["execution_policy"] == "confirm_before_act"
            )
            denied = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=False
            )
            assert _payload(denied)["success"] is False
    finally:
        _reset_context(tokens)


def test_governed_operation_rejects_unknown_action() -> None:
    tokens = _user_context()
    try:
        result = tool_bridge.tool_prepare_governed_operation(
            action="drop_everything"
        )
        payload = _payload(result)
        assert payload["success"] is False
        assert payload["status_code"] == 400
    finally:
        _reset_context(tokens)


# ----------------------------------------------------- instance contexto


def test_instance_contexto_write_uses_canonical_path() -> None:
    dispatch = GptActionsDispatchService()
    request = SimpleNamespace(state=SimpleNamespace(user=SimpleNamespace(id="u1")))
    existing = {"instancia_id": "i1", "processo_id": "p1"}
    contexto = {
        "format": "instancia_contexto_v1",
        "format_version": 1,
        "node_notes": {"n1": "contexto"},
        "links": [],
    }
    with patch(
        "tm_app.application.gpt_actions.dispatch_service."
        "check_instancia_manage_access",
        return_value=None,
    ), patch(
        "tm_app.application.gpt_actions.dispatch_service."
        "ProcessoInstanciaRepository"
    ) as repo_cls, patch(
        "tm_app.application.gpt_actions.dispatch_service."
        "touch_processo_updated_at"
    ), patch.object(dispatch, "_audit"):
        repo = repo_cls.return_value
        repo.get.side_effect = [existing, {"contexto": contexto}]
        data, _msg = dispatch._update_instancia(
            request, "i1", {"contexto": contexto}
        )
        repo.update_contexto.assert_called_once_with("i1", contexto)
        repo.update.assert_not_called()
        assert data["verified"] is True
        assert data["contexto"] == contexto


def test_instance_contexto_rejects_invalid_shape() -> None:
    dispatch = GptActionsDispatchService()
    request = SimpleNamespace(state=SimpleNamespace(user=SimpleNamespace(id="u1")))
    existing = {"instancia_id": "i1", "processo_id": "p1"}
    with patch(
        "tm_app.application.gpt_actions.dispatch_service."
        "check_instancia_manage_access",
        return_value=None,
    ), patch(
        "tm_app.application.gpt_actions.dispatch_service."
        "ProcessoInstanciaRepository"
    ) as repo_cls:
        repo_cls.return_value.get.return_value = existing
        with pytest.raises(Exception) as excinfo:
            dispatch._update_instancia(
                request, "i1", {"contexto": {"format": "wrong"}}
            )
        assert getattr(excinfo.value, "status_code", None) == 400


# ------------------------------------------------------------- my context


def test_my_context_signature_profile_permission_gated() -> None:
    tokens = _user_context()
    try:
        with patch.object(
            tool_bridge._user_context,
            "get_my_context",
            return_value={"display_name": "Téo", "email": "teo@example.com"},
        ), patch.object(
            tool_bridge._dispatch,
            "my_signature_profile_or_none",
            return_value={"display_name": "Ana", "has_signature": True},
        ):
            result = tool_bridge.tool_get_my_context()
            data = _payload(result)["data"]
            assert data["signature_profile"]["display_name"] == "Ana"
    finally:
        _reset_context(tokens)


def test_my_context_signature_profile_none_when_denied() -> None:
    tokens = _user_context()
    try:
        with patch.object(
            tool_bridge._user_context,
            "get_my_context",
            return_value={"display_name": "Téo"},
        ), patch.object(
            tool_bridge._dispatch,
            "my_signature_profile_or_none",
            return_value=None,
        ):
            result = tool_bridge.tool_get_my_context()
            data = _payload(result)["data"]
            assert data["signature_profile"] is None
    finally:
        _reset_context(tokens)


# -------------------------------------------------------------- analyze


def test_analyze_rejects_unknown_view() -> None:
    tokens = _user_context()
    try:
        result = tool_bridge.tool_analyze(view="delete_everything")
        payload = _payload(result)
        assert payload["success"] is False
        assert payload["status_code"] in (400, 401, 403)
    finally:
        _reset_context(tokens)


def test_analyze_new_views_reach_canonical_dispatch() -> None:
    tokens = _user_context()
    try:
        captured = {}
        real_analyze = tool_bridge._dispatch.analyze

        def spy(request, view=None, **kwargs):
            captured["view"] = view
            raise LookupError("stop-before-db")

        for view in (
            "dashboard_alerts",
            "dashboard_evolution",
            "dashboard_by_family",
            "dashboard_due_dates",
            "dashboard_strategic_indicators",
            "process_revision_comparison",
            "decomposition_link_validation",
            "decomposition_draft_suggestion",
            "diagram_validation",
            "diagram_bpmn_xml",
            "impact_effort_matrix",
            "revision_allocation_diagnostic",
            "revision_diagram_merged",
            "revision_decomposition_merged",
        ):
            captured.clear()
            with patch.object(
                tool_bridge._dispatch, "analyze", side_effect=spy
            ):
                result = tool_bridge.tool_analyze(
                    view=view, processo_id="p", revisao_id="r", instancia_id="i"
                )
            assert captured.get("view") == view, view
    finally:
        _reset_context(tokens)


# --------------------------------------------------- link validator (canonical)


def test_link_validator_orphan_processo_chave() -> None:
    from tm_app.application.services.decomposition_flowchart_link_validator import (
        DecompositionFlowchartLinkValidator,
    )

    tree = {
        "nodes": [
            {"id": "pk-1", "level": "processo_chave", "disabled": False},
            {"id": "pk-2", "level": "processo_chave", "disabled": True},
            {"id": "sub-1", "level": "subprocesso", "disabled": False},
        ]
    }
    flowchart = {"nodes": [{"id": "f1", "meta": {"decomposition_id": "pk-9"}}]}
    out = DecompositionFlowchartLinkValidator().validate(
        tree=tree, flowchart=flowchart
    )
    codes = {w["code"] for w in out["warnings"]}
    assert "invalid_decomposition_id" in codes
    assert "unlinked_processo_chave" in codes
    orphan = [w for w in out["warnings"] if w["code"] == "unlinked_processo_chave"]
    assert {w["decomposition_id"] for w in orphan} == {"pk-1"}
    assert out["valid"] is False


def test_link_validator_clean_tree() -> None:
    from tm_app.application.services.decomposition_flowchart_link_validator import (
        DecompositionFlowchartLinkValidator,
    )

    tree = {"nodes": [{"id": "pk-1", "level": "processo_chave"}]}
    flowchart = {"nodes": [{"id": "f1", "meta": {"decomposition_id": "pk-1"}}]}
    out = DecompositionFlowchartLinkValidator().validate(
        tree=tree, flowchart=flowchart
    )
    assert out["valid"] is True
    assert out["warnings"] == []


# ------------------------------------------------------------- no proxy


def test_no_generic_proxy_capability_ids() -> None:
    forbidden = {
        "execute_anything",
        "execute_capability",
        "generic_http",
        "proxy_route",
        "sql_query",
        "call_any_route",
    }
    catalog = build_capability_surface_catalog("mcp")
    ec = catalog["exposure_classification"]
    ids = {
        item["id"]
        for items in ec.values()
        for item in items
    }
    assert not (ids & forbidden)
    assert not (
        forbidden & set(GOVERNED_OPERATION_ACTION_TO_CAPABILITY)
    )
    assert not (forbidden & set(MEETING_MINUTE_ACTION_TO_CAPABILITY))
