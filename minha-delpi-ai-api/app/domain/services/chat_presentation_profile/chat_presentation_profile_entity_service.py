"""Delegate — perfis declarativos de apresentação."""

from __future__ import annotations

from typing import Any

from app.domain.services.openapi_presentation_profile_deriver_service import (
    OpenApiPresentationProfileDeriverService,
)
from app.domain.services.openapi_operation_contract_service import (
    OpenApiOperationContractService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_facade_access import (
    presentation_profile_service,
)



class ChatPresentationProfileEntityService:
    @classmethod
    def entity_set(cls, set_key: str) -> frozenset[str]:
        raw = presentation_profile_service().node("entitySets", str(set_key or "").strip())

        if not isinstance(raw, list):
            return frozenset()

        return frozenset(
            str(item).strip()
            for item in raw
            if str(item).strip()
        )

    @classmethod
    def entity_routed_for_present(cls) -> frozenset[str]:
        merged: set[str] = set()

        for key in (
            "profilePresent",
            "kpiPresent",
            "lmpPresent",
            "sqlPresent",
            "systemPresent",
            "saleOrderPresent",
            "entityRoutedExtra",
        ):
            merged.update(presentation_profile_service().entity_set(key))

        return frozenset(merged)

    @classmethod
    def entity_presentation_routing(cls) -> dict[str, Any]:
        node = presentation_profile_service().node("entityPresentationRouting")

        return dict(node) if isinstance(node, dict) else {}

    @classmethod
    def operational_empty_route_key(cls, entity: str | None) -> str | None:
        mapping = cls.entity_presentation_routing().get("operationalEmptyKeys") or {}
        token = str(entity or "").strip()
        key = mapping.get(token) if token else None

        return str(key) if key else None

    @classmethod
    def is_product_operational_entity(cls, entity: str | None) -> bool:
        token = str(entity or "").strip()
        entities = cls.entity_presentation_routing().get("productOperationalEntities") or []

        return bool(token and token in entities)

    @classmethod
    def list_route_entity(cls, entity: str | None) -> str | None:
        mapping = cls.entity_presentation_routing().get("listRouteEntities") or {}
        token = str(entity or "").strip()
        route = mapping.get(token) if token else None

        return str(route) if route else None

    @classmethod
    def is_no_chart_entity(cls, entity: str | None) -> bool:
        token = str(entity or "").strip()
        entities = cls.entity_presentation_routing().get("noChartEntities") or []

        return bool(token and token in entities)

