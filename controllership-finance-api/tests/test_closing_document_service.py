"""Orquestração do upload — C2 + D-U7 sem I/O real (fakes).

Idempotência: existente com mesmo `request_hash` ⇒ deduplicated;
hash divergente ⇒ `idempotency_conflict`; corrida perdida ⇒ binário
órfão é compensado; falha de persistência ⇒ binário removido; falha de
compensação ⇒ log, nunca sucesso falso.
"""

from __future__ import annotations

import hashlib
import uuid
from unittest.mock import MagicMock

import pytest

from controllership_finance_app.application.services.closing_document_service import (
    ClosingDocumentService,
    _version_request_hash,
)
from controllership_finance_app.domain.closing_checklist import errors as de
from controllership_finance_app.infrastructure.storage.closing_document_storage import (
    ClosingDocumentStorage,
)


def _pdf() -> bytes:
    return b"%PDF-1.4\n" + b"x" * 2048 + b"\n%%EOF\n"


def _corrupted_pdf() -> bytes:
    return b"%PDF-1.4\n" + b"x" * 2048  # sem trailer %%EOF


def _invalid_xlsx() -> bytes:
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("random.txt", "sem membros OOXML")
    return buf.getvalue()


def _no_parts(tmp_path) -> None:
    assert list((tmp_path / ".tmp").glob("*.part")) == []


def _repo(doc=None, item_ok=True, item_scope="BOTH") -> MagicMock:
    repo = MagicMock()
    repo.get_competence_id.return_value = str(uuid.uuid4())
    if item_ok:
        repo.get_snapshot_item.return_value = {
            "snapshot_item_id": uuid.uuid4(),
            "branch_scope": item_scope,
        }
    else:
        repo.get_snapshot_item.side_effect = de.ItemNotFound("item")
    repo.find_document_by_idempotency.return_value = doc
    repo.create_document.return_value = (
        doc
        if doc is not None
        else MagicMock(document_id=uuid.uuid4(), state="ATTACHED"),
        True,
    )
    repo.get_document_by_id.return_value = MagicMock(
        document_id=uuid.uuid4(), state="ATTACHED"
    )
    repo.find_version_by_idempotency.return_value = None
    repo.add_version.return_value = (MagicMock(), True)
    return repo


def _storage(tmp_path) -> ClosingDocumentStorage:
    return ClosingDocumentStorage(str(tmp_path))


def _upload_kwargs(**overrides):
    kw = {
        "period": "2026-05",
        "actor": str(uuid.uuid4()),
        "original_name": "extrato.pdf",
        "declared_mime": "application/pdf",
        "chunks": [_pdf()],
        "snapshot_item_id": None,
        "title": "Extrato",
        "attachment_role": None,
        "idempotency_key": "key-1",
    }
    kw.update(overrides)
    return kw


def test_upload_happy_creates_document_and_binary(tmp_path):
    repo = _repo()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    doc, created = service.upload(**_upload_kwargs())
    assert created is True
    repo.create_document.assert_called_once()
    call = repo.create_document.call_args.kwargs
    assert call["link_kind"] == "competence"
    assert call["attachment_role"] == "generic"
    assert call["checksum_sha256"]
    assert call["size_bytes"] == len(_pdf())


def test_upload_to_item_validates_membership(tmp_path):
    repo = _repo()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    item_id = str(uuid.uuid4())
    service.upload(**_upload_kwargs(snapshot_item_id=item_id))
    repo.get_snapshot_item.assert_called_once()
    assert (
        repo.create_document.call_args.kwargs["link_kind"]
        == "competence_item"
    )


def test_upload_cross_competence_item_404(tmp_path):
    repo = _repo(item_ok=False)
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.ItemNotFound):
        service.upload(**_upload_kwargs(snapshot_item_id=str(uuid.uuid4())))
    repo.create_document.assert_not_called()


def test_upload_item_scope_matches_declared_context(tmp_path):
    # Ana (contexto Matriz) anexa em item MATRIX — dentro do escopo.
    repo = _repo(item_scope="MATRIX")
    service = ClosingDocumentService(repo, _storage(tmp_path))
    doc, created = service.upload(
        **_upload_kwargs(
            snapshot_item_id=str(uuid.uuid4()), branch_scope="MATRIX"
        )
    )
    assert created is True


