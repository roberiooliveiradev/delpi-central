from types import SimpleNamespace
from unittest.mock import patch

import pytest

from cipa_app.application.use_cases.member_service import MemberService

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"
MEMBER_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ACTOR = "33333333-3333-3333-3333-333333333333"


def _user(*, permissions: list[str], user_id: str = ACTOR):
    return SimpleNamespace(
        id=user_id,
        sub=user_id,
        name="Gestor",
        permissions=permissions,
        is_superadmin=False,
    )


def _manager():
    return _user(permissions=["cipa.manage", "cipa.unit.filial-01"])


def _viewer():
    return _user(permissions=["cipa.view", "cipa.unit.filial-01"])


def _row(**overrides):
    base = {
        "id": MEMBER_ID,
        "unit_code": "01",
        "user_id": USER_A,
        "display_name": "Ana Presidente",
        "role": "president",
        "mandate_start": "2026-01-01",
        "mandate_end": None,
        "is_active": True,
        "sort_order": 0,
        "created_by_user_id": ACTOR,
        "updated_by_user_id": ACTOR,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "deleted_at": None,
    }
    base.update(overrides)
    return base


def test_list_requires_unit_read():
    svc = MemberService()
    user = _user(permissions=["cipa.view", "cipa.unit.filial-02"])
    with pytest.raises(PermissionError):
        svc.list_members(user, unit_code="01")


def test_list_active_on_date_passes_filter():
    svc = MemberService()
    with patch.object(svc.repo, "list_members", return_value=[_row()]) as listed:
        payload = svc.list_members(
            _viewer(),
            unit_code="01",
            active_on="2026-07-16",
        )
    listed.assert_called_once_with(
        unit_code="01",
        active_on="2026-07-16",
        include_inactive=False,
    )
    assert payload[0]["role"] == "president"


def test_create_requires_manage():
    svc = MemberService()
    with pytest.raises(PermissionError):
        svc.create_member(
            _viewer(),
            {
                "unit_code": "01",
                "user_id": USER_A,
                "display_name": "Ana",
                "role": "president",
                "mandate_start": "2026-01-01",
            },
        )


def test_create_rejects_duplicate_active_user():
    svc = MemberService()
    with patch.object(svc.repo, "find_active_by_user", return_value=_row()):
        with pytest.raises(ValueError, match="membro ativo"):
            svc.create_member(
                _manager(),
                {
                    "unit_code": "01",
                    "user_id": USER_A,
                    "display_name": "Ana",
                    "role": "titular_member",
                    "mandate_start": "2026-01-01",
                },
            )


def test_create_rejects_leadership_conflict():
    svc = MemberService()
    with patch.object(svc.repo, "find_active_by_user", return_value=None):
        with patch.object(
            svc.repo,
            "find_active_leadership",
            return_value=_row(display_name="Outro"),
        ):
            with pytest.raises(ValueError, match="ocupante ativo"):
                svc.create_member(
                    _manager(),
                    {
                        "unit_code": "01",
                        "user_id": USER_B,
                        "display_name": "Bruno",
                        "role": "president",
                        "mandate_start": "2026-01-01",
                    },
                )


def test_create_persists_member():
    svc = MemberService()
    created = _row(role="titular_member", user_id=USER_B, display_name="Bruno")
    with patch.object(svc.repo, "find_active_by_user", return_value=None):
        with patch.object(svc.repo, "find_active_leadership", return_value=None):
            with patch.object(svc.repo, "create_member", return_value=created) as create:
                payload = svc.create_member(
                    _manager(),
                    {
                        "unit_code": "01",
                        "user_id": USER_B,
                        "display_name": " Bruno ",
                        "role": "titular_member",
                        "mandate_start": "2026-01-01",
                        "mandate_end": "2027-12-31",
                    },
                )
    create.assert_called_once()
    kwargs = create.call_args.kwargs
    assert kwargs["display_name"] == "Bruno"
    assert kwargs["mandate_end"] == "2027-12-31"
    assert payload["user_id"] == USER_B


def test_create_rejects_invalid_period():
    svc = MemberService()
    with pytest.raises(ValueError, match="fim do mandato"):
        svc.create_member(
            _manager(),
            {
                "unit_code": "01",
                "user_id": USER_A,
                "display_name": "Ana",
                "role": "titular_member",
                "mandate_start": "2026-06-01",
                "mandate_end": "2026-01-01",
            },
        )


def test_create_rejects_invalid_uuid():
    svc = MemberService()
    with pytest.raises(ValueError, match="user_id"):
        svc.create_member(
            _manager(),
            {
                "unit_code": "01",
                "user_id": "not-a-uuid",
                "display_name": "Ana",
                "role": "titular_member",
                "mandate_start": "2026-01-01",
            },
        )


def test_end_membership_sets_inactive():
    svc = MemberService()
    current = _row()
    ended = _row(is_active=False, mandate_end="2026-07-16")
    with patch.object(svc.repo, "get_member", return_value=current):
        with patch.object(svc.repo, "find_active_by_user", return_value=None):
            with patch.object(svc.repo, "find_active_leadership", return_value=None):
                with patch.object(svc.repo, "update_member", return_value=ended) as update:
                    payload = svc.end_membership(
                        _manager(),
                        MEMBER_ID,
                        mandate_end="2026-07-16",
                    )
    assert payload["is_active"] is False
    assert update.call_args.kwargs["fields"]["is_active"] is False
    assert update.call_args.kwargs["fields"]["mandate_end"] == "2026-07-16"


def test_soft_delete_requires_manage_and_keeps_history_flag():
    svc = MemberService()
    current = _row()
    deleted = _row(is_active=False, deleted_at="2026-07-16T12:00:00+00:00")
    with patch.object(svc.repo, "get_member", return_value=current):
        with patch.object(svc.repo, "soft_delete", return_value=deleted) as soft:
            payload = svc.soft_delete(_manager(), MEMBER_ID)
    soft.assert_called_once_with(member_id=MEMBER_ID, actor_user_id=ACTOR)
    assert payload["deleted_at"] is not None


def test_update_reactivate_checks_leadership_conflict():
    svc = MemberService()
    current = _row(is_active=False, role="secretary")
    with patch.object(svc.repo, "get_member", return_value=current):
        with patch.object(svc.repo, "find_active_by_user", return_value=None):
            with patch.object(
                svc.repo,
                "find_active_leadership",
                return_value=_row(id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            ):
                with pytest.raises(ValueError, match="ocupante ativo"):
                    svc.update_member(
                        _manager(),
                        MEMBER_ID,
                        {"is_active": True},
                    )


def test_list_invalid_active_on():
    svc = MemberService()
    with pytest.raises(ValueError, match="vigência"):
        svc.list_members(_viewer(), unit_code="01", active_on="16/07/2026")
