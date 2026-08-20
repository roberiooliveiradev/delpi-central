"""Decodificação UTF-8 explícita para streams HTTP de LLM.

Sem charset no Content-Type, o requests assume ISO-8859-1 em
`iter_lines(decode_unicode=True)` e transforma UTF-8 válido em mojibake
(ex.: «até» → «atÃ©»). Sempre decodificar bytes como UTF-8.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any


def force_response_utf8(response: Any) -> None:
    """Garante que response.text / decode_unicode usem UTF-8."""
    try:
        response.encoding = "utf-8"
    except Exception:  # noqa: BLE001 — resposta mock / sem encoding mutável
        pass


def decode_stream_line(raw: bytes | str | None) -> str | None:
    if raw is None or raw == b"" or raw == "":
        return None

    if isinstance(raw, bytes):
        return raw.decode("utf-8")

    text = str(raw)
    return repair_utf8_mojibake(text)


def repair_utf8_mojibake(text: str) -> str:
    """Reverte UTF-8 lido como Latin-1 (Ã© → é) quando o padrão bate."""
    if not text or "Ã" not in text and "Â" not in text:
        return text

    try:
        repaired = text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

    if repaired.count("Ã") + repaired.count("Â") < text.count("Ã") + text.count("Â"):
        return repaired

    return text


def iter_utf8_lines(response: Any) -> Iterator[str]:
    force_response_utf8(response)

    for raw in response.iter_lines(decode_unicode=False):
        line = decode_stream_line(raw)

        if line is None:
            continue

        yield line
