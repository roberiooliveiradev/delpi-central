"""Roteamento de apresentação por meta.entity (Fase 7 — contrato api-delpi)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CHAT_CRITICAL_ENTITIES: frozenset[str] = frozenset(
    {
        "product_search",
        "product",
        "product_stock",
        "product_structure",
        "product_structure_exclusivity",
        "product_analyser",
        "product_factory_status",
        "product_production_status",
        "product_shipping_status",
        "product_parents",
        "product_guide",
        "product_inspection",
        "product_pricing",
        "product_purchases",
        "product_sales",
        "product_open_orders",
        "product_billing",
        "product_suppliers",
        "product_customers",
        "product_internal_movements",
        "product_inbound_invoice_items",
        "product_outbound_invoice_items",
    }
)

PROFILE_PRESENT_ENTITIES: frozenset[str] = frozenset(
    {
        "product_search",
        "product",
        "product_stock",
        "product_structure",
        "product_structure_exclusivity",
        "product_analyser",
        "product_factory_status",
        "product_production_status",
        "product_shipping_status",
        "product_parents",
        "product_guide",
        "product_inspection",
        "product_pricing",
        "product_purchases",
        "product_suppliers",
        "product_customers",
        "product_internal_movements",
        "product_inbound_invoice_items",
        "product_outbound_invoice_items",
    }
)

PATH_ENTITY_FALLBACKS: tuple[tuple[str, str], ...] = (
    ("/analyser", "product_analyser"),
    ("/factory-status", "product_factory_status"),
    ("/structure/exclusivity", "product_structure_exclusivity"),
    ("/production-status", "product_production_status"),
    ("/shipping-status", "product_shipping_status"),
    ("/structure", "product_structure"),
    ("/parents", "product_parents"),
    ("/stock", "product_stock"),
    ("/guide", "product_guide"),
    ("/inspection", "product_inspection"),
    ("/pricing", "product_pricing"),
    ("/purchases", "product_purchases"),
    ("/suppliers", "product_suppliers"),
    ("/customers", "product_customers"),
    ("/internal-movements", "product_internal_movements"),
    ("/inbound-invoice-items", "product_inbound_invoice_items"),
    ("/outbound-invoice-items", "product_outbound_invoice_items"),
    ("/open-orders", "product_open_orders"),
    ("/sales/billing", "product_billing"),
    ("/sales", "product_sales"),
    ("/summary", "product"),
    ("/search", "product_search"),
)


@dataclass(frozen=True)
class ApiDelpiResponseProfile:
    entity: str | None
    shape: str | None
    operation_id: str | None
    routed_by: str  # "meta.entity" | "path" | "none"


class ChatApiDelpiResponseProfileService:
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
        return bool(entity and entity in CHAT_CRITICAL_ENTITIES)

    @classmethod
    def is_profile_present_entity(cls, entity: str | None) -> bool:
        return bool(entity and entity in PROFILE_PRESENT_ENTITIES)

    @classmethod
    def profile_coverage_ratio(cls) -> float:
        if not CHAT_CRITICAL_ENTITIES:
            return 0.0
        covered = CHAT_CRITICAL_ENTITIES & PROFILE_PRESENT_ENTITIES
        return len(covered) / len(CHAT_CRITICAL_ENTITIES)

    @classmethod
    def enrich_humanized(cls, humanized: dict | None, data: Any) -> dict | None:
        if not isinstance(humanized, dict):
            return humanized

        meta = cls.extract_meta(data)

        if not meta:
            return humanized

        fields = meta.get("fields")

        if not isinstance(fields, dict) or not fields:
            return humanized

        glossary_lines = [
            f"{key}: {label.strip()}"
            for key, label in fields.items()
            if isinstance(key, str) and isinstance(label, str) and label.strip()
        ][:4]

        if not glossary_lines:
            return humanized

        enriched = dict(humanized)
        detail_lines = list(enriched.get("linhas_detalhe") or [])
        existing = set(detail_lines) | set(enriched.get("linhas") or [])

        for line in glossary_lines:
            if line not in existing:
                detail_lines.append(line)

        if detail_lines:
            enriched["linhas_detalhe"] = detail_lines

        return enriched

    @classmethod
    def _entity_from_path(cls, path: str) -> str | None:
        lowered = str(path or "").lower()

        if not lowered:
            return None

        for fragment, entity in PATH_ENTITY_FALLBACKS:
            if fragment in lowered:
                return entity

        parts = lowered.rstrip("/").split("/")

        if (
            len(parts) >= 3
            and parts[-2] == "products"
            and parts[-1].isdigit()
        ):
            return "product"

        return None
