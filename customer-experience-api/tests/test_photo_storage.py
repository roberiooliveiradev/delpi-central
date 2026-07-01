import pytest

from cx_app.application.services.photo_storage import PhotoStorage, PhotoValidationError

_PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def test_rejects_unsupported_mime(tmp_path):
    storage = PhotoStorage(base_dir=str(tmp_path))
    with pytest.raises(PhotoValidationError):
        storage.validate(content=_PNG, mime_type="application/pdf")


def test_rejects_empty_content(tmp_path):
    storage = PhotoStorage(base_dir=str(tmp_path))
    with pytest.raises(PhotoValidationError):
        storage.validate(content=b"", mime_type="image/png")


def test_save_and_read_roundtrip(tmp_path):
    storage = PhotoStorage(base_dir=str(tmp_path))
    filename, mime = storage.save(content=_PNG, mime_type="image/png")
    assert filename.endswith(".png")
    assert mime == "image/png"
    assert storage.read(filename) == _PNG


def test_delete_removes_file(tmp_path):
    storage = PhotoStorage(base_dir=str(tmp_path))
    filename, _ = storage.save(content=_PNG, mime_type="image/png")
    storage.delete(filename)
    assert storage.read(filename) is None