def test_upload_item_outside_declared_scope_is_404(tmp_path):
    # Bruno (contexto Filial) tenta anexar no mesmo item MATRIX —
    # fora do escopo declarado: 404, sem criar documento nem arquivo.
    repo = _repo(item_scope="MATRIX")
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.ItemNotFound):
        service.upload(
            **_upload_kwargs(
                snapshot_item_id=str(uuid.uuid4()), branch_scope="BRANCH"
            )
        )
    repo.create_document.assert_not_called()


def test_upload_invalid_branch_scope_rejected(tmp_path):
    repo = _repo()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.InvalidUpload):
        service.upload(**_upload_kwargs(branch_scope="filial-99"))


def test_upload_missing_idempotency_key(tmp_path):
    repo = _repo()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.InvalidUpload):
        service.upload(**_upload_kwargs(idempotency_key="  "))
    repo.create_document.assert_not_called()


def test_upload_non_generic_role_rejected(tmp_path):
    repo = _repo()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.InvalidUpload):
        service.upload(**_upload_kwargs(attachment_role="comprovante"))


def test_replay_same_hash_deduplicates(tmp_path):
    repo = _repo()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    service.upload(**_upload_kwargs())
    # Segundo upload idêntico: simula registro existente com o mesmo hash.
    first_call = repo.create_document.call_args.kwargs
    repo.find_document_by_idempotency.return_value = {
        "document_id": uuid.uuid4(),
        "request_hash": first_call["request_hash"],
    }
    doc, created = service.upload(**_upload_kwargs())
    assert created is False
    assert repo.create_document.call_count == 1
    # `.part` do replay foi descartado, nenhum binário duplicado.
    parts = list((tmp_path / ".tmp").glob("*.part"))
    assert parts == []


def test_same_key_divergent_payload_conflicts(tmp_path):
    repo = _repo()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    repo.find_document_by_idempotency.return_value = {
        "document_id": uuid.uuid4(),
        "request_hash": "diferente",
    }
    with pytest.raises(de.IdempotencyConflict):
        service.upload(**_upload_kwargs())
    repo.create_document.assert_not_called()


def test_race_lost_compensates_binary(tmp_path):
    repo = _repo()
    # Corrida perdida: create_document retorna created=False (vencedor
    # concorrente) — o binário desta tentativa vira órfão e é removido.
    repo.create_document.return_value = (MagicMock(), False)
    storage = _storage(tmp_path)
    service = ClosingDocumentService(repo, storage)
    service.upload(**_upload_kwargs())
    finals = [p for p in tmp_path.rglob("*") if p.is_file() and ".tmp" not in str(p)]
    assert finals == []


def test_persistence_failure_compensates_binary(tmp_path):
    repo = _repo()
    repo.create_document.side_effect = de.PersistenceUnavailable("db down")
    storage = _storage(tmp_path)
    service = ClosingDocumentService(repo, storage)
    with pytest.raises(de.PersistenceUnavailable):
        service.upload(**_upload_kwargs())
    finals = [p for p in tmp_path.rglob("*") if p.is_file() and ".tmp" not in str(p)]
    assert finals == []


# -- R-W2: `.part` nunca permanece após rejeição -----------------------------


def test_rejected_corrupted_pdf_leaves_no_part(tmp_path):
    repo = _repo()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.InvalidFileContent):
        service.upload(
            **_upload_kwargs(chunks=[_corrupted_pdf()])
        )
    _no_parts(tmp_path)


def test_rejected_invalid_xlsx_leaves_no_part(tmp_path):
    repo = _repo()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.InvalidFileContent):
        service.upload(
            **_upload_kwargs(
                original_name="planilha.xlsx",
                declared_mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"
                ),
                chunks=[_invalid_xlsx()],
            )
        )
    _no_parts(tmp_path)


def test_rejected_content_type_mismatch_leaves_no_part(tmp_path):
    repo = _repo()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.ContentTypeMismatch):
        service.upload(
            **_upload_kwargs(
                original_name="extrato.pdf",
                declared_mime="application/pdf",
                chunks=[b"col1;col2\ntexto;plano\n"],  # CSV real
            )
        )
    _no_parts(tmp_path)


def test_rejected_unsupported_extension_leaves_no_part(tmp_path):
    repo = _repo()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.UnsupportedMediaType):
        service.upload(
            **_upload_kwargs(
                original_name="retorno.ofx",
                declared_mime="application/x-ofx",
                chunks=[b"OFXHEADER:100\n"],
            )
        )
    _no_parts(tmp_path)


