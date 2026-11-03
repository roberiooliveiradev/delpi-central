"""Sanitização de filename para transporte de documentos.

Fonte única usada pela borda HTTP (`Content-Disposition`) e pela
superfície MCP (metadata/recurso embutido). O nome vindo do upstream é
dado não confiável: separadores de path, aspas, CRLF e não-ASCII são
removidos — nunca escapados no header/campo de saída.
"""

from __future__ import annotations

import re

_FILENAME_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_pdf_filename(raw: str | None, *, fallback: str) -> str:
    """Filename seguro com extensão `.pdf` garantida.

    Fallback para o valor informado (ex.: código do produto) quando não
    sobra nome válido; último recurso ``drawing.pdf``."""
    name = (raw or "").rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    name = _FILENAME_UNSAFE.sub("_", name).strip("._ ")
    if not name:
        name = _FILENAME_UNSAFE.sub("_", fallback).strip("._ ") or "drawing"
    if not name.lower().endswith(".pdf"):
        name = f"{name}.pdf"
    return name
