"""Validação de slug e limites de conteúdo — Guias e Procedimentos."""

from __future__ import annotations

import re
import unicodedata

from app.domain.services.guias_procedimentos.exceptions import GuiasValidationError

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

DEPARTMENT_NAME_MAX = 200
DEPARTMENT_SLUG_MAX = 120
DEPARTMENT_DESCRIPTION_MAX = 4000
DEPARTMENT_ICON_MAX = 64

PROCEDURE_TITLE_MAX = 500
PROCEDURE_SLUG_MAX = 160
PROCEDURE_SUMMARY_MAX = 4000
PROCEDURE_HTML_MAX = 200_000
READING_TIME_MAX = 480

SLUG_MIN_LENGTH = 2


def normalize_optional_text(value: object | None, *, field: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise GuiasValidationError(f"{field} deve ser string.")
    return value.strip()


def require_non_empty_text(
    value: object | None,
    *,
    field: str,
    max_length: int,
) -> str:
    text = normalize_optional_text(value, field=field)
    if not text:
        raise GuiasValidationError(f"{field} é obrigatório.")
    if len(text) > max_length:
        raise GuiasValidationError(
            f"{field} deve ter no máximo {max_length} caracteres."
        )
    return text


def validate_slug(raw: object | None, *, field: str = "slug", max_length: int) -> str:
    if not isinstance(raw, str):
        raise GuiasValidationError(f"{field} deve ser string.")
    slug = raw.strip().lower()
    if not slug:
        raise GuiasValidationError(f"{field} é obrigatório.")
    if len(slug) < SLUG_MIN_LENGTH:
        raise GuiasValidationError(
            f"{field} deve ter ao menos {SLUG_MIN_LENGTH} caracteres."
        )
    if len(slug) > max_length:
        raise GuiasValidationError(
            f"{field} deve ter no máximo {max_length} caracteres."
        )
    if any(ch.isspace() for ch in slug):
        raise GuiasValidationError(f"{field} não pode conter espaços.")
    if "_" in slug or "/" in slug:
        raise GuiasValidationError(
            f"{field} deve usar apenas letras minúsculas, números e hífens."
        )
    normalized = unicodedata.normalize("NFKD", slug)
    if any(ord(ch) > 127 for ch in normalized):
        raise GuiasValidationError(f"{field} não pode conter acentos.")
    if not SLUG_PATTERN.fullmatch(slug):
        raise GuiasValidationError(
            f"{field} inválido. Use apenas a-z, 0-9 e hífens "
            "(sem começar/terminar com hífen nem hífens consecutivos)."
        )
    return slug


def validate_order_index(value: object | None, *, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise GuiasValidationError("order_index deve ser inteiro.")
    if value < 0:
        raise GuiasValidationError("order_index não pode ser negativo.")
    return value


def validate_reading_time_minutes(value: object | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise GuiasValidationError("reading_time_minutes deve ser inteiro.")
    if value < 1:
        raise GuiasValidationError("reading_time_minutes deve ser positivo.")
    if value > READING_TIME_MAX:
        raise GuiasValidationError(
            f"reading_time_minutes deve ser no máximo {READING_TIME_MAX}."
        )
    return value


def validate_icon(value: object | None, *, default: str = "book-open") -> str:
    if value is None:
        return default
    icon = require_non_empty_text(
        value, field="icon", max_length=DEPARTMENT_ICON_MAX
    )
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", icon):
        raise GuiasValidationError(
            "icon deve ser identificador curto em kebab-case (ex.: receipt)."
        )
    return icon


def validate_content_html_length(html: str) -> str:
    if len(html) > PROCEDURE_HTML_MAX:
        raise GuiasValidationError(
            f"content_html deve ter no máximo {PROCEDURE_HTML_MAX} caracteres."
        )
    return html