def test_publish_failure_leaves_no_part(tmp_path, monkeypatch):
    repo = _repo()
    storage = _storage(tmp_path)
    monkeypatch.setattr(
        storage, "publish", MagicMock(side_effect=OSError("disk full"))
    )
    service = ClosingDocumentService(repo, storage)
    with pytest.raises(OSError):
        service.upload(**_upload_kwargs())
    _no_parts(tmp_path)


# -- R-W1: escopo de filial em U2/U3 ------------------------------------------


def test_list_documents_forwards_scope(tmp_path):
    repo = _repo()
    repo.list_documents.return_value = {
        "items": [], "total": 0, "limit": 50, "offset": 0,
    }
    service = ClosingDocumentService(repo, _storage(tmp_path))
    service.list_documents(
        period="2026-05",
        snapshot_item_id=None,
        link_kind=None,
        state=None,
        branch_scope="BRANCH",
        limit=50,
        offset=0,
    )
    assert repo.list_documents.call_args.kwargs["branch_scope"] == "BRANCH"


def test_list_documents_both_context_is_unrestricted(tmp_path):
    repo = _repo()
    repo.list_documents.return_value = {
        "items": [], "total": 0, "limit": 50, "offset": 0,
    }
    service = ClosingDocumentService(repo, _storage(tmp_path))
    service.list_documents(
        period="2026-05",
        snapshot_item_id=None,
        link_kind=None,
        state=None,
        branch_scope="BOTH",
        limit=50,
        offset=0,
    )
    assert repo.list_documents.call_args.kwargs["branch_scope"] is None


def test_get_document_outside_declared_scope_is_404(tmp_path):
    repo = _repo()
    repo.get_document_by_id.return_value = {
        "document_id": uuid.uuid4(),
        "branch_scope": "BRANCH",
    }
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.DocumentNotFound):
        service.get_document(
            period="2026-05",
            document_id=str(uuid.uuid4()),
            branch_scope="MATRIX",
        )


def test_get_document_inside_declared_scope(tmp_path):
    repo = _repo()
    doc = {"document_id": uuid.uuid4(), "branch_scope": "BRANCH"}
    repo.get_document_by_id.return_value = doc
    service = ClosingDocumentService(repo, _storage(tmp_path))
    assert (
        service.get_document(
            period="2026-05",
            document_id=str(uuid.uuid4()),
            branch_scope="BRANCH",
        )
        is doc
    )


def test_download_resolves_and_audits(tmp_path):
    repo = _repo()
    storage = _storage(tmp_path)
    file_uuid = uuid.uuid4()
    tmp, _d, _s = storage.write_temp(file_uuid, [_pdf()])
    key, _n, final = storage.publish(
        tmp,
        competence_id=str(uuid.uuid4()),
        file_uuid=file_uuid,
        extension=".pdf",
    )
    repo.get_version_file.return_value = {
        "storage_key": key,
        "mime_type": "application/pdf",
        "original_name": "extrato.pdf",
    }
    service = ClosingDocumentService(repo, storage)
    path, meta = service.resolve_download(
        period="2026-05",
        document_id=str(uuid.uuid4()),
        version_no=1,
        actor=str(uuid.uuid4()),
    )
    assert path == final
    repo.audit_download.assert_called_once()
    assert repo.audit_download.call_args.kwargs["result"] == "AUTHORIZED"


def test_download_missing_binary_audits_failed_never_success(tmp_path):
    repo = _repo()
    repo.get_version_file.return_value = {
        "storage_key": f"{uuid.uuid4()}/inexistente.pdf",
        "mime_type": "application/pdf",
        "original_name": "x.pdf",
        "branch_scope": "BOTH",
    }
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.FileMissing):
        service.resolve_download(
            period="2026-05",
            document_id=str(uuid.uuid4()),
            version_no=1,
            actor=str(uuid.uuid4()),
        )
    repo.audit_download.assert_called_once()
    assert repo.audit_download.call_args.kwargs["result"] == "FAILED"


