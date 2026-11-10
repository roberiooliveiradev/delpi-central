"""Inventário de instâncias de banco de dados — normalização e validação.

Nenhum campo aceita credenciais: usuários, senhas e strings de conexão com
segredo ficam no cofre corporativo (bloqueados pelo `secret_guard`).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from it_portal_app.domain.catalogs import (
    ADMINISTRATIVE_STATUSES,
    CRITICALITIES,
    DBMS_ENGINES,
    ENVIRONMENTS,
)
from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.field_rules import (
    choice,
    optional_port,
    optional_text,
    required_text,
    required_uuid,
)
from it_portal_app.domain.secret_guard import ensure_no_secret

NAME_MAX = 120
VERSION_MAX = 60
PURPOSE_MAX = 160
RESPONSIBLE_MAX = 160
NOTES_MAX = 4000

DATABASE_CODE_PREFIX = "DB-"


def format_database_code(seq: int) -> str:
    return f"{DATABASE_CODE_PREFIX}{seq:04d}"


@dataclass(frozen=True)
class DatabaseInstanceFields:
    name: str
    dbms: str
    version: str | None
    server_id: str
    port: int | None
    environment: str
    purpose: str | None
    criticality: str
    responsible: str
    administrative_status: str
    technical_notes: str | None

    def as_dict(self) -> dict:
        return asdict(self)


DATABASE_FIELD_NAMES = tuple(DatabaseInstanceFields.__dataclass_fields__.keys())


def build_database_fields(raw: dict) -> DatabaseInstanceFields:
    errors: dict[str, str] = {}
    name = required_text(raw, "name", NAME_MAX, "Informe o nome da instância.", errors)
    dbms = choice(raw, "dbms", DBMS_ENGINES, "Selecione o SGBD.", errors)
    version = optional_text(raw, "version", VERSION_MAX, errors)
    server_id = required_uuid(raw, "server_id", "Selecione o servidor hospedeiro.", errors)
    port = optional_port(raw, "port", errors)
    environment = choice(raw, "environment", ENVIRONMENTS, "Selecione o ambiente.", errors)
    purpose = optional_text(raw, "purpose", PURPOSE_MAX, errors)
    criticality = choice(raw, "criticality", CRITICALITIES, "Selecione a criticidade.", errors)
    responsible = required_text(
        raw, "responsible", RESPONSIBLE_MAX, "Informe o responsável pela instância.", errors
    )
    administrative_status = choice(
        raw,
        "administrative_status",
        ADMINISTRATIVE_STATUSES,
        "Selecione a situação administrativa.",
        errors,
    )
    technical_notes = optional_text(raw, "technical_notes", NOTES_MAX, errors)

    if errors:
        raise ValidationError(
            "invalid_database_instance",
            "Revise os campos destacados da instância de banco.",
            {"fields": errors},
        )

    for field, value in (
        ("name", name),
        ("version", version),
        ("purpose", purpose),
        ("technical_notes", technical_notes),
    ):
        ensure_no_secret(field, value)

    return DatabaseInstanceFields(
        name=name,
        dbms=dbms,
        version=version,
        server_id=server_id,
        port=port,
        environment=environment,
        purpose=purpose,
        criticality=criticality,
        responsible=responsible,
        administrative_status=administrative_status,
        technical_notes=technical_notes,
    )
