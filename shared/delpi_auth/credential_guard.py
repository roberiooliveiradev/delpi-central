"""Validação de credenciais fracas no startup (LGPD Art. 46).

Impede que a aplicação inicie em modo de produção com senhas triviais
ou tokens de serviço inseguros. Em desenvolvimento, emite warnings.
"""

from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger("delpi_auth.credential_guard")

_WEAK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(.)\1*$"),                  # aaaa, 1111
    re.compile(r"^(password|senha|123|abc)", re.I),
    re.compile(r"^(admin|root|test|default)", re.I),
    re.compile(r"^changeme$", re.I),
    re.compile(r"^(qwerty|letmein|welcome)", re.I),
]

MIN_LENGTH = 12

_ENV_VARS_TO_CHECK = [
    "POSTGRES_CORE_PASSWORD",
    "POSTGRES_KC_PASSWORD",
    "PLUGINS_DB_PASSWORD",
    "API_DELPI_INTERNAL_SERVICE_TOKEN",
    "CORE_API_INTEGRATIONS_SERVICE_TOKEN",
    "KEYCLOAK_ADMIN_PASSWORD",
]


def _is_weak(value: str) -> str | None:
    """Retorna motivo se a credencial for considerada fraca, ou None."""
    if len(value) < MIN_LENGTH:
        return f"comprimento {len(value)} < mínimo {MIN_LENGTH}"
    for pattern in _WEAK_PATTERNS:
        if pattern.search(value):
            return f"padrão fraco detectado ({pattern.pattern})"
    return None


def check_credentials(
    *,
    extra_vars: list[str] | None = None,
    strict: bool | None = None,
) -> list[str]:
    """Valida variáveis de ambiente com credenciais.

    Args:
        extra_vars: variáveis adicionais a verificar além das padrão.
        strict: se True, levanta RuntimeError em caso de falha.
                Se None, auto-detecta: strict quando FLASK_ENV/APP_ENV == production.

    Returns:
        Lista de warnings encontrados (vazia = OK).
    """
    if strict is None:
        env = os.getenv("FLASK_ENV", os.getenv("APP_ENV", "development")).lower()
        strict = env == "production"

    vars_to_check = list(_ENV_VARS_TO_CHECK)
    if extra_vars:
        vars_to_check.extend(extra_vars)

    warnings: list[str] = []

    for var_name in vars_to_check:
        value = (os.getenv(var_name) or "").strip()
        if not value:
            continue
        reason = _is_weak(value)
        if reason:
            msg = f"Credencial fraca em {var_name}: {reason}"
            warnings.append(msg)

    if warnings:
        for w in warnings:
            logger.warning("LGPD credential-guard: %s", w)
        if strict:
            raise RuntimeError(
                "Credenciais fracas detectadas em produção (LGPD Art. 46). "
                "Corrija as seguintes variáveis: "
                + ", ".join(v.split(":")[0].split()[-1] for v in warnings)
            )

    return warnings