def test_download_outside_declared_scope_denied_and_audited(tmp_path):
    # Bruno (contexto Filial) tenta baixar evidência de item MATRIX —
    # negação auditável (ator+recurso conhecidos); resposta é 404.
    repo = _repo()
    repo.get_version_file.return_value = {
        "storage_key": f"{uuid.uuid4()}/extrato.pdf",
        "mime_type": "application/pdf",
        "original_name": "x.pdf",
        "branch_scope": "MATRIX",
    }
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.DocumentNotFound):
        service.resolve_download(
            period="2026-05",
            document_id=str(uuid.uuid4()),
            version_no=1,
            actor=str(uuid.uuid4()),
            branch_scope="BRANCH",
        )
    repo.audit_download.assert_called_once()
    assert repo.audit_download.call_args.kwargs["result"] == "DENIED"


def test_download_inside_declared_scope_authorized(tmp_path):
    repo = _repo()
    storage = _storage(tmp_path)
    file_uuid = uuid.uuid4()
    tmp, _d, _s = storage.write_temp(file_uuid, [_pdf()])
    key, _n, _f = storage.publish(
        tmp,
        competence_id=str(uuid.uuid4()),
        file_uuid=file_uuid,
        extension=".pdf",
    )
    repo.get_version_file.return_value = {
        "storage_key": key,
        "mime_type": "application/pdf",
        "original_name": "extrato.pdf",
        "branch_scope": "MATRIX",
    }
    service = ClosingDocumentService(repo, storage)
    path, _meta = service.resolve_download(
        period="2026-05",
        document_id=str(uuid.uuid4()),
        version_no=1,
        actor=str(uuid.uuid4()),
        branch_scope="MATRIX",
    )
    assert path.is_file()
    assert repo.audit_download.call_args.kwargs["result"] == "AUTHORIZED"


# -- U5/U7: mutações (SLICE-2) -------------------------------------------------


def _attached_doc(**overrides):
    doc = {
        "document_id": uuid.uuid4(),
        "competence_id": uuid.uuid4(),
        "state": "ATTACHED",
        "revision": 3,
        "current_version_no": 1,
        "uploaded_by": uuid.uuid4(),
        "branch_scope": "BOTH",
    }
    doc.update(overrides)
    return doc


def _replace_kwargs(**overrides):
    kw = {
        "period": "2026-05",
        "document_id": str(uuid.uuid4()),
        "actor": str(uuid.uuid4()),
        "can_manage": False,
        "original_name": "extrato2.pdf",
        "declared_mime": "application/pdf",
        "chunks": [_pdf()],
        "expected_revision": 3,
        "idempotency_key": "replace-key-1",
    }
    kw.update(overrides)
    return kw


def _no_finals(tmp_path) -> None:
    assert [
        p for p in tmp_path.rglob("*") if p.is_file() and ".tmp" not in str(p)
    ] == []


def test_replace_by_uploader_creates_version(tmp_path):
    actor = str(uuid.uuid4())
    repo = _repo()
    doc = _attached_doc(uploaded_by=actor)
    repo.get_document_by_id.return_value = doc
    service = ClosingDocumentService(repo, _storage(tmp_path))
    service.replace_document(
        **_replace_kwargs(document_id=str(doc["document_id"]), actor=actor)
    )
    repo.add_version.assert_called_once()
    call = repo.add_version.call_args.kwargs
    assert call["document_id"] == str(doc["document_id"])
    assert call["expected_revision"] == 3
    assert call["actor"] == actor
    assert call["checksum_sha256"]


def test_replace_by_eligible_manage_allowed(tmp_path):
    # Gestor com manage (e access — a rota exige access antes) que NÃO é
    # o uploader pode substituir; o evento registra o ator gestor.
    repo = _repo()
    manager = str(uuid.uuid4())
    repo.get_document_by_id.return_value = _attached_doc()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    service.replace_document(
        **_replace_kwargs(actor=manager, can_manage=True)
    )
    assert repo.add_version.call_args.kwargs["actor"] == manager


def test_replace_by_non_uploader_without_manage_forbidden(tmp_path):
    # Ana anexou; Bruno tem access mas não é uploader nem gestor — 403.
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.Forbidden):
        service.replace_document(**_replace_kwargs())
    repo.add_version.assert_not_called()
    _no_parts(tmp_path)
    _no_finals(tmp_path)


def test_replace_on_cancelled_document_denied(tmp_path):
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(
        state="CANCELLED", uploaded_by=actor
    )
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.DocumentCancelled):
        service.replace_document(
            **_replace_kwargs(actor=actor)
        )
    repo.add_version.assert_not_called()
    _no_finals(tmp_path)


