"""Storage adapter — sequência C2 (doc 103): `.part` em chunks com cap
mid-stream → sha256 durante a gravação → `os.replace` atômico → resolve
com guarda de traversal → compensação `unlink`. Órfãos são identificáveis;
nenhuma limpeza garantida é declarada.
"""

from __future__ import annotations

import hashlib
import uuid

import pytest

from controllership_finance_app.domain.closing_checklist.errors import (
    FileMissing,
    FileTooLarge,
)
from controllership_finance_app.domain.closing_documents.file_validation import (
    MAX_FILE_BYTES,
)
from controllership_finance_app.infrastructure.storage.closing_document_storage import (
    ClosingDocumentStorage,
)


def test_write_temp_chunks_and_hash(tmp_path):
    storage = ClosingDocumentStorage(str(tmp_path))
    payload = b"abc" * 100_000
    tmp, digest, size = storage.write_temp(
        uuid.uuid4(), [payload[:100_000], payload[100_000:]]
    )
    assert tmp.exists() and tmp.suffix == ".part"
    assert size == len(payload)
    assert digest == hashlib.sha256(payload).hexdigest()


def test_write_temp_aborts_mid_stream_over_cap(tmp_path):
    storage = ClosingDocumentStorage(str(tmp_path))
    file_uuid = uuid.uuid4()
    chunk = b"x" * (MAX_FILE_BYTES // 2)
    with pytest.raises(FileTooLarge):
        storage.write_temp(file_uuid, [chunk, chunk, chunk, b"overflow"])
    assert not (tmp_path / ".tmp" / f"{file_uuid.hex}.part").exists()


def test_write_temp_removes_partial_on_error(tmp_path):
    storage = ClosingDocumentStorage(str(tmp_path))
    file_uuid = uuid.uuid4()

    def bad_chunks():
        yield b"data"
        raise RuntimeError("stream died")

    with pytest.raises(RuntimeError):
        storage.write_temp(file_uuid, bad_chunks())
    assert not (tmp_path / ".tmp" / f"{file_uuid.hex}.part").exists()


def test_publish_replaces_atomically(tmp_path):
    storage = ClosingDocumentStorage(str(tmp_path))
    file_uuid = uuid.uuid4()
    tmp, _digest, _size = storage.write_temp(file_uuid, [b"conteudo"])
    competence = str(uuid.uuid4())
    key, stored_name, final = storage.publish(
        tmp, competence_id=competence, file_uuid=file_uuid, extension=".pdf"
    )
    assert key == f"{competence}/{stored_name}"
    assert stored_name.endswith(".pdf")
    assert final.is_file()
    assert not tmp.exists()  # .part publicado (rename)


def test_resolve_and_traversal_guard(tmp_path):
    storage = ClosingDocumentStorage(str(tmp_path))
    file_uuid = uuid.uuid4()
    tmp, _d, _s = storage.write_temp(file_uuid, [b"data"])
    key, _name, final = storage.publish(
        tmp,
        competence_id=str(uuid.uuid4()),
        file_uuid=file_uuid,
        extension=".csv",
    )
    assert storage.resolve(key) == final
    for bad in ("../x", "a/../../b", ".tmp/anything.part", "", "/"):
        with pytest.raises(FileMissing):
            storage.resolve(bad)


def test_resolve_missing_file(tmp_path):
    storage = ClosingDocumentStorage(str(tmp_path))
    with pytest.raises(FileMissing):
        storage.resolve(f"{uuid.uuid4()}/{uuid.uuid4().hex}.pdf")


def test_remove_compensation(tmp_path):
    storage = ClosingDocumentStorage(str(tmp_path))
    file_uuid = uuid.uuid4()
    tmp, _d, _s = storage.write_temp(file_uuid, [b"data"])
    key, _n, final = storage.publish(
        tmp,
        competence_id=str(uuid.uuid4()),
        file_uuid=file_uuid,
        extension=".pdf",
    )
    assert storage.remove(key) is True
    assert not final.exists()
    # Idempotente na ausência — compensação repete sem erro.
    assert storage.remove(key) is True


def test_discard_temp(tmp_path):
    storage = ClosingDocumentStorage(str(tmp_path))
    file_uuid = uuid.uuid4()
    tmp, _d, _s = storage.write_temp(file_uuid, [b"data"])
    storage.discard_temp(file_uuid)
    assert not tmp.exists()
