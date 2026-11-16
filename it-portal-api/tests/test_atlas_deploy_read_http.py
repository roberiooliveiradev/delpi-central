"""HTTP authz for P2.2h.2d read-only ATLAS journal; no Postgres/host."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from it_portal_app.config import settings
from it_portal_app.interface.http.routes.atlas_deploy_read_routes import (
    ATLAS_DEPLOY_VIEW, get_atlas_journal_reader,
)
from it_portal_app.main import app
from tests.conftest import ALL_PERMISSIONS, USER_ID

REQUESTER = "11111111-2222-4333-8444-555555555555"
PROPOSAL = "01234567-89ab-4def-8abc-0123456789ab"


def example():
    return {
        "id": PROPOSAL,
        "requester_subject": REQUESTER,
        "request_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        "environment": "prod",
        "service_id": "public-hub",
        "status": "pending_approval",
        "target_commit_sha": "a"*40,
        "base_commit_sha": "b"*40,
        "manifest_digest": "sha256:"+"c"*64,
        "previous_image_id": "sha256:"+"d"*64,
        "target_image_id": "sha256:"+"e"*64,
        "rollback_image_id": "sha256:"+"d"*64,
        "binding_sha256": "f"*64,
        "created_at": datetime(2026, 11, 16, tzinfo=timezone.utc),
        "expires_at": datetime(2026, 11, 17, tzinfo=timezone.utc),
        "expired": False,
        "approved_by": None,
        "approved_at": None,
        "revision": 1,
        "can_approve": False,
        "can_execute": False,
    }


class FakeReader:
    def __init__(self):
        self.calls: list = []

    def list_proposals(self, **query):
        self.calls.append(("list", query))
        return {"items": [example()], "total": 1,
                "page": query["page"], "page_size": query["page_size"]}

    def get_proposal(self, proposal_id):
        self.calls.append(("detail", proposal_id))
        return {**example(), "events": [{
            "sequence": 1, "event_type": "prepared",
            "actor_subject": REQUESTER,
            "occurred_at": datetime(2026, 11, 16, tzinfo=timezone.utc),
        }]}


@pytest.fixture
def enabled_reader(client, principal, monkeypatch):
    fake = FakeReader()
    app.dependency_overrides[get_atlas_journal_reader] = lambda: fake
    monkeypatch.setattr(settings, "ATLAS_JOURNAL_READ_ENABLED", True)
    principal.permissions = [*ALL_PERMISSIONS, ATLAS_DEPLOY_VIEW]
    yield fake


def test_anonymous_journal_never_reads_repository(monkeypatch, repository):
    fake = FakeReader()
    app.dependency_overrides[get_atlas_journal_reader] = lambda: fake
    monkeypatch.setattr(settings, "ATLAS_JOURNAL_READ_ENABLED", True)
    try:
        with TestClient(app) as anonymous:
            assert anonymous.get("/atlas/deployments").status_code == 401
            assert anonymous.get(f"/atlas/deployments/{PROPOSAL}").status_code == 401
        assert fake.calls == []
    finally:
        app.dependency_overrides.clear()


def test_default_disabled_never_queries_database(client, principal, monkeypatch):
    fake = FakeReader()
    app.dependency_overrides[get_atlas_journal_reader] = lambda: fake
    principal.permissions = [*ALL_PERMISSIONS, ATLAS_DEPLOY_VIEW]
    monkeypatch.setattr(settings, "ATLAS_JOURNAL_READ_ENABLED", False)
    resp = client.get("/atlas/deployments")
    assert resp.status_code == 503
    assert resp.json()["data"]["error"]["code"] == "atlas_journal_disabled"
    assert fake.calls == []


@pytest.mark.parametrize("path", ["/atlas/deployments", f"/atlas/deployments/{PROPOSAL}"])
def test_plain_portal_access_is_not_journal_grant(client, principal, monkeypatch, path):
    monkeypatch.setattr(settings, "ATLAS_JOURNAL_READ_ENABLED", True)
    principal.permissions = ALL_PERMISSIONS
    assert client.get(path).status_code == 403


def test_list_and_detail_are_get_only_and_force_fresh_core(client, principal, enabled_reader):
    before = principal.fresh_lookups
    resp = client.get("/atlas/deployments?environment=prod&page=2&page_size=10")
    assert resp.status_code == 200, resp.text
    item = resp.json()["data"]["items"][0]
    assert item["manifest_digest"] == example()["manifest_digest"]
    assert item["binding_sha256"] == example()["binding_sha256"]
    assert item["can_approve"] is False and item["can_execute"] is False
    assert not any("challenge" in key or "statement_sha256" in key for key in item)
    assert enabled_reader.calls == [("list", {
        "environment": "prod", "status": None, "page": 2, "page_size": 10,
    })]
    detail = client.get(f"/atlas/deployments/{PROPOSAL}")
    assert detail.status_code == 200
    assert detail.json()["data"]["events"][0]["event_type"] == "prepared"
    assert principal.fresh_lookups == before + 2
    assert client.post("/atlas/deployments", json={}).status_code == 405


def test_revocation_from_fresh_core_fails_without_db(client, principal, enabled_reader):
    principal.fresh_permissions = ["it-portal.access"]
    assert client.get("/atlas/deployments").status_code == 403
    assert enabled_reader.calls == []


def test_core_unavailable_fails_closed_without_db(client, principal, enabled_reader):
    principal.fresh_unavailable = True
    assert client.get("/atlas/deployments").status_code == 503
    assert enabled_reader.calls == []


def test_cached_access_cannot_replace_specific_grant(client, principal, enabled_reader):
    principal.permissions = ["it-portal.access"]
    principal.fresh_permissions = [*ALL_PERMISSIONS, ATLAS_DEPLOY_VIEW]
    assert client.get("/atlas/deployments").status_code == 403
    assert enabled_reader.calls == []


def test_invalid_query_is_rejected_without_data_access(client, enabled_reader):
    for path in (
        "/atlas/deployments?environment=other",
        "/atlas/deployments?status=unknown",
        "/atlas/deployments?page_size=1000",
        "/atlas/deployments?page=0",
        "/atlas/deployments/not-a-uuid",
    ):
        assert client.get(path).status_code == 422, path
    assert enabled_reader.calls == []


def test_service_tokens_are_rejected(client, enabled_reader, monkeypatch):
    import delpi_auth.middleware.fastapi_auth as fastapi_auth
    monkeypatch.setattr(
        fastapi_auth, "request_has_valid_internal_service_token",
        lambda _request: True,
    )
    assert client.get("/atlas/deployments").status_code == 403
    assert enabled_reader.calls == []


def test_fresh_core_identity_mismatch_cannot_be_accepted(client, principal, enabled_reader, monkeypatch):
    import delpi_auth.middleware.fastapi_auth as fastapi_auth

    async def mismatched(_token, *, force_refresh=False):
        return {
            "id": REQUESTER if force_refresh else USER_ID,
            "name": "Different", "permissions": [*ALL_PERMISSIONS, ATLAS_DEPLOY_VIEW],
            "is_superadmin": False,
        }

    monkeypatch.setattr(fastapi_auth, "load_user_rbac", mismatched)
    assert client.get("/atlas/deployments").status_code == 403
    assert enabled_reader.calls == []


def test_routes_present_in_openapi_but_no_write_operation(client, enabled_reader):
    paths = client.get("/openapi.json").json()["paths"]
    assert list(paths["/atlas/deployments"].keys()) == ["get"]
    assert list(paths["/atlas/deployments/{proposal_id}"].keys()) == ["get"]
