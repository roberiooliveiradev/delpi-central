"""Fatia 1: access/manage e ausência de autorização por filial."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from starlette.requests import Request

from tm_app.application.security.authorization_policy import (
    AuthorizationDenied,
    TransformometroAuthorizationPolicy,
)
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
)
from tm_app.application.services.meeting_minutes_service import MeetingMinutesService
from tm_app.interface.http.branch_access_http import (
    check_dashboard_filial_access,
    check_processo_view_access,
    filter_rows_for_access,
    require_transformometro_view_access,
)


def _user(**kwargs):
    return SimpleNamespace(
        id=kwargs.get("id", "u1"),
        email="u@test",
        name="U",
        permissions=kwargs.get("permissions", []),
        is_superadmin=kwargs.get("is_superadmin", False),
    )


def _request(user) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/transformometro/processos",
        "raw_path": b"/transformometro/processos",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 0),
        "server": ("test", 443),
    }
    request = Request(scope)
    request.state.user = user
    return request


def test_no_access_is_denied_and_access_is_allowed():
    policy = TransformometroAuthorizationPolicy()
    with pytest.raises(AuthorizationDenied) as missing:
        policy.require_access(None)
    assert missing.value.status_code == 401
    with pytest.raises(AuthorizationDenied):
        policy.require_access(_user(permissions=[]))
    policy.require_access(_user(permissions=[ACCESS_PERMISSION]))
    with pytest.raises(AuthorizationDenied):
        policy.require_access(_user(permissions=["transformometro.view"]))


def test_removed_codes_do_not_grant_access():
    policy = TransformometroAuthorizationPolicy()
    for code in (
        "transformometro.view",
        "transformometro.view.consolidated",
        "transformometro.branch.filial-01",
        "transformometro.view.filial-01",
        "transformometro.manage.filial-02",
        "transformometro.data.transfer",
        "transformometro.processes.manage",
        "transformometro.meeting-minutes.sign",
        "transformometro.atas.manage",
    ):
        assert policy.has_access(_user(permissions=[code])) is False
        assert policy.has_manage(_user(permissions=[code])) is False


def test_manage_does_not_imply_access():
    policy = TransformometroAuthorizationPolicy()
    admin = _user(permissions=[MANAGE_PERMISSION])
    assert policy.has_manage(admin) is True
    assert policy.has_access(admin) is False
    with pytest.raises(AuthorizationDenied):
        policy.require_access(admin)
    policy.require_manage(admin)


def test_access_sees_both_filiais_and_dashboard_filters():
    user = _user(permissions=[ACCESS_PERMISSION])
    request = _request(user)
    rows = [
        {"id": "p1", "codigo_filial": "01"},
        {"id": "p2", "codigo_filial": "02"},
    ]
    visible = filter_rows_for_access(request, rows, codigo_key="codigo_filial")
    assert [row["id"] for row in visible] == ["p1", "p2"]
    assert check_processo_view_access(request, "p1") is None
    assert check_processo_view_access(request, "p2") is None
    assert check_dashboard_filial_access(
        request, view="consolidated", filial_id=None, setor_id=None
    ) is None
    assert check_dashboard_filial_access(
        request, view="filial", filial_id="01", setor_id=None
    ) is None
    assert check_dashboard_filial_access(
        request, view="filial", filial_id="02", setor_id=None
    ) is None


def test_access_uses_the_product_and_does_not_administer():
    policy = TransformometroAuthorizationPolicy()
    user = _user(permissions=[ACCESS_PERMISSION])
    request = _request(user)
    policy.require_access(user)
    assert require_transformometro_view_access(request) is None
    with pytest.raises(AuthorizationDenied):
        policy.require_manage(user)

    admin = _request(_user(permissions=[MANAGE_PERMISSION]))
    assert require_transformometro_view_access(admin) is not None


def test_legacy_codes_do_not_open_the_portal():
    view = _request(_user(permissions=["transformometro.view"]))
    assert require_transformometro_view_access(view) is not None
    assert require_transformometro_view_access(
        _request(_user(permissions=["transformometro.branch.filial-01"]))
    ) is not None


class _MinuteRepo:
    def __init__(self, *, status: str, signer_id: str | None):
        self.minute = {
            "id": "m1",
            "status": status,
            "current_version_id": "v1",
            "unit_code": "02",
            "title": "Ata",
            "meeting_type": "ordinary",
            "meeting_date": "2026-09-18",
        }
        self.version = {"id": "v1", "content_hash": "abc", "title": "Ata"}
        self.signers = []
        if signer_id:
            self.signers = [
                {"id": "s1", "user_id": signer_id, "status": "pending", "display_name": "Ana"}
            ]

    def get_minute(self, _):
        return self.minute

    def get_version(self, _, version_id=None):
        return self.version

    def list_signers(self, _):
        return self.signers

    def list_signatures(self, _):
        return []

    def list_participants(self, _):
        return []

    def list_versions(self, _):
        return [self.version]

    def get_signer_for_user(self, _, user_id):
        return next((s for s in self.signers if s["user_id"] == user_id), None)


def test_access_reads_minute_of_any_unit_and_sign_follows_domain():
    reader = _user(id="reader", permissions=[ACCESS_PERMISSION])
    service = MeetingMinutesService(_MinuteRepo(status="awaiting_signatures", signer_id="signer"))
    loaded = service._load(reader, "view", "m1")
    assert loaded["unit_code"] == "02"

    signer = _user(id="signer", permissions=[ACCESS_PERMISSION])
    signing = MeetingMinutesService(_MinuteRepo(status="awaiting_signatures", signer_id="signer"))
    signing.signature_storage = SimpleNamespace(save_png=lambda **_: "sig.png")
    signing.repo.register_signature = lambda **_: {
        "signature": {"id": "sig"},
        "signed_count": 1,
        "required_count": 1,
    }
    signing.repo.invalidate_open_invites = lambda **_: None
    signing.repo.set_status = lambda **_: signing.repo.minute
    signed = signing.sign(
        signer,
        "m1",
        png_bytes=b"png",
        display_name_confirmed="Ana",
        terms_accepted=True,
        client_ip=None,
        user_agent=None,
        session_id=None,
        idempotency_key=None,
    )
    assert signed["signature"]["id"] == "sig"

    outsider = MeetingMinutesService(_MinuteRepo(status="awaiting_signatures", signer_id="other"))
    with pytest.raises(PermissionError, match="signatário"):
        outsider.sign(
            reader,
            "m1",
            png_bytes=b"png",
            display_name_confirmed="Ana",
            terms_accepted=True,
            client_ip=None,
            user_agent=None,
            session_id=None,
            idempotency_key=None,
        )

    draft = MeetingMinutesService(_MinuteRepo(status="draft", signer_id="signer"))
    with pytest.raises(ValueError, match="aguardando"):
        draft.sign(
            signer,
            "m1",
            png_bytes=b"png",
            display_name_confirmed="Ana",
            terms_accepted=True,
            client_ip=None,
            user_agent=None,
            session_id=None,
            idempotency_key=None,
        )
