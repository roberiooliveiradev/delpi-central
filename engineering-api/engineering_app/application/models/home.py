"""Contrato versionado da Home do Portal Engenharia (F2a.S1).

A `engineering-api` é BFF/composição: este schema normaliza itens vindos
de owners oficiais sem reproduzir regras de domínio. Nenhum campo é
inventado — cada item carrega `source` e só os campos que o owner fornece.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"

# Estados canônicos de seção — sem sinônimos duplicados.
# available: fonte respondeu com itens.
# empty: fonte respondeu com sucesso e zero itens (ausência legítima de dados).
# unavailable: fonte indisponível/timeout/falha de transporte ou contrato.
# forbidden: owner do recurso negou acesso ao usuário autenticado.
# not_implemented: seção prevista sem backend oficial (nunca finge dados).
SectionStatus = Literal[
    "available",
    "empty",
    "unavailable",
    "forbidden",
    "not_implemented",
]

# Status agregado: reflete apenas as fontes elegíveis (com backend).
# available: todas responderam; partial: misto; unavailable: nenhuma utilizável.
HomeStatus = Literal["available", "partial", "unavailable"]

# Razões machine-readable de indisponibilidade — auditáveis pelo frontend.
SectionReason = Literal[
    "timeout",
    "transport_error",
    "upstream_error",
    "contract_error",
    "no_official_source",
]


class HomeItem(BaseModel):
    """Item normalizado — resumo autorizado, nunca payload técnico completo."""

    id: str
    kind: str  # "lmp" | "request" | "task" — tipo do recurso na fonte
    title: str
    status: Optional[str] = None  # estado oficial do owner, preservado
    status_label: Optional[str] = None  # rótulo oficial (ex.: alias de workflow)
    date: Optional[str] = None  # data ISO-8601 relevante ao item (owner)
    href: Optional[str] = None  # rota autorizada no Portal para abrir o item
    source: str  # sistema proprietário: "api-delpi" | "requests-api" | ...
    meta: dict[str, Any] = Field(default_factory=dict)


class SourceRef(BaseModel):
    """Provenance — rastreabilidade da seção até o owner oficial."""

    system: str
    endpoint: Optional[str] = None  # rota oficial consumida (método + path)


class HomeSection(BaseModel):
    status: SectionStatus
    source: Optional[SourceRef] = None
    items: list[HomeItem] = Field(default_factory=list)
    total: Optional[int] = None  # total reportado pelo owner (paginação)
    reason: Optional[SectionReason] = None
    message: Optional[str] = None


class HomeSections(BaseModel):
    attention: HomeSection
    tasks: HomeSection
    lmps: HomeSection
    requests: HomeSection
    activity: HomeSection
    collaboration: HomeSection


class HomeResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    generated_at: str  # ISO-8601 UTC
    status: HomeStatus
    sections: HomeSections
