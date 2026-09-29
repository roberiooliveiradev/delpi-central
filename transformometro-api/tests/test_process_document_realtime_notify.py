"""Realtime invalidation contract for ProcessDocument writes.

Contract: every canonical write (HTTP Portal + governed GPT/MCP) emits
entity.updated(entity_type="process_document", sectionKey="documentacao")
fanned out to the parent room ``processo:{processo_id}``. The WS event is an
invalidation signal only — it must never carry ``content_md``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tm_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tm_app.application.services.transformometro_realtime_notify import (
    _related_rooms,
    enrich_realtime_scope_payload,
    infer_section_key,
)
from tm_app.application.use_cases.manage_process_documents import ProcessDocumentUseCases
from tm_app.domain.entities.process_document import ProcessDocument
from tm_app.infrastructure.persistence.repositories.process_document_repository import (
    InMemoryProcessDocumentRepository,
)

USER = "11111111-1111-1111-1111-111111111111"
PROCESS_A = "33333333-3333-3333-3333-333333333333"
DOC_ID = "66666666-6666-6666-6666-666666666666"


def test_section_key_maps_process_document_crud_to_documentacao():
    for action in ("create", "update", "delete"):
        assert infer_section_key("process_document", action) == "documentacao"


def test_related_rooms_fans_out_to_parent_processo_room():
    rooms = _related_rooms(
        "process_document",
        DOC_ID,
        {"processo_id": PROCESS_A, "document_id": DOC_ID},
    )
    assert f"process_document:{DOC_ID}" in rooms
    assert f"processo:{PROCESS_A}" in rooms
    # Documents do not invalidate catalog/dashboard listings.
    assert not any(room.startswith("catalog:") for room in rooms)


def test_related_rooms_without_processo_scope_stays_local():
    rooms = _related_rooms("process_document", DOC_ID, {"document_id": DOC_ID})
    assert rooms == [f"process_document:{DOC_ID}"]


def test_enrich_scope_payload_looks_up_document_processo(monkeypatch):
    doc = SimpleNamespace(processo_id=PROCESS_A)
    monkeypatch.setattr(
        "tm_app.infrastructure.persistence.repositories.process_document_repository"
        ".ProcessDocumentRepository.get_by_document_id",
        lambda self, document_id: doc,
    )
    body = enrich_realtime_scope_payload("process_document", DOC_ID, {})
    assert body["processo_id"] == PROCESS_A


def test_enrich_scope_payload_keeps_existing_processo_id(monkeypatch):
    monkeypatch.setattr(
        "tm_app.infrastructure.persistence.repositories.process_document_repository"
        ".ProcessDocumentRepository.get_by_document_id",
        lambda self, document_id: SimpleNamespace(processo_id="other"),
    )
    body = enrich_realtime_scope_payload(
        "process_document", DOC_ID, {"processo_id": PROCESS_A}
    )
    assert body["processo_id"] == PROCESS_A


def _http_cases() -> tuple[ProcessDocumentUseCases, InMemoryProcessDocumentRepository]:
    repo = InMemoryProcessDocumentRepository()
    repo.processes.add(PROCESS_A)
    return ProcessDocumentUseCases(repo), repo


def _use_access_user():
    from tests.support import test_app as support

    prev = (
        support.TEST_USER.id,
        support.TEST_USER.is_superadmin,
        list(support.TEST_USER.permissions),
    )
    support.TEST_USER.id = USER
    support.TEST_USER.is_superadmin = False
    support.TEST_USER.permissions = ["transformometro.access"]
    return prev


def _restore_user(prev) -> None:
    from tests.support import test_app as support

    support.TEST_USER.id, support.TEST_USER.is_superadmin, perms = prev
    support.TEST_USER.permissions = perms


def test_http_writes_emit_realtime_invalidation(tm_client):
    prev = _use_access_user()

    cases, _repo = _http_cases()
    try:
        with (
            patch(
                "tm_app.interface.http.routes.process_document_routes._docs",
                cases,
            ),
            patch(
                "tm_app.interface.http.routes.process_document_routes"
                ".notify_entity_updated",
            ) as notify,
        ):
            created = tm_client.post(
                f"/transformometro/processos/{PROCESS_A}/documents",
                json={"title": "Doc", "content_md": "# secret body"},
            )
            assert created.status_code == 201
            document_id = created.json()["data"]["id"]

            patched = tm_client.patch(
                f"/transformometro/processos/{PROCESS_A}/documents/{document_id}",
                json={"content_md": "## novo"},
            )
            assert patched.status_code == 200

            deleted = tm_client.delete(
                f"/transformometro/processos/{PROCESS_A}/documents/{document_id}"
            )
            assert deleted.status_code == 200
    finally:
        _restore_user(prev)

    assert [call.kwargs["action"] for call in notify.call_args_list] == [
        "create",
        "update",
        "delete",
    ]
    for call in notify.call_args_list:
        assert call.kwargs["entity_type"] == "process_document"
        assert call.kwargs["entity_id"] == document_id
        payload = call.kwargs["payload"]
        assert payload["processo_id"] == PROCESS_A
        assert payload["document_id"] == document_id
        assert "content_md" not in payload


def test_http_failed_write_emits_no_event(tm_client):
    prev = _use_access_user()

    cases, _repo = _http_cases()
    try:
        with (
            patch(
                "tm_app.interface.http.routes.process_document_routes._docs",
                cases,
            ),
            patch(
                "tm_app.interface.http.routes.process_document_routes"
                ".notify_entity_updated",
            ) as notify,
        ):
            missing = tm_client.patch(
                f"/transformometro/processos/{PROCESS_A}/documents/{DOC_ID}",
                json={"title": "x"},
            )
            assert missing.status_code == 404
    finally:
        _restore_user(prev)

    notify.assert_not_called()


def _gpt_doc(**overrides) -> ProcessDocument:
    now = datetime.now(timezone.utc)
    base = dict(
        id="doc-1",
        processo_id="proc-1",
        title="AS-IS notes",
        content_md="# Hello",
        created_by_user_id="user-1",
        updated_by_user_id="user-1",
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return ProcessDocument(**base)


def _gpt_request():
    req = MagicMock()
    req.state.user = SimpleNamespace(
        id="user-1", permissions=["transformometro.access"]
    )
    return req


def test_gpt_writes_reach_realtime_notify_with_processo_scope():
    dispatch = GptActionsDispatchService()
    req = _gpt_request()
    doc = _gpt_doc()

    with (
        patch.object(dispatch._process_docs, "create_document", return_value=doc),
        patch.object(dispatch._process_docs, "get_document_by_id", return_value=doc),
        patch.object(dispatch._process_docs, "update_document", return_value=doc),
        patch.object(
            dispatch._process_docs,
            "delete_document",
            return_value=_gpt_doc(deleted_at=datetime.now(timezone.utc)),
        ),
        patch("tm_app.application.gpt_actions.dispatch_service.AuditRepository"),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.notify_from_audit"
        ) as notify,
    ):
        dispatch.create_record(
            req,
            "process_document",
            {"data": {"processo_id": "proc-1", "title": "T", "content_md": "c"}},
        )
        dispatch.update_record(
            req, "process_document", "doc-1", {"data": {"title": "T2"}}
        )
        dispatch.delete_record(req, "process_document", "doc-1")

    assert [call.kwargs["action"] for call in notify.call_args_list] == [
        "create",
        "update",
        "delete",
    ]
    for call in notify.call_args_list:
        assert call.kwargs["entity_type"] == "process_document"
        assert call.kwargs["payload"]["processo_id"] == "proc-1"
        assert "content_md" not in call.kwargs["payload"]
