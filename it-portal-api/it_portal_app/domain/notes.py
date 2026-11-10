"""Notas técnicas — somente criação e leitura; autoria vem da sessão."""

from __future__ import annotations

from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.secret_guard import ensure_no_secret

NOTE_MAX = 4000


def build_note_body(raw_body: object) -> str:
    body = str(raw_body).strip() if raw_body is not None else ""
    if not body:
        raise ValidationError(
            "invalid_note",
            "Escreva o conteúdo da nota.",
            {"fields": {"body": "Escreva o conteúdo da nota."}},
        )
    if len(body) > NOTE_MAX:
        raise ValidationError(
            "invalid_note",
            f"A nota pode ter no máximo {NOTE_MAX} caracteres.",
            {"fields": {"body": f"Use no máximo {NOTE_MAX} caracteres."}},
        )
    ensure_no_secret("body", body)
    return body
