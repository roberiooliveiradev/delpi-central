"""C6 — requiredPermissionCodes: filtro obrigatório AND sobre permissões
efetivas (PermissionResolver), aplicado DEPOIS da seleção OR de
permissionCodes. Dispatches antigos sem o campo seguem inalterados."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.application.dto.dispatch_notifications_request import (
    DispatchNotificationsRequest,
)
from app.application.services.dispatch_notifications_serialization import (
    payload_dict_to_request,
    request_to_payload_dict,
)
from app.application.services.notification_recipient_resolution import (
    resolve_notification_recipient_ids,
)
from app.domain.ports.user_repository_port import UserDTO
from app.interfaces.http.notifications_controller import _parse_dispatch_body

PERM_VIEW = "production-control.machine-load.view"
PERM_BRANCH = "production-control.view.filial-01"


def _request(**overrides):
    base = dict(
        title="t",
        message="m",
        type="warning",
        category="production_control_operator_feedback",
        presentation="text",
        html_content=None,
        action_type="portal_route",
        action_label="Abrir",
        action_target="/apps/production-control/machine-load",
        icon=None,
        metadata=None,
        expires_at=None,
        broadcast=False,
        user_ids=[],
        emails=[],
        role_ids=[],
        group_ids=[],
        permission_codes=[PERM_VIEW],
        excluded_user_ids=[],
        source_app="production-control",
    )
    base.update(overrides)
    return DispatchNotificationsRequest(**base)


def _uow(selected, *, perms=None, superadmins=(), all_codes=None):
    """UoW fake: selected recebe os ids escolhidos por permissionCodes;
    perms mapeia user_id -> (direct_codes, group_codes, overrides)."""
    uow = MagicMock()
    uow.cache = None
    uow.rbac_queries.list_user_ids_by_permission_code.return_value = list(
        selected
    )
    uow.rbac_queries.list_user_ids_by_role.return_value = []
    uow.rbac_queries.list_user_ids_by_group_role.return_value = []
    uow.rbac_queries.list_user_ids_by_group.return_value = []

    perms = perms or {}

    def get_by_id(user_id):
        uid = str(user_id)
        if uid not in selected:
            return None
        return UserDTO(
            id=user_id,
            email=f"{uid}@test.com",
            name="User",
            active=True,
            is_superadmin=uid in {str(i) for i in superadmins},
            last_login_at=None,
        )

    uow.users.get_by_id.side_effect = get_by_id
    uow.users.list_all.return_value = [
        get_by_id(uid) for uid in selected
    ]
    uow.permission_queries.list_all_permission_codes.return_value = (
        all_codes if all_codes is not None else [PERM_VIEW, PERM_BRANCH]
    )

    def direct(uid):
        return list(perms.get(str(uid), ([], [], []))[0])

    def groups(uid):
        return list(perms.get(str(uid), ([], [], []))[1])

    def overrides_fn(uid):
        return list(perms.get(str(uid), ([], [], []))[2])

    uow.permission_queries.list_direct_role_permissions.side_effect = direct
    uow.permission_queries.list_group_role_permissions.side_effect = groups
    uow.permission_queries.list_user_overrides.side_effect = overrides_fn
    return uow


# --- parsing / serialização -------------------------------------------------


def test_parse_dispatch_body_accepts_required_permission_codes():
    dto = _parse_dispatch_body(
        {
            "message": "x",
            "permissionCodes": [PERM_VIEW],
            "requiredPermissionCodes": [PERM_BRANCH],
        }
    )
    assert dto.required_permission_codes == [PERM_BRANCH]
    assert dto.permission_codes == [PERM_VIEW]


def test_parse_dispatch_body_snake_case_fallback():
    dto = _parse_dispatch_body(
        {"message": "x", "required_permission_codes": ["a.b"]}
    )
    assert dto.required_permission_codes == ["a.b"]


def test_serialization_roundtrip_preserves_required_codes():
    req = _request(required_permission_codes=[PERM_BRANCH, "x.y"])
    payload = request_to_payload_dict(req)
    assert payload["requiredPermissionCodes"] == [PERM_BRANCH, "x.y"]
    back = payload_dict_to_request(payload)
    assert back.required_permission_codes == [PERM_BRANCH, "x.y"]


def test_deserialization_of_legacy_payload_defaults_empty():
    back = payload_dict_to_request({"message": "x", "permissionCodes": ["a"]})
    assert back.required_permission_codes == []


# --- resolução de destinatários ---------------------------------------------


def test_user_without_required_permission_is_filtered_out():
    allowed = str(uuid4())
    denied = str(uuid4())
    uow = _uow(
        [allowed, denied],
        perms={
            allowed: ([PERM_VIEW, PERM_BRANCH], [], []),
            denied: ([PERM_VIEW], [], []),  # sem filial-01
        },
    )
    out = resolve_notification_recipient_ids(
        uow, _request(required_permission_codes=[PERM_BRANCH])
    )
    assert out == [allowed]


def test_user_with_all_required_permissions_remains():
    uid = str(uuid4())
    uow = _uow(
        [uid],
        perms={uid: ([PERM_VIEW], [PERM_BRANCH], [])},
    )
    out = resolve_notification_recipient_ids(
        uow, _request(required_permission_codes=[PERM_BRANCH])
    )
    assert out == [uid]


def test_required_codes_must_all_match():
    uid = str(uuid4())
    uow = _uow(
        [uid],
        perms={uid: ([PERM_VIEW, PERM_BRANCH], [], [])},
    )
    out = resolve_notification_recipient_ids(
        uow,
        _request(required_permission_codes=[PERM_BRANCH, "other.code"]),
    )
    assert out == []


def test_group_granted_permission_counts():
    uid = str(uuid4())
    uow = _uow(
        [uid],
        perms={uid: ([], [PERM_VIEW, PERM_BRANCH], [])},  # só via grupo
    )
    out = resolve_notification_recipient_ids(
        uow, _request(required_permission_codes=[PERM_BRANCH])
    )
    assert out == [uid]


def test_user_override_grant_counts_and_deny_removes():
    granted = str(uuid4())
    denied = str(uuid4())
    uow = _uow(
        [granted, denied],
        perms={
            # filial-01 só via override grant
            granted: ([PERM_VIEW], [], [(PERM_BRANCH, True)]),
            # override deny remove filial-01 do papel
            denied: ([PERM_VIEW, PERM_BRANCH], [], [(PERM_BRANCH, False)]),
        },
    )
    out = resolve_notification_recipient_ids(
        uow, _request(required_permission_codes=[PERM_BRANCH])
    )
    assert out == [granted]


def test_superadmin_passes_required_filter():
    uid = str(uuid4())
    uow = _uow([uid], superadmins={uid})
    out = resolve_notification_recipient_ids(
        uow, _request(required_permission_codes=[PERM_BRANCH])
    )
    assert out == [uid]
    # superadmin bypassa via catalogo completo, sem consultar roles do user
    uow.permission_queries.list_direct_role_permissions.assert_not_called()


def test_empty_required_codes_keeps_legacy_selector_behavior():
    a, b = str(uuid4()), str(uuid4())
    uow = _uow([a, b])
    out = resolve_notification_recipient_ids(uow, _request())
    assert sorted(out) == sorted([a, b])
    # sem required codes o resolver efetivo nem é consultado
    uow.permission_queries.list_direct_role_permissions.assert_not_called()


def test_required_filter_applies_to_explicit_user_ids():
    uid = str(uuid4())
    other = str(uuid4())
    uow = _uow(
        [uid, other],
        perms={
            uid: ([PERM_BRANCH], [], []),
            other: ([], [], []),
        },
    )
    out = resolve_notification_recipient_ids(
        uow,
        _request(
            permission_codes=[],
            user_ids=[uid, other],
            required_permission_codes=[PERM_BRANCH],
        ),
    )
    assert out == [uid]


def test_required_filter_applies_to_broadcast():
    a, b = str(uuid4()), str(uuid4())
    uow = _uow(
        [a, b],
        perms={a: ([PERM_BRANCH], [], []), b: ([], [], [])},
    )
    out = resolve_notification_recipient_ids(
        uow,
        _request(
            permission_codes=[],
            broadcast=True,
            required_permission_codes=[PERM_BRANCH],
        ),
    )
    assert out == [a]
