"""Validação de URL de destino do mural."""

from __future__ import annotations

from urllib.parse import urlparse

from app.domain.services.mural_acessos.exceptions import MuralAcessosValidationError

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_MAX_URL_LEN = 2000
_MIN_TITLE_LEN = 1
_MAX_TITLE_LEN = 80
_MAX_DESCRIPTION_LEN = 240
_MAX_SUBTITLE_LEN = 160
_MIN_TOKEN_LEN = 2
_MAX_TOKEN_LEN = 40


def normalize_title(value: str | None) -> str:
    title = " ".join((value or "").split())
    if len(title) < _MIN_TITLE_LEN:
        raise MuralAcessosValidationError("Informe o título do acesso.")
    if len(title) > _MAX_TITLE_LEN:
        raise MuralAcessosValidationError("O título deve ter no máximo 80 caracteres.")
    return title


def normalize_description(value: str | None) -> str:
    description = " ".join((value or "").split())
    if len(description) > _MAX_DESCRIPTION_LEN:
        raise MuralAcessosValidationError(
            "A descrição deve ter no máximo 240 caracteres."
        )
    return description


def normalize_subtitle(value: str | None) -> str:
    subtitle = " ".join((value or "").split())
    if len(subtitle) > _MAX_SUBTITLE_LEN:
        raise MuralAcessosValidationError(
            "O subtítulo deve ter no máximo 160 caracteres."
        )
    return subtitle


def normalize_link_url(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        raise MuralAcessosValidationError("Informe o link de destino.")
    if len(raw) > _MAX_URL_LEN:
        raise MuralAcessosValidationError("O link é muito longo.")

    parsed = urlparse(raw)
    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise MuralAcessosValidationError("O link deve começar com http:// ou https://.")
    if not (parsed.netloc or "").strip():
        raise MuralAcessosValidationError("Informe um link válido.")
    return raw


def normalize_public_token(value: str | None) -> str:
    raw = (value or "").strip().lower()
    pieces: list[str] = []
    hyphen_pending = False
    for char in raw:
        if ("a" <= char <= "z") or ("0" <= char <= "9"):
            if hyphen_pending and pieces:
                pieces.append("-")
            pieces.append(char)
            hyphen_pending = False
        elif char in " -_.":
            hyphen_pending = True
    token = "".join(pieces)
    if len(token) < _MIN_TOKEN_LEN:
        raise MuralAcessosValidationError(
            "Informe um identificador público com pelo menos 2 caracteres."
        )
    if len(token) > _MAX_TOKEN_LEN:
        raise MuralAcessosValidationError(
            "O identificador público deve ter no máximo 40 caracteres."
        )
    return token
