from __future__ import annotations

from pathlib import Path

import pytest

from production_control_app.domain.errors import DrawingNotFound
from production_control_app.infrastructure.storage.drawing_pdf_library_storage import (
    DrawingPdfLibraryStorage,
)


def _library(tmp_path: Path, *filenames: str) -> DrawingPdfLibraryStorage:
    for name in filenames:
        (tmp_path / name).write_bytes(b"%PDF-1.4 test")
    return DrawingPdfLibraryStorage(tmp_path)


def test_resolves_exact_filename(tmp_path: Path) -> None:
    storage = _library(tmp_path, "90262957.pdf", "90262957_R02.pdf")

    drawing = storage.resolve_pdf("90262957")

    assert drawing.filename == "90262957.pdf"
    assert drawing.path == (tmp_path / "90262957.pdf").resolve()


def test_prefers_base_over_variant(tmp_path: Path) -> None:
    storage = _library(tmp_path, "90262957.pdf", "90262957-2.pdf")

    assert storage.resolve_pdf("90262957-5").filename == "90262957.pdf"


def test_picks_highest_revision(tmp_path: Path) -> None:
    storage = _library(tmp_path, "90262957_R01.pdf", "90262957_R10.pdf", "90262957_R03.pdf")

    assert storage.resolve_pdf("90262957").filename == "90262957_R10.pdf"


def test_resolves_explicit_variant(tmp_path: Path) -> None:
    storage = _library(tmp_path, "90262957-1.pdf", "90262957-2.pdf")

    assert storage.resolve_pdf("90262957-2").filename == "90262957-2.pdf"


def test_missing_drawing_is_distinct_from_missing_library(tmp_path: Path) -> None:
    storage = _library(tmp_path, "90262957.pdf")

    with pytest.raises(DrawingNotFound, match="não encontrado"):
        storage.resolve_pdf("11111111")


def test_library_not_mounted_is_explicit(tmp_path: Path) -> None:
    storage = DrawingPdfLibraryStorage(tmp_path / "ausente")

    with pytest.raises(DrawingNotFound, match="não montada"):
        storage.resolve_pdf("90262957")


def test_empty_library_is_explicit(tmp_path: Path) -> None:
    storage = DrawingPdfLibraryStorage(tmp_path)

    with pytest.raises(DrawingNotFound, match="vazia"):
        storage.resolve_pdf("90262957")


def test_rejects_path_traversal(tmp_path: Path) -> None:
    storage = _library(tmp_path, "90262957.pdf")

    with pytest.raises(DrawingNotFound, match="inválido"):
        storage.resolve_pdf("../etc/passwd")


def test_uses_injected_messages(tmp_path: Path) -> None:
    storage = DrawingPdfLibraryStorage(
        tmp_path,
        message=lambda key, default: "pasta vazia no servidor"
        if key == "drawingLibraryEmpty"
        else default,
    )

    with pytest.raises(DrawingNotFound, match="pasta vazia no servidor"):
        storage.resolve_pdf("90262957")
