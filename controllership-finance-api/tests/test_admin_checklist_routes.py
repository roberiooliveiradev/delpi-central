"""P6-MIN admin API — authorization + domain error mapping tests.

Chain under test: middleware → human principal → ``manage`` efetivo
(escopo administrativo do slice) → repository → typed domain errors.
``access`` alone never authorizes administrative mutations.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.domain.closing_checklist import errors as de
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
MANAGE = "controllership-finance.manage"
TOKEN = "viewer-test-token"
TEMPLATE_ID = "11111111-1111-4111-8111-111111111111"


def _claims(**overrides) -> dict:
    claims = {
        "sub": "33333333-3333-4333-8333-333333333333",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "given_name": "Ana",
    }
    claims.update(overrides)
    return claims


def _rbac(**overrides) -> dict:
    rbac = {
        "id": "33333333-3333-4333-8333-333333333333",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "roles": [],
        "groups": [],
        "permissions": [MANAGE],
        "is_superadmin": False,
    }
    rbac.update(overrides)
    return rbac


async def _load_rbac_result(rbac: dict):
    return rbac


@pytest.fixture(autouse=True)
def _auth_pipeline(monkeypatch):
    rbac_holder = {"rbac": _rbac()}
    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: False
    )
    monkeypatch.setattr(fa, "validate_token", lambda token: _claims())
    monkeypatch.setattr(
        fa,
        "load_user_rbac",
        lambda token, *, force_refresh=False: _load_rbac_result(
            rbac_holder["rbac"]
        ),
    )
    yield rbac_holder


@pytest.fixture
def repo(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "admin_checklist_routes._repository",
        lambda: fake,
    )
    return fake


def _client() -> TestClient:
    return TestClient(app)


def _headers(token: str = TOKEN) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- authorization ----------------------------------------------------------


def test_requires_bearer(repo):
    assert (
        _client().get(f"/admin/checklist-templates").status_code == 401
    )
    repo.list_templates.assert_not_called()


def test_access_only_is_forbidden(_auth_pipeline, repo):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS])
    response = _client().get(
        "/admin/checklist-templates", headers=_headers()
    )
    assert response.status_code == 403
    repo.list_templates.assert_not_called()


def test_access_only_cannot_publish(_auth_pipeline, repo):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS])
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/1/publish",
        headers=_headers(),
        json={"effective_from_period": "2026-11"},
    )
    assert response.status_code == 403
    repo.publish_version.assert_not_called()


def test_service_principal_denied(monkeypatch, repo):
    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: True
    )
    response = _client().get(
        "/admin/checklist-templates", headers=_headers()
    )
    assert response.status_code == 403
    repo.list_templates.assert_not_called()


def test_rbac_unavailable_fails_closed(_auth_pipeline, repo):
    _auth_pipeline["rbac"] = _rbac(rbac_unavailable=True)
    response = _client().get(
        "/admin/checklist-templates", headers=_headers()
    )
    assert response.status_code == 503
    repo.list_templates.assert_not_called()


# --- happy paths ------------------------------------------------------------


def test_list_templates(_auth_pipeline, repo):
    repo.list_templates.return_value = [
        {"code": "monthly-closing-checklist", "name": "Checklist"}
    ]
    response = _client().get(
        "/admin/checklist-templates", headers=_headers()
    )
    assert response.status_code == 200
    assert response.json()["data"]["templates"][0]["code"] == (
        "monthly-closing-checklist"
    )


def test_create_draft(_auth_pipeline, repo):
    repo.create_draft_version.return_value = {
        "version_id": "v",
        "version": 2,
        "status": "DRAFT",
        "revision": 1,
    }
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions",
        headers=_headers(),
    )
    assert response.status_code == 201
    repo.create_draft_version.assert_called_once()


def test_update_draft(_auth_pipeline, repo):
    repo.update_draft_items.return_value = {"version_id": "v", "revision": 2}
    response = _client().put(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/2",
        headers=_headers(),
        json={
            "revision": 1,
            "items": [
                {
                    "item_key": "CK-E-01",
                    "sheet": "ELETRONICO",
                    "name": "Extratos",
                    "origin_kind": "EXTERNAL",
                }
            ],
        },
    )
    assert response.status_code == 200
    kwargs = repo.update_draft_items.call_args
    assert kwargs.kwargs["expected_revision"] == 1


def test_publish(_auth_pipeline, repo):
    repo.publish_version.return_value = {
        "version_id": "v",
        "status": "PUBLISHED",
    }
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/1/publish",
        headers=_headers(),
        json={"effective_from_period": "2026-10"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PUBLISHED"


def test_inactivate(_auth_pipeline, repo):
    repo.inactivate_version.return_value = {
        "version_id": "v",
        "status": "INACTIVE",
    }
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/1/inactivate",
        headers=_headers(),
    )
    assert response.status_code == 200


# --- typed domain errors ----------------------------------------------------


@pytest.mark.parametrize(
    "exc, status, code",
    [
        (de.TemplateNotFound("x"), 404, "template_not_found"),
        (de.DraftAlreadyOpen("x"), 409, "draft_already_open"),
        (de.DuplicateItemKey("x"), 409, "duplicate_item_key"),
        (de.VersionNotDraft("x"), 409, "version_not_draft"),
        (de.StaleRevision("x"), 409, "stale_revision"),
        (de.PersistenceUnavailable("x"), 503, "persistence_unavailable"),
    ],
)
def test_domain_errors_mapped(_auth_pipeline, repo, exc, status, code):
    repo.list_versions.side_effect = exc
    response = _client().get(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions",
        headers=_headers(),
    )
    assert response.status_code == status
    body = response.json()
    assert body["success"] is False
    assert body["data"]["error"]["code"] == code


def test_publish_empty_items_rejected(_auth_pipeline, repo):
    repo.publish_version.side_effect = de.VersionNotDraft("sem itens")
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/1/publish",
        headers=_headers(),
        json={"effective_from_period": "2026-10"},
    )
    assert response.status_code == 409


def test_publish_invalid_period_422(_auth_pipeline, repo):
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/1/publish",
        headers=_headers(),
        json={"effective_from_period": "2026-13"},
    )
    assert response.status_code == 422
    repo.publish_version.assert_not_called()


# --- actor identity (R2) ----------------------------------------------------


def test_publish_rejects_non_uuid_actor(_auth_pipeline, repo):
    _auth_pipeline["rbac"] = _rbac(id="user-1")
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/1/publish",
        headers=_headers(),
        json={"effective_from_period": "2026-10"},
    )
    assert response.status_code == 401
    repo.publish_version.assert_not_called()


def test_publish_rejects_missing_actor_id(
    _auth_pipeline, repo, monkeypatch
):
    """Sem `sub` no token e sem `id` no RBAC: fail-closed no middleware
    (401) antes da rota — nenhum ator inventado alcança o repositório."""
    _auth_pipeline["rbac"] = _rbac(id=None)
    monkeypatch.setattr(
        fa, "validate_token", lambda token: _claims(sub=None)
    )
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions/1/publish",
        headers=_headers(),
        json={"effective_from_period": "2026-10"},
    )
    assert response.status_code == 401
    repo.publish_version.assert_not_called()


def test_valid_uuid_actor_reaches_repository(_auth_pipeline, repo):
    repo.create_draft_version.return_value = {
        "version_id": "v",
        "version": 2,
        "status": "DRAFT",
        "revision": 1,
    }
    response = _client().post(
        f"/admin/checklist-templates/{TEMPLATE_ID}/versions",
        headers=_headers(),
    )
    assert response.status_code == 201
    assert repo.create_draft_version.call_args.kwargs["actor"] == (
        "33333333-3333-4333-8333-333333333333"
    )


def test_list_template_events(_auth_pipeline, repo):
    repo.list_template_events.return_value = [
        {
            "event_id": "e-1",
            "event_type": "VERSION_PUBLISHED",
            "actor_subject": "u-1",
            "detail": {"version": 2},
            "created_at": "2026-05-02T10:00:00Z",
            "version": 2,
        }
    ]
    response = _client().get(
        f"/admin/checklist-templates/{TEMPLATE_ID}/events",
        headers=_headers(),
    )
    assert response.status_code == 200
    assert (
        response.json()["data"]["events"][0]["event_type"]
        == "VERSION_PUBLISHED"
    )
    repo.list_template_events.assert_called_once_with(TEMPLATE_ID, None)


def test_list_template_events_version_filter(_auth_pipeline, repo):
    repo.list_template_events.return_value = []
    response = _client().get(
        f"/admin/checklist-templates/{TEMPLATE_ID}/events?version=3",
        headers=_headers(),
    )
    assert response.status_code == 200
    repo.list_template_events.assert_called_once_with(TEMPLATE_ID, 3)


def test_list_template_events_access_only_forbidden(
    _auth_pipeline, repo
):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS])
    response = _client().get(
        f"/admin/checklist-templates/{TEMPLATE_ID}/events",
        headers=_headers(),
    )
    assert response.status_code == 403
    repo.list_template_events.assert_not_called()
