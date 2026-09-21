from __future__ import annotations

import re

MAX_MESSAGE_LENGTH = 4000
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def normalize_uuid(value: str | None, *, label: str) -> str:
    identifier = (value or "").strip()
    if not _UUID_RE.match(identifier):
        raise ValueError(f"{label} precisa ser um identificador válido.")
    return identifier


def normalize_processo_id(value: str | None) -> str:
    return normalize_uuid(value, label="O processo")


def normalize_message_content(value: str | None) -> str:
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        raise ValueError("A mensagem não pode ficar em branco.")
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"A mensagem pode ter no máximo {MAX_MESSAGE_LENGTH} caracteres.")
    return text
