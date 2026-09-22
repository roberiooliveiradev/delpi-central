"""Process Documentation via governed GPT entity catalog (no new Action routes)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.application.gpt_actions.entities import GptEntity, entity_supports, parse_entity
from tm_app.application.gpt_actions.openapi_builder import (
    GPT_ACTIONS_OPERATION_IDS,
    build_gpt_actions_openapi,
    count_operations,
)
from tm_app.domain.entities.process_document import ProcessDocument


def _user():
    return SimpleNamespace(id="user-1", permissions=["transformometro.access"])


def _request():
    req = MagicMock()
    req.state.user = _user()
    return req


def _doc(**overrides) -> ProcessDocument:
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


def test_process_document_entity_in_catalog():
    assert parse_entity("process_document") is GptEntity.PROCESS_DOCUMENT
    assert entity_supports(GptEntity.PROCESS_DOCUMENT, "search")
    assert entity_supports(GptEntity.PROCESS_DOCUMENT, "get")
    assert entity_supports(GptEntity.PROCESS_DOCUMENT, "create")
    assert entity_supports(GptEntity.PROCESS_DOCUMENT, "update")
    assert entity_supports(GptEntity.PROCESS_DOCUMENT, "delete")
    assert not entity_supports(GptEntity.PROCESS_DOCUMENT, "duplicate")


def test_action_budget_unchanged_after_process_document_entity():
    doc = build_gpt_actions_openapi()
    assert count_operations(doc) == len(GPT_ACTIONS_OPERATION_IDS) == 21
    assert count_operations(doc) <= 30
    blob = str(doc)
    assert "process_document" in blob
    assert "gpt_list_process_documents" not in blob
    assert "gpt_call_any_route" not in blob
    assert "gpt_http_proxy" not in blob
    assert "gpt_run_sql" not in blob


def test_search_requires_parent_processo_id():
    dispatch = GptActionsDispatchService()
    with pytest.raises(GptActionsError) as exc:
        dispatch.search_records(_request(), "process_document")
    assert exc.value.status_code == 400
    assert "parent_id" in str(exc.value)


def test_search_lists_via_canonical_use_case():
    dispatch = GptActionsDispatchService()
    docs = [_doc(), _doc(id="doc-2", title="Other")]
    with patch.object(dispatch._process_docs, "list_documents", return_value=docs) as listed:
        result = dispatch.search_records(
            _request(), "process_document", parent_id="proc-1", q="as-is"
        )
    listed.assert_called_once()
    assert result["total"] == 1
    assert result["items"][0]["id"] == "doc-1"
    assert "content_md" not in result["items"][0]


def test_get_create_update_delete_delegate_to_use_case():
    dispatch = GptActionsDispatchService()
    req = _request()
    created = _doc()

    with patch.object(
        dispatch._process_docs, "get_document_by_id", return_value=created
    ) as getter:
        got = dispatch.get_record(req, "process_document", "doc-1")
    getter.assert_called_once()
    assert got["content_md"] == "# Hello"

    with (
        patch.object(dispatch._process_docs, "create_document", return_value=created) as creator,
        patch.object(dispatch, "_audit"),
    ):
        row, msg, status = dispatch.create_record(
            req,
            "process_document",
            {"data": {"processo_id": "proc-1", "title": "AS-IS notes", "content_md": "# Hello"}},
        )
    creator.assert_called_once()
    assert status == 201
    assert row["id"] == "doc-1"
    assert "Documento" in msg

    updated = _doc(title="Updated", content_md="# Updated")
    with (
        patch.object(dispatch._process_docs, "get_document_by_id", return_value=created),
        patch.object(dispatch._process_docs, "update_document", return_value=updated) as updater,
        patch.object(dispatch, "_audit"),
    ):
        row2, _msg2 = dispatch.update_record(
            req, "process_document", "doc-1", {"data": {"title": "Updated"}}
        )
    updater.assert_called_once()
    assert row2["title"] == "Updated"

    deleted = _doc(deleted_at=datetime.now(timezone.utc))
    with (
        patch.object(dispatch._process_docs, "get_document_by_id", return_value=created),
        patch.object(dispatch._process_docs, "delete_document", return_value=deleted) as deleter,
        patch.object(dispatch, "_audit"),
    ):
        row3, _msg3 = dispatch.delete_record(req, "process_document", "doc-1")
    deleter.assert_called_once()
    assert row3["id"] == "doc-1"