def test_replace_stale_revision_fails_before_write(tmp_path):
    # O ator viu revision 3, o documento já está em 5 — nada toca o disco.
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(
        revision=5, uploaded_by=actor
    )
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.StaleRevision):
        service.replace_document(
            **_replace_kwargs(actor=actor, expected_revision=3)
        )
    repo.add_version.assert_not_called()
    _no_parts(tmp_path)
    _no_finals(tmp_path)


def test_replace_outside_declared_scope_is_404(tmp_path):
    # Evidência de item MATRIX consultada por contexto Filial — 404.
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(
        uploaded_by=actor, branch_scope="MATRIX"
    )
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.DocumentNotFound):
        service.replace_document(
            **_replace_kwargs(actor=actor, branch_scope="BRANCH")
        )
    repo.add_version.assert_not_called()
    _no_finals(tmp_path)


def test_replace_invalid_file_leaves_no_part(tmp_path):
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(uploaded_by=actor)
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.InvalidFileContent):
        service.replace_document(
            **_replace_kwargs(actor=actor, chunks=[_corrupted_pdf()])
        )
    repo.add_version.assert_not_called()
    _no_parts(tmp_path)


def test_replace_persistence_failure_compensates_new_binary(tmp_path):
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(uploaded_by=actor)
    repo.add_version.side_effect = de.PersistenceUnavailable("db down")
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.PersistenceUnavailable):
        service.replace_document(**_replace_kwargs(actor=actor))
    _no_parts(tmp_path)
    _no_finals(tmp_path)


def test_replace_publish_failure_leaves_no_part(tmp_path, monkeypatch):
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(uploaded_by=actor)
    storage = _storage(tmp_path)
    monkeypatch.setattr(
        storage, "publish", MagicMock(side_effect=OSError("disk full"))
    )
    service = ClosingDocumentService(repo, storage)
    with pytest.raises(OSError):
        service.replace_document(**_replace_kwargs(actor=actor))
    _no_parts(tmp_path)
    _no_finals(tmp_path)


def test_replace_idempotent_replay_deduplicates(tmp_path):
    # Mesma key + mesmo binário (request_hash igual) ⇒ efeito já
    # aplicado: retorna o documento vigente, sem nova versão, sem novo
    # binário — mesmo com revision do request já obsoleta.
    actor = str(uuid.uuid4())
    repo = _repo()
    doc = _attached_doc(uploaded_by=actor, revision=9)
    repo.get_document_by_id.return_value = doc
    prior_hash = _version_request_hash(
        checksum_sha256=hashlib.sha256(_pdf()).hexdigest()
    )
    repo.find_version_by_idempotency.return_value = {
        "version_no": 2,
        "request_hash": prior_hash,
    }
    service = ClosingDocumentService(repo, _storage(tmp_path))
    document, created = service.replace_document(
        **_replace_kwargs(
            document_id=str(doc["document_id"]),
            actor=actor,
            expected_revision=3,  # obsoleta — dedup resolve antes
        )
    )
    assert created is False
    assert document is doc
    repo.add_version.assert_not_called()
    _no_parts(tmp_path)
    _no_finals(tmp_path)


def test_replace_same_key_divergent_payload_conflicts(tmp_path):
    # Mesma key + binário divergente ⇒ idempotency_conflict 409; nada
    # toca disco nem repositório.
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(
        uploaded_by=actor
    )
    repo.find_version_by_idempotency.return_value = {
        "version_no": 2,
        "request_hash": "0" * 64,
    }
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.IdempotencyConflict):
        service.replace_document(**_replace_kwargs(actor=actor))
    repo.add_version.assert_not_called()
    _no_parts(tmp_path)
    _no_finals(tmp_path)


def test_replace_requires_idempotency_key(tmp_path):
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(
        uploaded_by=actor
    )
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.InvalidUpload):
        service.replace_document(
            **_replace_kwargs(actor=actor, idempotency_key="  ")
        )
    repo.add_version.assert_not_called()
    _no_finals(tmp_path)


def test_replace_race_lost_compensates_published_binary(tmp_path):
    # Corrida perdida sob lock (pre-check passou, add_version deduplicou
    # o vencedor): o binário que publicamos é órfão e é removido.
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(
        uploaded_by=actor
    )
    repo.add_version.return_value = (MagicMock(), False)
    service = ClosingDocumentService(repo, _storage(tmp_path))
    _, created = service.replace_document(
        **_replace_kwargs(actor=actor)
    )
    assert created is False
    _no_parts(tmp_path)
    _no_finals(tmp_path)


