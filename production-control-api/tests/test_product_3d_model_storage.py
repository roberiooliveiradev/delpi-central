from __future__ import annotations

from pathlib import Path

import pytest

from production_control_app.domain.errors import Product3DModelInvalid, Product3DModelNotFound
from production_control_app.infrastructure.storage.product_3d_model_storage import (
    Product3DModelFilesystemStorage,
)


def test_write_and_read_glb_bytes(tmp_path: Path) -> None:
    storage = Product3DModelFilesystemStorage(tmp_path)
    payload = b"glTF" + b"\x02\x00\x00\x00test-model"

    filename = storage.write_glb(product_code="50320064", payload=payload)

    assert filename == "50320064.glb"
    path = Path(storage.resolve_glb(stored_filename=filename))
    assert path.read_bytes() == payload


def test_write_normalizes_product_code(tmp_path: Path) -> None:
    storage = Product3DModelFilesystemStorage(tmp_path)

    filename = storage.write_glb(product_code=" 90262957 ", payload=b"glTFxx")

    assert filename == "90262957.glb"
    assert (tmp_path / "90262957.glb").is_file()


def test_rejects_invalid_product_code(tmp_path: Path) -> None:
    storage = Product3DModelFilesystemStorage(tmp_path)

    with pytest.raises(Product3DModelInvalid):
        storage.write_glb(product_code="../etc/passwd", payload=b"glTF")


def test_missing_file_is_not_found(tmp_path: Path) -> None:
    storage = Product3DModelFilesystemStorage(tmp_path)

    with pytest.raises(Product3DModelNotFound):
        storage.resolve_glb(stored_filename="50320064.glb")


def test_delete_removes_bytes(tmp_path: Path) -> None:
    storage = Product3DModelFilesystemStorage(tmp_path)
    filename = storage.write_glb(product_code="50320064", payload=b"glTFxx")

    storage.delete_glb(stored_filename=filename)

    assert not (tmp_path / filename).exists()
