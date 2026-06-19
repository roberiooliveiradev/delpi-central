"""Fixtures de PDF de desenho — caminho canônico e pré-requisitos de extração live."""

from __future__ import annotations

from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[2]
DRAWING_PDF_DIR = _API_ROOT / "desenhos"


def drawing_pdf_path(filename: str) -> Path:
    return DRAWING_PDF_DIR / filename


def require_drawing_pdf(filename: str) -> Path:
    path = drawing_pdf_path(filename)

    if not path.is_file():
        pytest.skip(f"fixture PDF ausente: {path}")

    return path


def require_tesseract() -> None:
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
    except Exception as exc:
        pytest.skip(f"Tesseract indisponível: {exc}")


def require_drawing_pdf_with_tesseract(filename: str) -> Path:
    require_tesseract()
    return require_drawing_pdf(filename)


def assert_component_codes(
    parsed: dict,
    *,
    required: set[str],
    forbidden: set[str] | None = None,
) -> None:
    codes = set(parsed.get("componentCodes") or [])
    missing = required - codes
    assert not missing, f"códigos ausentes: {sorted(missing)}; obtidos: {sorted(codes)}"
    if forbidden:
        unexpected = forbidden & codes
        assert not unexpected, f"códigos proibidos: {sorted(unexpected)}"
