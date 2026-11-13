"""Regras puras para o cadastro de estacoes de trabalho (G1-DOM).

Este modulo nao instala agentes, nao abre sessoes e nao concede controle remoto.
A identidade persistente do agente sera definida em outra camada no G2.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from uuid import UUID

from it_portal_app.domain.catalogs import ADMINISTRATIVE_STATUSES, UNIT_CODES
from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.secret_guard import ensure_no_secret
from it_portal_app.domain.servers import is_valid_hostname, normalize_hostname, normalize_ip

DEVICE_KINDS = ("desktop", "notebook", "mini_pc", "workstation")
WORKSTATION_CODE_PREFIX = "PC-"

NAME_MAX = 120
DEPARTMENT_MAX = 120
LOCATION_MAX = 160
RESPONSIBLE_MAX = 160
OS_MAX = 120
DESCRIPTION_MAX = 4000


def format_workstation_code(seq: int) -> str:
    """Codigo humano derivado da sequencia, sem ser identidade de seguranca."""
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
        raise ValueError("A sequencia da estacao deve ser um inteiro positivo.")
    return f"{WORKSTATION_CODE_PREFIX}{seq:04d}"


@dataclass(frozen=True)
class WorkstationFields:
    name: str
    hostname: str
    ip_address: str | None
    unit_code: str
    device_kind: str
    department: str | None
    location: str | None
    responsible: str | None
    responsible_user_id: str | None
    operating_system: str | None
    administrative_status: str
    description: str | None

    def as_dict(self) -> dict:
        return asdict(self)


def _clean(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _optional(raw: dict, key: str, limit: int, errors: dict[str, str]) -> str | None:
    value = _clean(raw.get(key))
    if not value:
        return None
    if len(value) > limit:
        errors[key] = f"Use no maximo {limit} caracteres."
    return value


def build_workstation_fields(raw: dict) -> WorkstationFields:
    """Valida dados curados de uma estacao, sem habilitar qualquer acesso remoto."""
    errors: dict[str, str] = {}

    name = _clean(raw.get("name"))
    if not name:
        errors["name"] = "Informe o nome da estacao."
    elif len(name) > NAME_MAX:
        errors["name"] = f"Use no maximo {NAME_MAX} caracteres."

    hostname = normalize_hostname(raw.get("hostname"))
    if not is_valid_hostname(hostname):
        errors["hostname"] = "Informe um hostname valido."

    try:
        ip_address = normalize_ip(raw.get("ip_address"))
    except ValueError:
        ip_address = None
        errors["ip_address"] = "Endereco IP invalido (IPv4 ou IPv6)."

    unit_code = _clean(raw.get("unit_code"))
    if unit_code not in UNIT_CODES:
        errors["unit_code"] = "Selecione a unidade da estacao."

    device_kind = _clean(raw.get("device_kind"))
    if device_kind not in DEVICE_KINDS:
        errors["device_kind"] = "Selecione o tipo de estacao."

    status = _clean(raw.get("administrative_status"))
    if status not in ADMINISTRATIVE_STATUSES:
        errors["administrative_status"] = "Selecione uma situacao valida."

    department = _optional(raw, "department", DEPARTMENT_MAX, errors)
    location = _optional(raw, "location", LOCATION_MAX, errors)
    responsible = _optional(raw, "responsible", RESPONSIBLE_MAX, errors)
    raw_owner_id = _clean(raw.get("responsible_user_id"))
    responsible_user_id = None
    if raw_owner_id:
        try:
            normalized_owner_id = UUID(raw_owner_id)
            if normalized_owner_id.int == 0:
                raise ValueError("zero UUID")
            responsible_user_id = str(normalized_owner_id)
        except (ValueError, AttributeError):
            errors["responsible_user_id"] = "Selecione um usuario valido do Core."
    operating_system = _optional(raw, "operating_system", OS_MAX, errors)
    description = _optional(raw, "description", DESCRIPTION_MAX, errors)

    if errors:
        raise ValidationError(
            "invalid_workstation",
            "Revise os campos destacados da estacao.",
            {"fields": errors},
        )

    for key, value in (
        ("name", name),
        ("operating_system", operating_system),
        ("department", department),
        ("location", location),
        ("responsible", responsible),
        ("description", description),
    ):
        ensure_no_secret(key, value)

    return WorkstationFields(
        name=name,
        hostname=hostname,
        ip_address=ip_address,
        unit_code=unit_code,
        device_kind=device_kind,
        department=department,
        location=location,
        responsible=responsible,
        responsible_user_id=responsible_user_id,
        operating_system=operating_system,
        administrative_status=status,
        description=description,
    )


WORKSTATION_FIELD_NAMES = tuple(WorkstationFields.__dataclass_fields__.keys())
