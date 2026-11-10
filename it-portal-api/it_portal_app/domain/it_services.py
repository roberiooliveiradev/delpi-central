"""Cadastro de serviços e aplicações — normalização e validação de entrada.

Um serviço é a aplicação lógica ou o serviço de plataforma; onde ele roda
(container, processo, serviço do SO) é a hospedagem em `inventory_links`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from it_portal_app.domain.catalogs import (
    ADMINISTRATIVE_STATUSES,
    CRITICALITIES,
    ENVIRONMENTS,
    SERVICE_KINDS,
    SERVICE_TYPES,
    UNIT_CODES,
)
from it_portal_app.domain.errors import ValidationError
from it_portal_app.domain.field_rules import choice, optional_port, optional_text, required_text
from it_portal_app.domain.secret_guard import ensure_no_secret

NAME_MAX = 120
TECHNOLOGY_MAX = 120
RESPONSIBLE_MAX = 160
DESCRIPTION_MAX = 4000

SERVICE_CODE_PREFIX = "SVC-"


def format_service_code(seq: int) -> str:
    return f"{SERVICE_CODE_PREFIX}{seq:04d}"


@dataclass(frozen=True)
class ServiceFields:
    name: str
    description: str | None
    service_kind: str
    service_type: str
    technology: str | None
    environment: str
    unit_code: str
    port: int | None
    criticality: str
    responsible: str
    administrative_status: str

    def as_dict(self) -> dict:
        return asdict(self)


SERVICE_FIELD_NAMES = tuple(ServiceFields.__dataclass_fields__.keys())


def build_service_fields(raw: dict) -> ServiceFields:
    errors: dict[str, str] = {}
    name = required_text(raw, "name", NAME_MAX, "Informe o nome do serviço.", errors)
    service_kind = choice(
        raw, "service_kind", SERVICE_KINDS, "Selecione se é aplicação ou serviço de plataforma.", errors
    )
    service_type = choice(raw, "service_type", SERVICE_TYPES, "Selecione o tipo do serviço.", errors)
    technology = optional_text(raw, "technology", TECHNOLOGY_MAX, errors)
    environment = choice(raw, "environment", ENVIRONMENTS, "Selecione o ambiente.", errors)
    unit_code = choice(raw, "unit_code", UNIT_CODES, "Selecione a unidade.", errors)
    port = optional_port(raw, "port", errors)
    criticality = choice(raw, "criticality", CRITICALITIES, "Selecione a criticidade.", errors)
    responsible = required_text(
        raw, "responsible", RESPONSIBLE_MAX, "Informe o responsável pelo serviço.", errors
    )
    administrative_status = choice(
        raw,
        "administrative_status",
        ADMINISTRATIVE_STATUSES,
        "Selecione a situação administrativa.",
        errors,
    )
    description = optional_text(raw, "description", DESCRIPTION_MAX, errors)

    if errors:
        raise ValidationError(
            "invalid_service", "Revise os campos destacados do serviço.", {"fields": errors}
        )

    ensure_no_secret("technology", technology)
    ensure_no_secret("description", description)

    return ServiceFields(
        name=name,
        description=description,
        service_kind=service_kind,
        service_type=service_type,
        technology=technology,
        environment=environment,
        unit_code=unit_code,
        port=port,
        criticality=criticality,
        responsible=responsible,
        administrative_status=administrative_status,
    )
