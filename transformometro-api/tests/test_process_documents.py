from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
)
from tm_app.application.use_cases.manage_process_documents import ProcessDocumentUseCases
from tm_app.domain.services.process_document_rules import (
    MAX_CONTENT_MD_LENGTH,
    MAX_TITLE_LENGTH,
    normalize_document_content_md,
    normalize_document_title,
)
from tm_app.infrastructure.persistence.repositories.process_document_repository import (
    InMemoryProcessDocumentRepository,
)

USER = "11111111-1111-1111-1111-111111111111"
PROCESS_A = "33333333-3333-3333-3333-333333333333"
PROCESS_B = "44444444-4444-4444-4444-444444444444"

# operationIds do baseline:
# list_process_documents
# create_process_document
# get_process_document
# update_process_document
# delete_process_document


def _user(*, permissions=None, user_id=USER):
    return SimpleNamespace(
        id=user_id,
        permissions=[ACCESS_PERMISSION] if permissions is None else permissions,
        is_superadmin=False,
    )


def _cases() -> tuple[ProcessDocumentUseCases, InMemoryProcessDocumentRepository]:
    repo = InMemoryProcessDocumentRepository()
    repo.processes.add(PROCESS_A)
    repo.processes.add(PROCESS_B)
    return ProcessDocumentUseCases(repo), repo


def test_title_and_content_rules():
    assert normalize_document_title("  Visão geral  ") == "Visão geral"
    with pytest.raises(ValueError):
        normalize_document_title("   ")
    with pytest.raises(ValueError):
        normalize_document_title("x" * (MAX_TITLE_LENGTH + 1))
    assert normalize_document_content_md("") == ""
    assert normalize_document_content_md("a\r\nb") == "a\nb"
    with pytest.raises(ValueError):
        normalize_document_content_md("x" * (MAX_CONTENT_MD_LENGTH + 1))


def test_create_list_get_update_delete_with_read_back():
    cases, _repo = _cases()
    created = cases.create_document(
        _user(),
        PROCESS_A,
        title="Visão geral",
        content_md="# Intro\n\nTexto",
    )
    assert created.processo_id == PROCESS_A
    assert created.title == "Visão geral"
    assert created.content_md == "# Intro\n\nTexto"
    assert created.created_by_user_id == USER

    listed = cases.list_documents(_user(), PROCESS_A)
    assert [item.id for item in listed] == [created.id]
    assert "content_md" not in listed[0].to_summary_dict()

    detail = cases.get_document(_user(), PROCESS_A, created.id)
    assert detail.content_md == "# Intro\n\nTexto"

    updated = cases.update_document(
        _user(),
        PROCESS_A,
        created.id,
        title="Fluxo",
        content_md="## Fluxo\n\n- passo",
    )
    assert updated.title == "Fluxo"
    assert updated.content_md == "## Fluxo\n\n- passo"
    assert updated.updated_by_user_id == USER

    deleted = cases.delete_document(_user(), PROCESS_A, created.id)
    assert deleted.deleted_at is not None
    assert cases.list_documents(_user(), PROCESS_A) == []
    with pytest.raises(LookupError):
        cases.get_document(_user(), PROCESS_A, created.id)


def test_process_isolation_and_missing_process():
    cases, _repo = _cases()
    doc_a = cases.create_document(_user(), PROCESS_A, title="A", content_md="a")
    doc_b = cases.create_document(_user(), PROCESS_B, title="B", content_md="b")
    assert [item.id for item in cases.list_documents(_user(), PROCESS_A)] == [doc_a.id]
    assert [item.id for item in cases.list_documents(_user(), PROCESS_B)] == [doc_b.id]
    with pytest.raises(LookupError):
        cases.get_document(_user(), PROCESS_A, doc_b.id)
    with pytest.raises(LookupError):
        cases.list_documents(_user(), "55555555-5555-5555-5555-555555555555")


