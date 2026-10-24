"""P2-Upload SLICE-1 — contratos HTTP U1–U4 (doc 103 + AC-P2-UP-*).

`access` efetivo autoriza upload/list/get/download; service principal e
Core indisponível falham fechado; cross-competence/item é 404; replay
idempotente retorna o original (deduplicated); payload divergente ⇒
`idempotency_conflict` 409; download emite `DOCUMENT_DOWNLOADED` apenas
após authz + integridade (result=AUTHORIZED, D-U3=A).
"""

from __future__ import annotations

import io
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.domain.closing_checklist import errors as de
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
TOKEN = "viewer-test-token"
NOW = datetime(2026, 4, 10, 12, 0, 0, tzinfo=timezone.utc)


def _claims(**overrides) -> dict:
    claims = {
        "sub": "33333333-3333-4333-8333-333333333333",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
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
        "permissions": [ACCESS],
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
def service(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "documents_routes._service",
        lambda: fake,
    )
    return fake


def _client() -> TestClient:
    return TestClient(app)


def _doc(**overrides) -> dict:
    row = {
        "document_id": uuid.uuid4(),
        "competence_id": uuid.uuid4(),
        "snapshot_item_id": None,
        "snapshot_item_key": None,
        "branch_scope": "BOTH",
        "link_kind": "competence",
        "title": "Extrato maio",
        "attachment_role": "generic",
        "state": "ATTACHED",
        "current_version_no": 1,
        "revision": 1,
        "uploaded_by": uuid.uuid4(),
        "created_at": NOW,
        "updated_at": NOW,
        "original_name": "extrato.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 2048,
        "checksum_sha256": "ab" * 32,
    }
    row.update(overrides)
    return row


def _pdf() -> bytes:
    return b"%PDF-1.4\n" + b"x" * 2048 + b"\n%%EOF\n"


def _upload(client: TestClient, **kwargs):
    return client.post(
        "/closing/competences/2026-05/documents",
        files={"file": (kwargs.pop("name", "extrato.pdf"), _pdf(), "application/pdf")},
        data={"idempotency_key": "key-1", **kwargs.pop("data", {})},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )


# -- U1 ---------------------------------------------------------------------


def test_upload_created_returns_201(service):
    service.upload.return_value = (_doc(), True)
    response = _upload(_client())
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["state"] == "ATTACHED"
    assert body["attachment_role"] == "generic"
    assert body["link_kind"] == "competence"
    assert "storage_key" not in body and "stored_name" not in body


def test_upload_replay_returns_200_deduplicated(service):
    service.upload.return_value = (_doc(), False)
    response = _upload(_client())
    assert response.status_code == 200
    assert response.json()["data"]["deduplicated"] is True


def test_upload_requires_idempotency_key(service):
    response = _client().post(
        "/closing/competences/2026-05/documents",
        files={"file": ("a.pdf", _pdf(), "application/pdf")},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 422
    service.upload.assert_not_called()


def test_upload_to_competence_item(service):
    item_id = str(uuid.uuid4())
    service.upload.return_value = (
        _doc(link_kind="competence_item", snapshot_item_id=item_id),
        True,
    )
    response = _upload(_client(), data={"snapshot_item_id": item_id})
    assert response.status_code == 201
    assert service.upload.call_args.kwargs["snapshot_item_id"] == item_id


def test_upload_invalid_snapshot_item_uuid(service):
    response = _upload(_client(), data={"snapshot_item_id": "não-uuid"})
    assert response.status_code == 422
    assert response.json()["data"]["error"]["code"] == "invalid_upload"


def test_upload_forwards_declared_branch_scope(service):
    service.upload.return_value = (_doc(), True)
    response = _upload(_client(), data={"branch_scope": "MATRIX"})
    assert response.status_code == 201
    assert service.upload.call_args.kwargs["branch_scope"] == "MATRIX"


def test_upload_rejects_invalid_branch_scope(service):
    response = _upload(_client(), data={"branch_scope": "filial-01"})
    assert response.status_code == 422
    service.upload.assert_not_called()


def test_upload_typed_errors(service):
    cases = [
        (de.FileTooLarge("grande"), 422, "file_too_large"),
        (de.UnsupportedMediaType("tipo"), 415, "unsupported_media_type"),
        (de.InvalidFileContent("corrompido"), 422, "invalid_file_content"),
        (de.EmptyFile("vazio"), 422, "empty_file"),
        (de.ContentTypeMismatch("diverge"), 422, "content_type_mismatch"),
        (de.IdempotencyConflict("conflito"), 409, "idempotency_conflict"),
        (de.CompetenceNotOpened("fechada"), 404, "competence_not_opened"),
        (de.ItemNotFound("item"), 404, "item_not_found"),
        (de.InvalidUpload("role"), 422, "invalid_upload"),
        (de.PersistenceUnavailable("down"), 503, "persistence_unavailable"),
    ]
    for exc, status, code in cases:
        service.upload.side_effect = exc
        response = _upload(_client())
        assert response.status_code == status, code
        assert response.json()["data"]["error"]["code"] == code


# -- U2 ---------------------------------------------------------------------


def test_list_documents(service):
    service.list_documents.return_value = {
        "items": [_doc(), _doc()],
        "total": 2,
        "limit": 50,
        "offset": 0,
    }
    response = _client().get(
        "/closing/competences/2026-05/documents",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2 and len(data["documents"]) == 2


def test_list_documents_filters_forwarded(service):
    item_id = str(uuid.uuid4())
    service.list_documents.return_value = {
        "items": [],
        "total": 0,
        "limit": 10,
        "offset": 5,
    }
    response = _client().get(
        f"/closing/competences/2026-05/documents?snapshot_item_id={item_id}"
        "&link_kind=competence_item&state=ATTACHED&limit=10&offset=5",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    call = service.list_documents.call_args.kwargs
    assert call["snapshot_item_id"] == item_id
    assert call["link_kind"] == "competence_item"
    assert call["state"] == "ATTACHED"
    assert call["branch_scope"] is None
    assert call["limit"] == 10 and call["offset"] == 5


def test_list_documents_forwards_branch_scope(service):
    service.list_documents.return_value = {
        "items": [_doc(branch_scope="MATRIX")],
        "total": 1,
        "limit": 50,
        "offset": 0,
    }
    response = _client().get(
        "/closing/competences/2026-05/documents?branch_scope=MATRIX",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    assert (
        service.list_documents.call_args.kwargs["branch_scope"] == "MATRIX"
    )
    assert response.json()["data"]["documents"][0]["branch_scope"] == "MATRIX"


def test_list_documents_empty(service):
    service.list_documents.return_value = {
        "items": [],
        "total": 0,
        "limit": 50,
        "offset": 0,
    }
    response = _client().get(
        "/closing/competences/2026-05/documents",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["documents"] == []


# -- U3 ---------------------------------------------------------------------


def test_get_document(service):
    doc_id = str(uuid.uuid4())
    service.get_document.return_value = _doc(document_id=doc_id)
    response = _client().get(
        f"/closing/competences/2026-05/documents/{doc_id}",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["document_id"] == doc_id
    assert body["checksum_sha256"] == "ab" * 32


def test_get_document_cross_competence_is_404(service):
    service.get_document.side_effect = de.DocumentNotFound("não")
    response = _client().get(
        f"/closing/competences/2026-05/documents/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 404
    assert response.json()["data"]["error"]["code"] == "document_not_found"


def test_get_document_outside_declared_scope_is_404(service):
    # Usuário em contexto Filial consulta documento de item MATRIX —
    # o backend responde 404 sem vazar existência (resource scope).
    service.get_document.side_effect = de.DocumentNotFound("não")
    doc_id = str(uuid.uuid4())
    response = _client().get(
        f"/closing/competences/2026-05/documents/{doc_id}"
        "?branch_scope=BRANCH",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 404
    assert (
        service.get_document.call_args.kwargs["branch_scope"] == "BRANCH"
    )


# -- U4 ---------------------------------------------------------------------


def test_download_streams_file_and_audits(service, tmp_path):
    target = tmp_path / "extrato.pdf"
    target.write_bytes(_pdf())
    service.resolve_download.return_value = (
        target,
        {"mime_type": "application/pdf", "original_name": "extrato.pdf"},
    )
    doc_id = str(uuid.uuid4())
    response = _client().get(
        f"/closing/competences/2026-05/documents/{doc_id}/versions/1/content",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    assert response.content == _pdf()
    assert response.headers["content-type"].startswith("application/pdf")


def test_download_missing_file_is_503_never_false_success(service):
    service.resolve_download.side_effect = de.FileMissing("sumiu")
    response = _client().get(
        f"/closing/competences/2026-05/documents/{uuid.uuid4()}/versions/1/content",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 503
    assert response.json()["data"]["error"]["code"] == "file_missing"


def test_download_cross_competence_is_404(service):
    service.resolve_download.side_effect = de.DocumentNotFound("não")
    response = _client().get(
        f"/closing/competences/2026-05/documents/{uuid.uuid4()}/versions/1/content",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 404


def test_download_outside_declared_scope_is_404(service):
    service.resolve_download.side_effect = de.DocumentNotFound("não")
    doc_id = str(uuid.uuid4())
    response = _client().get(
        f"/closing/competences/2026-05/documents/{doc_id}"
        "/versions/1/content?branch_scope=BRANCH",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 404
    assert (
        service.resolve_download.call_args.kwargs["branch_scope"]
        == "BRANCH"
    )


def test_download_rejects_invalid_branch_scope(service):
    doc_id = str(uuid.uuid4())
    response = _client().get(
        f"/closing/competences/2026-05/documents/{doc_id}"
        "/versions/1/content?branch_scope=ruim",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 422
    service.resolve_download.assert_not_called()


# -- segurança transversal -----------------------------------------------------


def test_service_principal_forbidden(_auth_pipeline, service, monkeypatch):
    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: True
    )
    response = _client().get(
        "/closing/competences/2026-05/documents",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 403
    service.list_documents.assert_not_called()


def test_no_access_permission_forbidden(_auth_pipeline, service):
    _auth_pipeline["rbac"] = _rbac(permissions=["controllership-finance.manage"])
    response = _upload(_client())
    assert response.status_code == 403
    service.upload.assert_not_called()


def test_rbac_unavailable_is_503(_auth_pipeline, service):
    _auth_pipeline["rbac"] = _rbac(rbac_unavailable=True)
    response = _client().get(
        "/closing/competences/2026-05/documents",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 503
    service.list_documents.assert_not_called()


def test_malformed_actor_unauthorized(_auth_pipeline, service):
    _auth_pipeline["rbac"] = _rbac(id="não-uuid")
    response = _upload(_client())
    assert response.status_code == 401
    service.upload.assert_not_called()


# -- U5: substituição (SLICE-2) -------------------------------------------------

MANAGE = "controllership-finance.manage"


def _replace(client: TestClient, doc_id: str, **kwargs):
    return client.post(
        f"/closing/competences/2026-05/documents/{doc_id}/versions",
        files={"file": (kwargs.pop("name", "novo.pdf"), _pdf(), "application/pdf")},
        data={
            "revision": "3",
            "idempotency_key": "replace-key-1",
            **kwargs.pop("data", {}),
        },
        headers={"Authorization": f"Bearer {TOKEN}"},
    )


def test_replace_returns_201_with_updated_document(service):
    doc_id = str(uuid.uuid4())
    service.replace_document.return_value = (
        _doc(document_id=doc_id, current_version_no=2, revision=4),
        True,
    )
    response = _replace(_client(), doc_id)
    assert response.status_code == 201
    call = service.replace_document.call_args.kwargs
    assert call["document_id"] == doc_id
    assert call["expected_revision"] == 3
    assert call["idempotency_key"] == "replace-key-1"
    assert call["can_manage"] is False
    assert call["actor"] == "33333333-3333-4333-8333-333333333333"


def test_replace_deduplicated_returns_200(service):
    # Replay idêntico (key + mesmo payload) ⇒ deduplicated, sem 201.
    doc_id = str(uuid.uuid4())
    service.replace_document.return_value = (_doc(document_id=doc_id), False)
    response = _replace(_client(), doc_id)
    assert response.status_code == 200
    assert response.json()["data"]["deduplicated"] is True


def test_replace_manage_user_gets_can_manage(_auth_pipeline, service):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS, MANAGE])
    service.replace_document.return_value = (_doc(), True)
    response = _replace(_client(), str(uuid.uuid4()))
    assert response.status_code == 201
    assert service.replace_document.call_args.kwargs["can_manage"] is True


def test_replace_forwards_branch_scope(service):
    service.replace_document.return_value = (_doc(), True)
    response = _replace(_client(), str(uuid.uuid4()), data={"branch_scope": "MATRIX"})
    assert response.status_code == 201
    assert (
        service.replace_document.call_args.kwargs["branch_scope"] == "MATRIX"
    )


def test_replace_requires_revision(service):
    response = _client().post(
        f"/closing/competences/2026-05/documents/{uuid.uuid4()}/versions",
        files={"file": ("novo.pdf", _pdf(), "application/pdf")},
        data={"idempotency_key": "replace-key-1"},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 422
    service.replace_document.assert_not_called()


def test_replace_requires_idempotency_key(service):
    # D-U7=A na mutação: sem key o request é inválido — nunca chega ao
    # service (replay cego não pode criar versão).
    response = _client().post(
        f"/closing/competences/2026-05/documents/{uuid.uuid4()}/versions",
        files={"file": ("novo.pdf", _pdf(), "application/pdf")},
        data={"revision": "3"},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 422
    service.replace_document.assert_not_called()


def test_replace_typed_errors(service):
    cases = [
        (de.Forbidden("não"), 403, "forbidden"),
        (de.DocumentNotFound("não"), 404, "document_not_found"),
        (de.DocumentCancelled("cancelado"), 409, "document_cancelled"),
        (de.StaleRevision("velha"), 409, "stale_revision"),
        (de.IdempotencyConflict("conflito"), 409, "idempotency_conflict"),
        (de.UnsupportedMediaType("tipo"), 415, "unsupported_media_type"),
        (de.InvalidFileContent("corrompido"), 422, "invalid_file_content"),
        (de.PersistenceUnavailable("down"), 503, "persistence_unavailable"),
    ]
    for exc, status, code in cases:
        service.replace_document.side_effect = exc
        response = _replace(_client(), str(uuid.uuid4()))
        assert response.status_code == status, code
        assert response.json()["data"]["error"]["code"] == code


def test_replace_without_access_is_403(_auth_pipeline, service):
    # `manage` sozinho nunca substitui — access é pré-condição (D-U1=A).
    _auth_pipeline["rbac"] = _rbac(permissions=[MANAGE])
    response = _replace(_client(), str(uuid.uuid4()))
    assert response.status_code == 403
    service.replace_document.assert_not_called()


# -- U6: histórico de versões (SLICE-2) -----------------------------------------


def _version(**overrides):
    row = {
        "document_version_id": uuid.uuid4(),
        "document_id": uuid.uuid4(),
        "version_no": 1,
        "state": "SUPERSEDED",
        "uploaded_by": uuid.uuid4(),
        "created_at": NOW,
        "original_name": "extrato.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 2048,
        "checksum_sha256": "cd" * 32,
    }
    row.update(overrides)
    return row


def test_list_versions_returns_history(service):
    doc_id = str(uuid.uuid4())
    service.list_document_versions.return_value = [
        _version(version_no=2, state="ATTACHED"),
        _version(version_no=1),
    ]
    response = _client().get(
        f"/closing/competences/2026-05/documents/{doc_id}/versions",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    versions = response.json()["data"]["versions"]
    assert [v["version_no"] for v in versions] == [2, 1]
    assert versions[0]["state"] == "ATTACHED"
    assert "storage_key" not in versions[0]


def test_list_versions_forwards_branch_scope(service):
    service.list_document_versions.return_value = []
    response = _client().get(
        f"/closing/competences/2026-05/documents/{uuid.uuid4()}"
        "/versions?branch_scope=BRANCH",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    assert (
        service.list_document_versions.call_args.kwargs["branch_scope"]
        == "BRANCH"
    )


def test_list_versions_outside_scope_is_404(service):
    service.list_document_versions.side_effect = de.DocumentNotFound("não")
    response = _client().get(
        f"/closing/competences/2026-05/documents/{uuid.uuid4()}/versions",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 404
    assert response.json()["data"]["error"]["code"] == "document_not_found"


# -- U7: cancelamento (SLICE-2) --------------------------------------------------


def test_cancel_returns_cancelled_document(service):
    doc_id = str(uuid.uuid4())
    service.cancel_document.return_value = _doc(
        document_id=doc_id, state="CANCELLED", revision=4
    )
    response = _client().post(
        f"/closing/competences/2026-05/documents/{doc_id}/cancel",
        json={"revision": 3},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["state"] == "CANCELLED"
    call = service.cancel_document.call_args.kwargs
    assert call["expected_revision"] == 3
    assert call["document_id"] == doc_id


def test_cancel_manage_user_gets_can_manage(_auth_pipeline, service):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS, MANAGE])
    service.cancel_document.return_value = _doc(state="CANCELLED")
    response = _client().post(
        f"/closing/competences/2026-05/documents/{uuid.uuid4()}/cancel",
        json={"revision": 1},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    assert service.cancel_document.call_args.kwargs["can_manage"] is True


def test_cancel_typed_errors(service):
    cases = [
        (de.Forbidden("não"), 403, "forbidden"),
        (de.DocumentNotFound("não"), 404, "document_not_found"),
        (de.DocumentCancelled("já"), 409, "document_cancelled"),
        (de.StaleRevision("velha"), 409, "stale_revision"),
        (de.PersistenceUnavailable("down"), 503, "persistence_unavailable"),
    ]
    for exc, status, code in cases:
        service.cancel_document.side_effect = exc
        response = _client().post(
            f"/closing/competences/2026-05/documents/{uuid.uuid4()}/cancel",
            json={"revision": 1},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert response.status_code == status, code
        assert response.json()["data"]["error"]["code"] == code


def test_cancel_requires_revision(service):
    response = _client().post(
        f"/closing/competences/2026-05/documents/{uuid.uuid4()}/cancel",
        json={},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 422
    service.cancel_document.assert_not_called()


# -- U8: eventos de auditoria (SLICE-2) ------------------------------------------


def _event(**overrides):
    row = {
        "event_id": uuid.uuid4(),
        "event_type": "DOCUMENT_UPLOADED",
        "actor_subject": uuid.uuid4(),
        "detail": {"original_name": "extrato.pdf"},
        "created_at": NOW,
    }
    row.update(overrides)
    return row


def test_list_events_returns_events(service):
    doc_id = str(uuid.uuid4())
    service.list_document_events.return_value = {
        "items": [_event(), _event(event_type="DOCUMENT_DOWNLOADED")],
        "total": 2,
        "limit": 50,
        "offset": 0,
    }
    response = _client().get(
        f"/closing/competences/2026-05/documents/{doc_id}/events",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert data["events"][1]["event_type"] == "DOCUMENT_DOWNLOADED"


def test_list_events_forwards_pagination_and_scope(service):
    service.list_document_events.return_value = {
        "items": [], "total": 0, "limit": 10, "offset": 5,
    }
    response = _client().get(
        f"/closing/competences/2026-05/documents/{uuid.uuid4()}"
        "/events?branch_scope=MATRIX&limit=10&offset=5",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    call = service.list_document_events.call_args.kwargs
    assert call["branch_scope"] == "MATRIX"
    assert call["limit"] == 10 and call["offset"] == 5


def test_list_events_outside_scope_is_404(service):
    service.list_document_events.side_effect = de.DocumentNotFound("não")
    response = _client().get(
        f"/closing/competences/2026-05/documents/{uuid.uuid4()}/events",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 404
    assert response.json()["data"]["error"]["code"] == "document_not_found"
