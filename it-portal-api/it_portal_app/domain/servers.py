"""Regras do cadastro de servidores — normalização e validação de entrada."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import asdict, dataclass

from it_portal_app.domain.catalogs import (
    ADMINISTRATIVE_STATUSES,
    CRITICALITIES,
    ENVIRONMENTS,
    SERVER_TYPES,
    UNIT_CODES,
)
from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.secret_guard import ensure_no_secret

# RFC 1123: rótulos alfanuméricos com hífen interno, até 63 chars; FQDN até 253.
_HOSTNAME_LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")

NAME_MAX = 120
LOCATION_MAX = 160
PURPOSE_MAX = 160
OS_MAX = 120
RESPONSIBLE_MAX = 160
DESCRIPTION_MAX = 4000

SERVER_CODE_PREFIX = "SRV-"


def format_server_code(seq: int) -> str:
    return f"{SERVER_CODE_PREFIX}{seq:04d}"


@dataclass(frozen=True)
class ServerFields:
    name: str
    hostname: str
    ip_address: str | None
    unit_code: str
    location: str | None
    environment: str
    server_type: str
    purpose: str | None
    operating_system: str | None
    criticality: str
    administrative_status: str
    responsible: str | None
    description: str | None

    def as_dict(self) -> dict:
        return asdict(self)


def _clean(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _optional(value: object, field: str, max_len: int, errors: dict) -> str | None:
    cleaned = _clean(value)
    if not cleaned:
        return None
    if len(cleaned) > max_len:
        errors[field] = f"Use no máximo {max_len} caracteres."
    return cleaned


def normalize_hostname(value: object) -> str:
    return _clean(value).lower().rstrip(".")


def is_valid_hostname(hostname: str) -> bool:
    if not hostname or len(hostname) > 253:
        return False
    return all(_HOSTNAME_LABEL.match(label) for label in hostname.split("."))


def normalize_ip(value: object) -> str | None:
    cleaned = _clean(value)
    if not cleaned:
        return None
    return str(ipaddress.ip_address(cleaned))


def build_server_fields(raw: dict) -> ServerFields:
    """Valida o payload completo; reporta todos os campos inválidos de uma vez."""
    errors: dict[str, str] = {}

    name = _clean(raw.get("name"))
    if not name:
        errors["name"] = "Informe o nome do servidor."
    elif len(name) > NAME_MAX:
        errors["name"] = f"Use no máximo {NAME_MAX} caracteres."

    hostname = normalize_hostname(raw.get("hostname"))
    if not hostname:
        errors["hostname"] = "Informe o hostname."
    elif not is_valid_hostname(hostname):
        errors["hostname"] = (
            "Hostname inválido: use letras, números, hífen e pontos "
            "(ex.: srv-app01 ou srv-app01.delpi.local)."
        )

    ip_address: str | None = None
    try:
        ip_address = normalize_ip(raw.get("ip_address"))
    except ValueError:
        errors["ip_address"] = "Endereço IP inválido (IPv4 ou IPv6)."

    def _enum(field: str, allowed: tuple[str, ...], message: str) -> str:
        value = _clean(raw.get(field))
        if value not in allowed:
            errors[field] = message
        return value

    unit_code = _enum("unit_code", UNIT_CODES, "Selecione a unidade.")
    environment = _enum("environment", ENVIRONMENTS, "Selecione o ambiente.")
    server_type = _enum("server_type", SERVER_TYPES, "Selecione o tipo do servidor.")
    criticality = _enum("criticality", CRITICALITIES, "Selecione a criticidade.")
    administrative_status = _enum(
        "administrative_status",
        ADMINISTRATIVE_STATUSES,
        "Selecione a situação administrativa.",
    )

    location = _optional(raw.get("location"), "location", LOCATION_MAX, errors)
    purpose = _optional(raw.get("purpose"), "purpose", PURPOSE_MAX, errors)
    operating_system = _optional(
        raw.get("operating_system"), "operating_system", OS_MAX, errors
    )
    responsible = _optional(raw.get("responsible"), "responsible", RESPONSIBLE_MAX, errors)
    description = _optional(raw.get("description"), "description", DESCRIPTION_MAX, errors)

    if errors:
        raise ValidationError(
            "invalid_server",
            "Revise os campos destacados do servidor.",
            {"fields": errors},
        )

    ensure_no_secret("description", description)

    return ServerFields(
        name=name,
        hostname=hostname,
        ip_address=ip_address,
        unit_code=unit_code,
        location=location,
        environment=environment,
        server_type=server_type,
        purpose=purpose,
        operating_system=operating_system,
        criticality=criticality,
        administrative_status=administrative_status,
        responsible=responsible,
        description=description,
    )


def diff_fields(before: dict, after: dict, fields: tuple[str, ...]) -> dict:
    """Mudanças campo a campo para a trilha de auditoria."""
    return {
        field: {"from": before.get(field), "to": after.get(field)}
        for field in fields
        if before.get(field) != after.get(field)
    }


SERVER_FIELD_NAMES = tuple(ServerFields.__dataclass_fields__.keys())