def test_authz_access_manage_only_and_anonymous():
    cases, _repo = _cases()
    with pytest.raises(AuthorizationDenied) as denied:
        cases.list_documents(None, PROCESS_A)
    assert denied.value.status_code == 401

    with pytest.raises(AuthorizationDenied):
        cases.create_document(_user(permissions=[]), PROCESS_A, title="X")

    with pytest.raises(AuthorizationDenied):
        cases.create_document(_user(permissions=[MANAGE_PERMISSION]), PROCESS_A, title="X")

    created = cases.create_document(_user(), PROCESS_A, title="Ok", content_md="")
    assert created.title == "Ok"


def test_ordering_updated_at_desc():
    cases, repo = _cases()
    first = cases.create_document(_user(), PROCESS_A, title="Primeiro", content_md="1")
    second = cases.create_document(_user(), PROCESS_A, title="Segundo", content_md="2")
    cases.update_document(_user(), PROCESS_A, first.id, content_md="1b")
    listed = cases.list_documents(_user(), PROCESS_A)
    assert [item.id for item in listed] == [first.id, second.id]
    assert repo.get(processo_id=PROCESS_A, document_id=first.id) is not None


def test_http_routes_authz_and_crud(tm_client):
    from tests.support import test_app as support

    prev_id = support.TEST_USER.id
    prev_super = support.TEST_USER.is_superadmin
    prev_perms = list(support.TEST_USER.permissions)
    support.TEST_USER.id = USER
    support.TEST_USER.is_superadmin = False
    support.TEST_USER.permissions = [ACCESS_PERMISSION]

    repo = InMemoryProcessDocumentRepository()
    repo.processes.add(PROCESS_A)
    repo.processes.add(PROCESS_B)
    cases = ProcessDocumentUseCases(repo)

    try:
        with patch(
            "tm_app.interface.http.routes.process_document_routes._docs",
            cases,
        ):
            missing = tm_client.get(
                f"/transformometro/processos/55555555-5555-5555-5555-555555555555/documents"
            )
            assert missing.status_code == 404

            created = tm_client.post(
                f"/transformometro/processos/{PROCESS_A}/documents",
                json={"title": "Http Doc", "content_md": "**ok**"},
            )
            assert created.status_code == 201
            body = created.json()["data"]
            document_id = body["id"]
            assert body["content_md"] == "**ok**"

            listed = tm_client.get(f"/transformometro/processos/{PROCESS_A}/documents")
            assert listed.status_code == 200
            items = listed.json()["data"]["items"]
            assert items[0]["id"] == document_id
            assert "content_md" not in items[0]

            detail = tm_client.get(
                f"/transformometro/processos/{PROCESS_A}/documents/{document_id}"
            )
            assert detail.status_code == 200
            assert detail.json()["data"]["content_md"] == "**ok**"

            patched = tm_client.patch(
                f"/transformometro/processos/{PROCESS_A}/documents/{document_id}",
                json={"title": "Atualizado", "content_md": "## novo"},
            )
            assert patched.status_code == 200
            assert patched.json()["data"]["title"] == "Atualizado"

            cross = tm_client.get(
                f"/transformometro/processos/{PROCESS_B}/documents/{document_id}"
            )
            assert cross.status_code == 404

            deleted = tm_client.delete(
                f"/transformometro/processos/{PROCESS_A}/documents/{document_id}"
            )
            assert deleted.status_code == 200
            gone = tm_client.get(
                f"/transformometro/processos/{PROCESS_A}/documents/{document_id}"
            )
            assert gone.status_code == 404

            support.TEST_USER.permissions = [MANAGE_PERMISSION]
            manage_only = tm_client.get(f"/transformometro/processos/{PROCESS_A}/documents")
            assert manage_only.status_code == 403

            support.TEST_USER.permissions = []
            no_access = tm_client.get(f"/transformometro/processos/{PROCESS_A}/documents")
            assert no_access.status_code == 403
    finally:
        support.TEST_USER.id = prev_id
        support.TEST_USER.is_superadmin = prev_super
        support.TEST_USER.permissions = prev_perms
