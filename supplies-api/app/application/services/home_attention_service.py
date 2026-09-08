from __future__ import annotations

from typing import Any

from app.application.services.capability_resolution_service import (
    CapabilityResolutionService,
)
from app.domain.entities import EffectiveUser

# Canonical attention shortcuts for the Home hub (E4: counts deferred; no TOTVS fan-out).
ATTENTION_CARD_DEFS: tuple[dict[str, str], ...] = (
    {
        "id": "my_tasks",
        "viewId": "my_tasks",
        "title": "Minhas tarefas",
        "description": "Fila de acompanhamento atribuída a você.",
        "requiredCap": "portal",
    },
    {
        "id": "purchase_requests",
        "viewId": "purchase_requests",
        "title": "Solicitações de compras",
        "description": "SCs no seu escopo de centro de custo e filial.",
        "requiredCap": "purchaseRequests",
    },
    {
        "id": "purchase_orders",
        "viewId": "purchase_orders",
        "title": "Pedidos de compra",
        "description": "Pedidos e acompanhamento operacional.",
        "requiredCap": "operations",
    },
    {
        "id": "deliveries",
        "viewId": "deliveries",
        "title": "Entregas",
        "description": "Entregas e atrasos no seu escopo.",
        "requiredCap": "operations",
    },
    {
        "id": "safety_stock",
        "viewId": "safety_stock",
        "title": "Estoque de segurança",
        "description": "Déficit e cobertura de ESTSEG.",
        "requiredCap": "operations",
    },
    {
        "id": "overview",
        "viewId": "overview",
        "title": "Visão geral",
        "description": "Indicadores do período (não é a tela inicial).",
        "requiredCap": "analytics",
    },
    {
        "id": "administration",
        "viewId": "administration",
        "title": "Administração",
        "description": "Mappings, escopos e configurações do Portal.",
        "requiredCap": "administration",
    },
)


class HomeAttentionService:
    def __init__(
        self,
        capability_resolution: CapabilityResolutionService | None = None,
    ) -> None:
        self.capability_resolution = capability_resolution or CapabilityResolutionService()

    def compose(self, user: EffectiveUser) -> dict[str, Any]:
        resolved = self.capability_resolution.resolve(user)
        capabilities: dict[str, bool] = resolved["capabilities"]
        cards: list[dict[str, Any]] = []
        for definition in ATTENTION_CARD_DEFS:
            required = definition["requiredCap"]
            if not capabilities.get(required, False):
                continue
            cards.append(
                {
                    "id": definition["id"],
                    "viewId": definition["viewId"],
                    "title": definition["title"],
                    "description": definition["description"],
                    "requiredCap": required,
                    "count": None,
                    "status": "available",
                }
            )
        return {"cards": cards, "partialFailures": []}
