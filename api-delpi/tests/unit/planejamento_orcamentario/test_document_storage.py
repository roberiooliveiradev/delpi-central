import pytest

from app.application.services.planejamento_orcamentario.document_storage import (
    BudgetDocumentStorage,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetDocumentTooLargeError,
    BudgetDocumentTypeNotAllowedError,
)


def test_reject_bad_mime(tmp_path):
    storage = BudgetDocumentStorage(base_dir=str(tmp_path))
    with pytest.raises(BudgetDocumentTypeNotAllowedError):
        storage.validate_upload(
            mime_type="application/x-msdownload",
            size_bytes=10,
            original_name="virus.exe",
        )


def test_reject_too_large(tmp_path):
    storage = BudgetDocumentStorage(base_dir=str(tmp_path))
    with pytest.raises(BudgetDocumentTooLargeError):
        storage.validate_upload(
            mime_type="application/pdf",
            size_bytes=26 * 1024 * 1024,
            original_name="big.pdf",
        )


def test_save_and_resolve(tmp_path):
    storage = BudgetDocumentStorage(base_dir=str(tmp_path))
    key, kind = storage.save(
        exercise_id="ex1",
        original_name="carta.pdf",
        content=b"%PDF-1.4",
        mime_type="application/pdf",
    )
    assert kind == "pdf"
    path = storage.resolve_file(exercise_id="ex1", storage_key=key)
    assert path.read_bytes().startswith(b"%PDF")


def test_path_traversal_blocked(tmp_path):
    storage = BudgetDocumentStorage(base_dir=str(tmp_path))
    with pytest.raises(BudgetDocumentTypeNotAllowedError):
        storage.resolve_file(exercise_id="ex1", storage_key="../secret")