def test_cancel_by_uploader(tmp_path):
    actor = str(uuid.uuid4())
    repo = _repo()
    doc = _attached_doc(uploaded_by=actor)
    repo.get_document_by_id.return_value = doc
    service = ClosingDocumentService(repo, _storage(tmp_path))
    service.cancel_document(
        period="2026-05",
        document_id="doc-1",
        actor=actor,
        can_manage=False,
        expected_revision=3,
    )
    repo.cancel_document.assert_called_once()
    assert repo.cancel_document.call_args.kwargs["expected_revision"] == 3


def test_cancel_by_eligible_manage_allowed(tmp_path):
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    service.cancel_document(
        period="2026-05",
        document_id="doc-1",
        actor=str(uuid.uuid4()),
        can_manage=True,
        expected_revision=3,
    )
    repo.cancel_document.assert_called_once()


def test_cancel_by_non_uploader_without_manage_forbidden(tmp_path):
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc()
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.Forbidden):
        service.cancel_document(
            period="2026-05",
            document_id="doc-1",
            actor=str(uuid.uuid4()),
            can_manage=False,
            expected_revision=3,
        )
    repo.cancel_document.assert_not_called()


def test_cancel_already_cancelled_denied(tmp_path):
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(
        state="CANCELLED", uploaded_by=actor
    )
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.DocumentCancelled):
        service.cancel_document(
            period="2026-05",
            document_id="doc-1",
            actor=actor,
            can_manage=False,
            expected_revision=3,
        )
    repo.cancel_document.assert_not_called()


def test_cancel_outside_declared_scope_is_404(tmp_path):
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(
        uploaded_by=actor, branch_scope="MATRIX"
    )
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.DocumentNotFound):
        service.cancel_document(
            period="2026-05",
            document_id="doc-1",
            actor=actor,
            can_manage=False,
            expected_revision=3,
            branch_scope="BRANCH",
        )
    repo.cancel_document.assert_not_called()


def test_cancel_stale_revision_propagates(tmp_path):
    actor = str(uuid.uuid4())
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(uploaded_by=actor)
    repo.cancel_document.side_effect = de.StaleRevision("stale")
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.StaleRevision):
        service.cancel_document(
            period="2026-05",
            document_id="doc-1",
            actor=actor,
            can_manage=False,
            expected_revision=1,
        )


# -- U6/U8: histórico e eventos (SLICE-2) --------------------------------------


def test_list_versions_inside_scope(tmp_path):
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(branch_scope="BRANCH")
    repo.list_document_versions.return_value = [{"version_no": 2}]
    service = ClosingDocumentService(repo, _storage(tmp_path))
    out = service.list_document_versions(
        period="2026-05",
        document_id="doc-1",
        branch_scope="BRANCH",
    )
    assert out == [{"version_no": 2}]
    repo.list_document_versions.assert_called_once()


def test_list_versions_outside_scope_is_404(tmp_path):
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(branch_scope="MATRIX")
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.DocumentNotFound):
        service.list_document_versions(
            period="2026-05",
            document_id="doc-1",
            branch_scope="BRANCH",
        )
    repo.list_document_versions.assert_not_called()


def test_list_events_inside_scope(tmp_path):
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc()
    repo.list_document_events.return_value = {
        "items": [], "total": 0, "limit": 50, "offset": 0,
    }
    service = ClosingDocumentService(repo, _storage(tmp_path))
    service.list_document_events(
        period="2026-05",
        document_id="doc-1",
        branch_scope=None,
        limit=25,
        offset=10,
    )
    call = repo.list_document_events.call_args.kwargs
    assert call["limit"] == 25 and call["offset"] == 10


def test_list_events_outside_scope_is_404(tmp_path):
    repo = _repo()
    repo.get_document_by_id.return_value = _attached_doc(branch_scope="MATRIX")
    service = ClosingDocumentService(repo, _storage(tmp_path))
    with pytest.raises(de.DocumentNotFound):
        service.list_document_events(
            period="2026-05",
            document_id="doc-1",
            branch_scope="BRANCH",
            limit=50,
            offset=0,
        )
    repo.list_document_events.assert_not_called()
