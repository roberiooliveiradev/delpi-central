"""Validação de campos compartilhada pelos cadastros do inventário (E2A+).

Acumula erros por campo em `errors` para que o cliente receba todos de uma vez.
"""

from __future__ import annotations

import uuid

PORT_MIN = 1
PORT_MAX = 65535


def clean(value: object) -> str:
    return str(value).strip() if value is not None else ""


def required_text(raw: dict, field: str, max_len: int, message: str, errors: dict) -> str:
    value = clean(raw.get(field))
    if not value:
        errors[field] = message
    elif len(value) > max_len:
        errors[field] = f"Use no máximo {max_len} caracteres."
    return value


def optional_text(raw: dict, field: str, max_len: int, errors: dict) -> str | None:
    value = clean(raw.get(field))
    if not value:
        return None
    if len(value) > max_len:
        errors[field] = f"Use no máximo {max_len} caracteres."
    return value


def choice(raw: dict, field: str, allowed: tuple[str, ...], message: str, errors: dict) -> str:
    value = clean(raw.get(field))
    if value not in allowed:
        errors[field] = message
    return value


def optional_port(raw: dict, field: str, errors: dict) -> int | None:
    value = raw.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        errors[field] = "Porta inválida."
        return None
    try:
        port = int(str(value).strip())
    except ValueError:
        errors[field] = f"Informe uma porta entre {PORT_MIN} e {PORT_MAX}."
        return None
    if not PORT_MIN <= port <= PORT_MAX:
        errors[field] = f"Informe uma porta entre {PORT_MIN} e {PORT_MAX}."
        return None
    return port


def required_uuid(raw: dict, field: str, message: str, errors: dict) -> str:
    value = clean(raw.get(field))
    try:
        return str(uuid.UUID(value))
    except ValueError:
        errors[field] = message
        return value
