"""Integrações e dependências operacionais entre serviços (E2B).

Integração: troca entre dois pontos, cada um sendo um serviço do inventário ou
um sistema externo nomeado explicitamente (não cadastrado). Pelo menos uma
ponta é interna; nenhuma credencial, token ou payload é registrado.

Dependência operacional: o serviço dependente precisa do requerido para
operar. É sempre explícita — nunca presumida a partir de outros vínculos.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from it_portal_app.domain.catalogs import (
    ADMINISTRATIVE_STATUSES,
    CRITICALITIES,
    INTEGRATION_DIRECTIONS,
    INTEGRATION_PROTOCOLS,
)
from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.field_rules import (
    choice,
    clean,
    optional_text,
    required_text,
    required_uuid,
)
from it_portal_app.domain.secret_guard import ensure_no_secret

NAME_MAX = 120
EXTERNAL_NAME_MAX = 160
PURPOSE_MAX = 160
RESPONSIBLE_MAX = 160
NOTES_MAX = 4000
LINK_NOTES_MAX = 500

INTEGRATION_CODE_PREFIX = "INT-"


def format_integration_code(seq: int) -> str:
    return f"{INTEGRATION_CODE_PREFIX}{seq:04d}"


@dataclass(frozen=True)
class IntegrationFields:
    name: str
    source_service_id: str | None
    source_external_name: str | None
    target_service_id: str | None
    target_external_name: str | None
    protocol: str
    direction: str
    purpose: str | None
    criticality: str
    responsible: str
    administrative_status: str
    notes: str | None

    def as_dict(self) -> dict:
        return asdict(self)

    def internal_service_ids(self) -> tuple[str, ...]:
        return tuple(
            service_id
            for service_id in (self.source_service_id, self.target_service_id)
            if service_id
        )


INTEGRATION_FIELD_NAMES = tuple(IntegrationFields.__dataclass_fields__.keys())


def _endpoint(raw: dict, side: str, label: str, errors: dict) -> tuple[str | None, str | None]:
    service_field = f"{side}_service_id"
    external_field = f"{side}_external_name"
    has_service = bool(clean(raw.get(service_field)))
    has_external = bool(clean(raw.get(external_field)))
    if has_service and has_external:
        errors[external_field] = (
            f"{label}: informe um serviço cadastrado ou um sistema externo, não ambos."
        )
        return None, None
    if has_service:
        return required_uuid(raw, service_field, f"Selecione o serviço de {label.lower()}.", errors), None
    if has_external:
        return None, optional_text(raw, external_field, EXTERNAL_NAME_MAX, errors)
    errors[service_field] = (
        f"Selecione o serviço de {label.lower()} ou identifique o sistema externo."
    )
    return None, None


def build_integration_fields(raw: dict) -> IntegrationFields:
    errors: dict[str, str] = {}
    name = required_text(raw, "name", NAME_MAX, "Informe o nome da integração.", errors)
    source_service_id, source_external_name = _endpoint(raw, "source", "Origem", errors)
    target_service_id, target_external_name = _endpoint(raw, "target", "Destino", errors)
    protocol = choice(
        raw, "protocol", INTEGRATION_PROTOCOLS, "Selecione o protocolo ou mecanismo.", errors
    )
    direction = choice(raw, "direction", INTEGRATION_DIRECTIONS, "Selecione a direção.", errors)
    purpose = optional_text(raw, "purpose", PURPOSE_MAX, errors)
    criticality = choice(raw, "criticality", CRITICALITIES, "Selecione a criticidade.", errors)
    responsible = required_text(
        raw, "responsible", RESPONSIBLE_MAX, "Informe o responsável pela integração.", errors
    )
    administrative_status = choice(
        raw,
        "administrative_status",
        ADMINISTRATIVE_STATUSES,
        "Selecione a situação administrativa.",
        errors,
    )
    notes = optional_text(raw, "notes", NOTES_MAX, errors)

    if not errors:
        if source_external_name and target_external_name:
            errors["target_external_name"] = (
                "Pelo menos uma ponta precisa ser um serviço cadastrado no inventário."
            )
        elif source_service_id and source_service_id == target_service_id:
            errors["target_service_id"] = "Origem e destino precisam ser serviços diferentes."

    if errors:
        raise ValidationError(
            "invalid_integration",
            "Revise os campos destacados da integração.",
            {"fields": errors},
        )

    for field, value in (
        ("name", name),
        ("source_external_name", source_external_name),
        ("target_external_name", target_external_name),
        ("purpose", purpose),
        ("notes", notes),
    ):
        ensure_no_secret(field, value)

    return IntegrationFields(
        name=name,
        source_service_id=source_service_id,
        source_external_name=source_external_name,
        target_service_id=target_service_id,
        target_external_name=target_external_name,
        protocol=protocol,
        direction=direction,
        purpose=purpose,
        criticality=criticality,
        responsible=responsible,
        administrative_status=administrative_status,
        notes=notes,
    )


@dataclass(frozen=True)
class ServiceDependencyFields:
    dependent_service_id: str
    required_service_id: str
    notes: str | None


def build_service_dependency_fields(raw: dict) -> ServiceDependencyFields:
    errors: dict[str, str] = {}
    dependent = required_uuid(
        raw, "dependent_service_id", "Selecione o serviço dependente.", errors
    )
    required = required_uuid(raw, "required_service_id", "Selecione o serviço requerido.", errors)
    notes = optional_text(raw, "notes", LINK_NOTES_MAX, errors)
    if not errors and dependent == required:
        errors["required_service_id"] = "Um serviço não pode depender de si mesmo."
    if errors:
        raise ValidationError(
            "invalid_service_dependency", "Revise os campos da dependência.", {"fields": errors}
        )
    ensure_no_secret("notes", notes)
    return ServiceDependencyFields(
        dependent_service_id=dependent, required_service_id=required, notes=notes
    )
