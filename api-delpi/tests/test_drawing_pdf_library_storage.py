from __future__ import annotations

from pathlib import Path

import pytest

from app.application.services.drawings.drawing_pdf_library_storage import (
    DrawingPdfLibraryStorage,
    DrawingPdfLibraryStorageError,
)


@pytest.fixture()
def library_dir(tmp_path: Path) -> Path:
    drawings = tmp_path / "drawings"
    drawings.mkdir()
    (drawings / "90262957.pdf").write_bytes(b"%PDF-1.4 test")
    (drawings / "90264227.pdf").write_bytes(b"%PDF-1.4 base")
    (drawings / "90264227-1.pdf").write_bytes(b"%PDF-1.4 variant")
    (drawings / "90261040_R02.pdf").write_bytes(b"%PDF-1.4 revision")
    (drawings / "90261040_R10.pdf").write_bytes(b"%PDF-1.4 revision-10")
    return drawings


def test_find_drawing_exact_match(library_dir: Path) -> None:
    storage = DrawingPdfLibraryStorage(library_dir)
    match = storage.find_drawing("90262957")
    assert match is not None
    assert match.filename == "90262957.pdf"
    assert match.size_bytes > 0


def test_find_drawing_prefers_base_over_variant(library_dir: Path) -> None:
    storage = DrawingPdfLibraryStorage(library_dir)
    match = storage.find_drawing("90264227")
    assert match is not None
    assert match.filename == "90264227.pdf"


def test_find_drawing_variant_code(library_dir: Path) -> None:
    storage = DrawingPdfLibraryStorage(library_dir)
    match = storage.find_drawing("90264227-1")
    assert match is not None
    assert match.filename == "90264227-1.pdf"
    assert match.variant_suffix == "1"


def test_find_drawing_prefers_highest_revision(library_dir: Path) -> None:
    storage = DrawingPdfLibraryStorage(library_dir)
    match = storage.find_drawing("90261040")
    assert match is not None
    assert match.filename == "90261040_R10.pdf"
    assert match.revision == "10"


def test_find_drawing_not_found(library_dir: Path) -> None:
    storage = DrawingPdfLibraryStorage(library_dir)
    assert storage.find_drawing("99999999") is None


def test_normalize_product_code_rejects_path_traversal(library_dir: Path) -> None:
    storage = DrawingPdfLibraryStorage(library_dir)
    with pytest.raises(DrawingPdfLibraryStorageError):
        storage.normalize_product_code("../90262957")


def test_resolve_pdf_path_returns_file(library_dir: Path) -> None:
    storage = DrawingPdfLibraryStorage(library_dir)
    path = storage.resolve_pdf_path("90262957")
    assert path.is_file()
    assert path.name == "90262957.pdf"
