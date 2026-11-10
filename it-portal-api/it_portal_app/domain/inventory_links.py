"""Vínculos explícitos entre recursos do inventário (E2A).

- hospedagem: serviço → servidor (onde a instância roda);
- consumo: serviço → instância de banco.

Cada vínculo tem id estável; removê-lo nunca remove os recursos ligados.
"""

from __future__ import annotations

from dataclasses import dataclass

from it_portal_app.domain.catalogs import HOSTING_RUNTIMES
from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.field_rules import choice, optional_text, required_uuid
from it_portal_app.domain.secret_guard import ensure_no_secret

INSTANCE_NAME_MAX = 160
LINK_NOTES_MAX = 500


@dataclass(frozen=True)
class HostingFields:
    service_id: str
    server_id: str
    runtime: str
    instance_name: str | None
    notes: str | None


@dataclass(frozen=True)
class ConsumerFields:
    database_instance_id: str
    service_id: str
    notes: str | None


def build_hosting_fields(raw: dict) -> HostingFields:
    errors: dict[str, str] = {}
    service_id = required_uuid(raw, "service_id", "Selecione o serviço.", errors)
    server_id = required_uuid(raw, "server_id", "Selecione o servidor.", errors)
    runtime = choice(
        raw, "runtime", HOSTING_RUNTIMES, "Selecione como o serviço roda no servidor.", errors
    )
    instance_name = optional_text(raw, "instance_name", INSTANCE_NAME_MAX, errors)
    notes = optional_text(raw, "notes", LINK_NOTES_MAX, errors)
    if errors:
        raise ValidationError(
            "invalid_service_hosting", "Revise os campos do vínculo.", {"fields": errors}
        )
    ensure_no_secret("instance_name", instance_name)
    ensure_no_secret("notes", notes)
    return HostingFields(
        service_id=service_id,
        server_id=server_id,
        runtime=runtime,
        instance_name=instance_name,
        notes=notes,
    )


def build_consumer_fields(raw: dict) -> ConsumerFields:
    errors: dict[str, str] = {}
    database_instance_id = required_uuid(
        raw, "database_instance_id", "Selecione a instância de banco.", errors
    )
    service_id = required_uuid(raw, "service_id", "Selecione o serviço.", errors)
    notes = optional_text(raw, "notes", LINK_NOTES_MAX, errors)
    if errors:
        raise ValidationError(
            "invalid_database_consumer", "Revise os campos do vínculo.", {"fields": errors}
        )
    ensure_no_secret("notes", notes)
    return ConsumerFields(
        database_instance_id=database_instance_id, service_id=service_id, notes=notes
    )
