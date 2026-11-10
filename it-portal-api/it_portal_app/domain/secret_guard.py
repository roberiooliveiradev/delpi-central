"""Bloqueia credenciais em texto livre (notas, descrições).

O inventário é consultado por várias pessoas; senhas, tokens e chaves têm
cofre próprio. A detecção é conservadora: exige um *valor* atribuído a um
rótulo de segredo ou um formato inequívoco de credencial — mencionar a
palavra "senha" numa frase não ativa o bloqueio.
"""

from __future__ import annotations

import re

from it_portal_app.domain.errors import ValidationError

_LABELLED_SECRET = re.compile(
    r"\b(senha|password|passwd|pwd|secret|segredo|token|api[_-]?key|"
    r"client[_-]?secret|access[_-]?key)\b\s*[:=]\s*\S{4,}",
    re.IGNORECASE,
)
_PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")
_AWS_ACCESS_KEY = re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")
_URL_CREDENTIALS = re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@", re.IGNORECASE)

_PATTERNS = (_LABELLED_SECRET, _PRIVATE_KEY, _JWT, _AWS_ACCESS_KEY, _URL_CREDENTIALS)


def contains_secret(text: str | None) -> bool:
    if not text:
        return False
    return any(pattern.search(text) for pattern in _PATTERNS)


def ensure_no_secret(field: str, text: str | None) -> None:
    if contains_secret(text):
        raise ValidationError(
            "secret_not_allowed",
            "O texto parece conter uma senha, token ou chave. Registre "
            "credenciais apenas no cofre de senhas oficial.",
            {"field": field},
        )
