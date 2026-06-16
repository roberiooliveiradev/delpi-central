"""Roteamento de apresentação por meta.entity (contrato OpenAPI operacional)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


class _EntitySetDescriptor:
    def __init__(self, set_key: str) -> None:
        self.set_key = set_key

    def __get__(self, obj: object | None, owner: type) -> frozenset[str]:
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        return ChatPresentationProfileService.entity_set(self.set_key)


class _EntityRoutedForPresentDescriptor:
    def __get__(self, obj: object | None, owner: type) -> frozenset[str]:
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        return ChatPresentationProfileService.entity_routed_for_present()


_MODULE_ENTITY_SET_ALIASES = {
    "CHAT_CRITICAL_ENTITIES": "chatCritical",
    "PLAYBOOK_OPERATIONAL_ENTITIES": "playbookOperational",
    "PROFILE_PRESENT_ENTITIES": "profilePresent",
    "PRODUCT_LIST_PRESENT_ENTITIES": "productListPresent",
    "KPI_PRESENT_ENTITIES": "kpiPresent",
    "LMP_PRESENT_ENTITIES": "lmpPresent",
    "SQL_PRESENT_ENTITIES": "sqlPresent",
    "SYSTEM_PRESENT_ENTITIES": "systemPresent",
    "SALE_ORDER_PRESENT_ENTITIES": "saleOrderPresent",
}


def __getattr__(name: str) -> frozenset[str]:
    if name == "ENTITY_ROUTED_FOR_PRESENT":
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        return ChatPresentationProfileService.entity_routed_for_present()

    set_key = _MODULE_ENTITY_SET_ALIASES.get(name)

    if set_key:
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        return ChatPresentationProfileService.entity_set(set_key)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


@dataclass(frozen=True)
class ApiDelpiResponseProfile:
    entity: str | None
    shape: str | None
    operation_id: str | None
    routed_by: str  # "meta.entity" | "path" | "none"


class ChatApiDelpiResponseProfileService:
    CHAT_CRITICAL_ENTITIES = _EntitySetDescriptor("chatCritical")
    PLAYBOOK_OPERATIONAL_ENTITIES = _EntitySetDescriptor("playbookOperational")
    PROFILE_PRESENT_ENTITIES = _EntitySetDescriptor("profilePresent")
    PRODUCT_LIST_PRESENT_ENTITIES = _EntitySetDescriptor("productListPresent")
    KPI_PRESENT_ENTITIES = _EntitySetDescriptor("kpiPresent")
    LMP_PRESENT_ENTITIES = _EntitySetDescriptor("lmpPresent")
    SQL_PRESENT_ENTITIES = _EntitySetDescriptor("sqlPresent")
    SYSTEM_PRESENT_ENTITIES = _EntitySetDescriptor("systemPresent")
    SALE_ORDER_PRESENT_ENTITIES = _EntitySetDescriptor("saleOrderPresent")
    ENTITY_ROUTED_FOR_PRESENT = _EntityRoutedForPresentDescriptor()

    @classmethod
    def resolve(cls, data: Any, *, path: str = "") -> ApiDelpiResponseProfile:
        meta = cls.extract_meta(data)
        entity = None
        shape = None
        operation_id = None
        routed_by = "none"

        if meta:
            raw_entity = meta.get("entity")
            if isinstance(raw_entity, str) and raw_entity.strip():
                entity = raw_entity.strip()
                routed_by = "meta.entity"

            raw_shape = meta.get("shape")
            if isinstance(raw_shape, str) and raw_shape.strip():
                shape = raw_shape.strip()

            raw_operation = meta.get("operationId")
            if isinstance(raw_operation, str) and raw_operation.strip():
                operation_id = raw_operation.strip()

        if not entity:
            fallback_entity = cls._entity_from_path(path)
            if fallback_entity:
                entity = fallback_entity
                routed_by = "path"

        return ApiDelpiResponseProfile(
            entity=entity,
            shape=shape,
            operation_id=operation_id,
            routed_by=routed_by,
        )

    @classmethod
    def extract_meta(cls, data: Any) -> dict[str, Any] | None:
        if not isinstance(data, dict):
            return None

        meta = data.get("meta")

        if isinstance(meta, dict):
            return meta

        return None

    @classmethod
    def is_chat_critical(cls, entity: str | None) -> bool:
        return bool(entity and entity in cls.CHAT_CRITICAL_ENTITIES)

    @classmethod
    def is_profile_present_entity(cls, entity: str | None) -> bool:
        return bool(entity and entity in cls.PROFILE_PRESENT_ENTITIES)

    @classmethod
    def is_kpi_entity(cls, entity: str | None) -> bool:
        return bool(entity and entity in cls.KPI_PRESENT_ENTITIES)

    @classmethod
    def is_entity_routed_for_present(cls, entity: str | None) -> bool:
        return bool(entity and entity in cls.ENTITY_ROUTED_FOR_PRESENT)

    @classmethod
    def is_playbook_operational_entity(cls, entity: str | None) -> bool:
        return bool(entity and entity in cls.PLAYBOOK_OPERATIONAL_ENTITIES)

    @classmethod
    def resolve_entity_from_path(cls, path: str) -> str | None:
        return cls._entity_from_path(path)

    @classmethod
    def is_playbook_operational_path(cls, path: str) -> bool:
        entity = cls._entity_from_path(path)
        return cls.is_playbook_operational_entity(entity)

    @classmethod
    def entity_path_hint(cls, entity: str | None) -> str:
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        return ChatPresentationProfileService.entity_path_hint(entity)

    @classmethod
    def presentation_path(cls, *, path: str = "", entity: str | None = None) -> str:
        normalized = str(path or "").strip()
        if normalized:
            return normalized

        hint = cls.entity_path_hint(entity)
        if not hint:
            return ""

        code_match = re.search(r"/products/(\d+)", normalized, flags=re.IGNORECASE)
        product_code = code_match.group(1) if code_match else "0"
        return hint.replace("/products/0/", f"/products/{product_code}/")

    @classmethod
    def profile_coverage_ratio(cls) -> float:
        critical = cls.CHAT_CRITICAL_ENTITIES
        present = cls.PROFILE_PRESENT_ENTITIES

        if not critical:
            return 0.0

        covered = critical & present
        return len(covered) / len(critical)

    @classmethod
    def enrich_humanized(cls, humanized: dict | None, data: Any) -> dict | None:
        return humanized

    @classmethod
    def _entity_from_path(cls, path: str) -> str | None:
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        return ChatPresentationProfileService.resolve_entity_from_path(path)
