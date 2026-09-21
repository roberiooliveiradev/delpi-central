from __future__ import annotations

import re

from tm_app.domain.services.interaction_room_rules import normalize_processo_id, normalize_uuid
from tm_app.domain.services.transformometro_task_rules import normalize_user_id

MAX_TITLE_LENGTH = 200
MAX_CONTENT_MD_LENGTH = 200_000

_TITLE_BLANK_RE = re.compile(r"\s+")


def normalize_document_id(value: str | None) -> str:
    return normalize_uuid(value, label="O documento")


def normalize_document_title(value: str | None) -> str:
    title = _TITLE_BLANK_RE.sub(" ", (value or "").strip())
    if not title:
        raise ValueError("O título não pode ficar em branco.")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError(f"O título pode ter no máximo {MAX_TITLE_LENGTH} caracteres.")
    return title


def normalize_document_content_md(value: str | None) -> str:
    """Persiste o source Markdown. Conteúdo vazio é permitido (rascunho sem workflow)."""
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    if len(text) > MAX_CONTENT_MD_LENGTH:
        raise ValueError(
            f"O conteúdo Markdown pode ter no máximo {MAX_CONTENT_MD_LENGTH} caracteres."
        )
    return text


def normalize_document_actor(user_id: str | None) -> str:
    return normalize_user_id(user_id, field="Usuário autenticado")


__all__ = [
    "MAX_CONTENT_MD_LENGTH",
    "MAX_TITLE_LENGTH",
    "normalize_document_actor",
    "normalize_document_content_md",
    "normalize_document_id",
    "normalize_document_title",
    "normalize_processo_id",
]
