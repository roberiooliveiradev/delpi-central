"""E5 — TÉO governed surface for Interaction Rooms V2 room management.

Contract-level coverage (tool_bridge / orchestrator / OpenAPI), never a
parallel authority: every PREPARE seals an exact change + fingerprint,
ACT re-resolves the fingerprint and the canonical
InteractionRoomUseCases re-authorize and verify read-back.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)

from tm_app.application.governed_writes.confirmation_policy import (
    AUTO_ACT,
    CONFIRM_BEFORE_ACT,
    execution_policy_for_capability,
)
from tm_app.application.governed_writes.orchestrator import (
    COLLABORATION_ACTION_TO_CAPABILITY,
    COLLABORATION_READ_ACTIONS,
    INTERACTION_ROOM_CAPABILITIES,
)
from tm_app.application.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from tm_app.application.gpt_actions.openapi_builder import (
    build_gpt_actions_openapi,
)
from tm_app.domain.services.interaction_room_access_service import (
    StaleRoomAuthorization,
)
from tm_app.interface.mcp import tool_bridge


# ----------------------------------------------------------------- helpers


def _user_context(*, permissions: list[str] | None = None, user_id: str = "u1"):
    user_token = set_current_user(
        SimpleNamespace(
            id=user_id,
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


_IMPACT = {
    "room_id": "room-1",
    "deleted": False,
    "access_scope": "members",
    "protected_content_count": 0,
    "participant_count": 1,
    "link_roles": ["helpdesk_ticket:primary"],
    "active_link_ids": ["link-1"],
    "participant_user_ids": ["u1"],
}


# ---------------------------------------------------------------- policies


def test_room_management_policy_classification() -> None:
    for cap in (
        "create_standalone_room",
        "add_room_link",
        "remove_room_link",
        "remove_room_participant",
        "delete_interaction_room",
        "restore_interaction_room",
    ):
        assert execution_policy_for_capability(cap) == CONFIRM_BEFORE_ACT, cap
    assert (
        execution_policy_for_capability("add_room_participant") == AUTO_ACT
    )


def test_collaboration_action_map_covers_v2_writes() -> None:
    for action in (
        "create_standalone_room",
        "add_room_link",
        "remove_room_link",
        "add_participant",
        "remove_participant",
        "delete_room",
        "restore_room",
    ):
        assert action in COLLABORATION_ACTION_TO_CAPABILITY, action
        assert (
            COLLABORATION_ACTION_TO_CAPABILITY[action]
            in INTERACTION_ROOM_CAPABILITIES
        )


def test_collaboration_read_actions_cover_v2_reads() -> None:
    assert {
        "room_links",
        "room_participants",
        "room_impact",
        "resolve_room",
    } <= COLLABORATION_READ_ACTIONS


# --------------------------------------------------------- PREPARE → ACT


def test_add_participant_auto_act_chain_with_impact_read_back() -> None:
    tokens = _user_context()
    try:
        impact_after = dict(_IMPACT, participant_count=2)
        impact_after["participant_user_ids"] = ["u1", "u2"]
        with patch.object(
            tool_bridge._dispatch, "room_impact", return_value=_IMPACT
        ) as impact, patch.object(
            tool_bridge._dispatch,
            "room_write",
            return_value={"added": True, "room_id": "room-1", "user_id": "u2"},
        ) as write:
            # Fingerprint must be identical at recompute; verify needs the
            # member visible — return the same sealed impact at prepare and
            # recompute, then the post-write impact at verify.
            impact.side_effect = [_IMPACT, _IMPACT, impact_after]
            prep = tool_bridge.tool_prepare_collaboration_change(
                action="add_participant", room_id="room-1", user_id="u2"
            )
            data = _payload(prep)["data"]
            assert data["persisted"] is False
            assert data["proposal"]["execution_policy"] == "auto_act"
            assert data["proposal"]["exact_change"]["user_id"] == "u2"
            committed = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=False
            )
            result = _payload(committed)
            assert result["success"] is True
            write.assert_called_once()
            assert result["data"]["persisted"] is True
            assert result["data"]["postcondition"]["verified"] is True
    finally:
        _reset_context(tokens)


def test_remove_room_link_requires_confirmation() -> None:
    tokens = _user_context()
    try:
        with patch.object(
            tool_bridge._dispatch, "room_impact", return_value=_IMPACT
        ):
            prep = tool_bridge.tool_prepare_collaboration_change(
                action="remove_room_link", room_id="room-1", link_id="link-1"
            )
            data = _payload(prep)["data"]
            assert data["proposal"]["execution_policy"] == "confirm_before_act"
            denied = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=False
            )
            result = _payload(denied)
            assert result["success"] is False
            assert result["data"].get("error_code") == "CONFIRMATION_REQUIRED"
    finally:
        _reset_context(tokens)


def test_delete_room_confirm_and_impact_flip_verified() -> None:
    tokens = _user_context()
    try:
        deleted = dict(_IMPACT, deleted=True)
        with patch.object(
            tool_bridge._dispatch, "room_impact"
        ) as impact, patch.object(
            tool_bridge._dispatch,
            "room_write",
            return_value={"id": "room-1", "deleted": True},
        ):
            impact.side_effect = [_IMPACT, _IMPACT, deleted]
            prep = tool_bridge.tool_prepare_collaboration_change(
                action="delete_room", room_id="room-1"
            )
            data = _payload(prep)["data"]
            assert data["proposal"]["execution_policy"] == "confirm_before_act"
            committed = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=True
            )
            result = _payload(committed)
            assert result["success"] is True
            assert result["data"]["postcondition"]["verified"] is True
    finally:
        _reset_context(tokens)


def test_remove_room_link_verify_via_active_link_ids() -> None:
    tokens = _user_context()
    try:
        after = dict(_IMPACT)
        after["active_link_ids"] = []
        after["link_roles"] = []
        with patch.object(
            tool_bridge._dispatch, "room_impact"
        ) as impact, patch.object(
            tool_bridge._dispatch,
            "room_write",
            return_value={"removed": True, "link_id": "link-1"},
        ):
            impact.side_effect = [_IMPACT, _IMPACT, after]
            prep = tool_bridge.tool_prepare_collaboration_change(
                action="remove_room_link", room_id="room-1", link_id="link-1"
            )
            data = _payload(prep)["data"]
            committed = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=True
            )
            assert _payload(committed)["success"] is True
    finally:
        _reset_context(tokens)


def test_self_removal_uses_member_projection_and_denial_proof() -> None:
    """A plain member removing themselves is not admin — fingerprint comes
    from the member-readable room, and the verify proof is the resulting
    access denial (the member is now locked out)."""
    tokens = _user_context(user_id="u1")
    try:
        room = {"id": "room-1", "participants": [{"user_id": "u1"}]}
        calls = {"n": 0}

        def get_room(*_a, **_k):
            calls["n"] += 1
            if calls["n"] <= 2:
                return room
            raise PermissionError("not_found")

        with patch.object(
            tool_bridge._dispatch, "get_room", side_effect=get_room
        ), patch.object(
            tool_bridge._dispatch, "room_impact"
        ) as impact, patch.object(
            tool_bridge._dispatch,
            "room_write",
            return_value={"removed": True, "user_id": "u1"},
        ):
            prep = tool_bridge.tool_prepare_collaboration_change(
                action="remove_participant", room_id="room-1", user_id="u1"
            )
            data = _payload(prep)["data"]
            # Admin-safe impact projection must NOT be consulted for a
            # non-admin actor.
            impact.assert_not_called()
            committed = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=True
            )
            result = _payload(committed)
            assert result["success"] is True
            assert result["data"]["postcondition"]["verified"] is True
    finally:
        _reset_context(tokens)


def test_fingerprint_drift_blocks_act() -> None:
    """State changed between PREPARE and ACT → proposal rejected."""
    tokens = _user_context()
    try:
        drifted = dict(_IMPACT, participant_count=3)
        with patch.object(
            tool_bridge._dispatch, "room_impact"
        ) as impact, patch.object(
            tool_bridge._dispatch, "room_write"
        ) as write:
            impact.side_effect = [_IMPACT, drifted]
            prep = tool_bridge.tool_prepare_collaboration_change(
                action="add_participant", room_id="room-1", user_id="u2"
            )
            data = _payload(prep)["data"]
            committed = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=False
            )
            result = _payload(committed)
            assert result["success"] is False
            write.assert_not_called()
    finally:
        _reset_context(tokens)


def test_revocation_between_prepare_and_act_blocks() -> None:
    tokens = _user_context()
    try:
        with patch.object(
            tool_bridge._dispatch, "room_impact"
        ) as impact, patch.object(
            tool_bridge._dispatch, "room_write"
        ) as write:
            impact.side_effect = [_IMPACT, PermissionError("denied")]
            prep = tool_bridge.tool_prepare_collaboration_change(
                action="remove_room_link", room_id="room-1", link_id="link-1"
            )
            data = _payload(prep)["data"]
            committed = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=True
            )
            result = _payload(committed)
            assert result["success"] is False
            write.assert_not_called()
    finally:
        _reset_context(tokens)


def test_unauthorized_user_cannot_prepare_room_write() -> None:
    tokens = _user_context(permissions=[])
    try:
        result = tool_bridge.tool_prepare_collaboration_change(
            action="add_participant", room_id="room-1", user_id="u2"
        )
        payload = _payload(result)
        assert payload["success"] is False
        assert payload["status_code"] in (401, 403)
    finally:
        _reset_context(tokens)


def test_prepare_rejects_unknown_action() -> None:
    tokens = _user_context()
    try:
        result = tool_bridge.tool_prepare_collaboration_change(
            action="wipe_room", room_id="room-1"
        )
        payload = _payload(result)
        assert payload["success"] is False
        assert payload["status_code"] == 400
    finally:
        _reset_context(tokens)


def test_prepare_reports_missing_required_fields() -> None:
    tokens = _user_context()
    try:
        with patch.object(
            tool_bridge._dispatch, "room_impact", return_value=_IMPACT
        ):
            result = tool_bridge.tool_prepare_collaboration_change(
                action="add_room_link", room_id="room-1"
            )
            payload = _payload(result)
            data = payload["data"]
            missing = data["validation_result"]["missing"]
            assert {"entity_type", "entity_key"} <= set(missing)
    finally:
        _reset_context(tokens)


def test_open_room_ticket_kind_seals_ticket_key() -> None:
    tokens = _user_context()
    try:
        prep = tool_bridge.tool_prepare_collaboration_change(
            action="open_room", room_kind="ticket", ticket_id="777"
        )
        data = _payload(prep)["data"]
        assert data["proposal"]["exact_change"]["ticket_id"] == "777"
        assert data["proposal"]["exact_change"]["room_kind"] == "ticket"
        missing_ticket = tool_bridge.tool_prepare_collaboration_change(
            action="open_room", room_kind="ticket"
        )
        payload = _payload(missing_ticket)["data"]
        assert "ticket_id" in payload["validation_result"]["missing"]
    finally:
        _reset_context(tokens)


def test_standalone_room_create_is_confirm_before_act() -> None:
    tokens = _user_context()
    try:
        prep = tool_bridge.tool_prepare_collaboration_change(
            action="create_standalone_room",
            title="War room",
            participant_ids=["u2"],
        )
        data = _payload(prep)["data"]
        assert data["proposal"]["execution_policy"] == "confirm_before_act"
        assert data["proposal"]["exact_change"]["title"] == "War room"
    finally:
        _reset_context(tokens)


def test_stale_authorization_context_propagates_typed() -> None:
    tokens = _user_context()
    try:
        with patch.object(
            tool_bridge._dispatch._rooms,
            "list_rooms",
            side_effect=StaleRoomAuthorization("ctx"),
        ):
            result = tool_bridge.tool_collaboration_read(action="rooms")
            payload = _payload(result)
            assert payload["success"] is False
            assert payload["status_code"] == 409
            assert (
                payload["data"].get("error_code")
                == "stale_authorization_context"
            )
    finally:
        _reset_context(tokens)


# ------------------------------------------------------------------- reads


def test_room_links_participants_impact_resolve_reads() -> None:
    tokens = _user_context()
    try:
        with patch.object(
            tool_bridge._dispatch,
            "list_room_links",
            return_value={"items": [], "total": 0},
        ) as links, patch.object(
            tool_bridge._dispatch,
            "list_room_participants",
            return_value={"items": [], "total": 0},
        ) as parts, patch.object(
            tool_bridge._dispatch,
            "room_impact",
            return_value=_IMPACT,
        ) as impact, patch.object(
            tool_bridge._dispatch,
            "resolve_room",
            return_value={"id": "room-1"},
        ) as resolve:
            assert _payload(
                tool_bridge.tool_collaboration_read(
                    action="room_links", room_id="room-1"
                )
            )["success"] is True
            assert _payload(
                tool_bridge.tool_collaboration_read(
                    action="room_participants", room_id="room-1"
                )
            )["success"] is True
            assert _payload(
                tool_bridge.tool_collaboration_read(
                    action="room_impact", room_id="room-1"
                )
            )["success"] is True
            assert _payload(
                tool_bridge.tool_collaboration_read(
                    action="resolve_room",
                    entity_type="process",
                    entity_key="p-1",
                )
            )["success"] is True
            links.assert_called_once()
            parts.assert_called_once()
            impact.assert_called_once()
            resolve.assert_called_once()
        missing = tool_bridge.tool_collaboration_read(action="resolve_room")
        assert _payload(missing)["success"] is False
        assert _payload(missing)["status_code"] == 400
    finally:
        _reset_context(tokens)


# ----------------------------------------------------------------- openapi


def test_openapi_contract_exposes_v2_actions_and_params() -> None:
    doc = build_gpt_actions_openapi()
    read_op = doc["paths"][
        next(
            path
            for path, methods in doc["paths"].items()
            if any(
                op.get("operationId") == "gpt_collaboration_read"
                for op in methods.values()
            )
        )
    ]["get"]
    read_enum = next(
        p for p in read_op["parameters"] if p["name"] == "action"
    )["schema"]["enum"]
    assert {
        "room_links",
        "room_participants",
        "room_impact",
        "resolve_room",
    } <= set(read_enum)
    param_names = {p["name"] for p in read_op["parameters"]}
    assert {"entity_type", "entity_key"} <= param_names

    body_schema = doc["components"]["schemas"]["GptCollaborationChangeBody"]
    write_enum = set(body_schema["properties"]["action"]["enum"])
    assert {
        "create_standalone_room",
        "add_room_link",
        "remove_room_link",
        "add_participant",
        "remove_participant",
        "delete_room",
        "restore_room",
    } <= write_enum
    for field in (
        "room_kind",
        "ticket_id",
        "entity_type",
        "entity_key",
        "link_role",
        "link_id",
        "user_id",
        "participant_ids",
    ):
        assert field in body_schema["properties"], field
