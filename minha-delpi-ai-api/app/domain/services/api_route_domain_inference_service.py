"""Infer apiRouteDomain from Action Catalog / OpenAPI path (no JSON pathMarkers).

E10 — domain authority lives in Python constants ported from the former
``api_route_domains.json`` path maps. Content JSON keeps only labels/methods
and parameterStrategies binding recipes.
"""

from __future__ import annotations

from typing import Any


class ApiRouteDomainInferenceService:
    """Ordered path→domain matching without reading lateral JSON path maps."""

    # Priority mirrors ChatOperationalApiDomainService._ordered_domains
    # (named domains first, then remaining domains in former JSON order).
    # More-specific OpenAPI path fragments before broader prefixes.
    _DOMAIN_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
        ("product_search", ("/products/search",), ()),
        ("product_directives", ("/products/directives/",), ()),
        (
            "product_exclusive_catalog",
            ("/products/exclusive-raw-materials/catalog",),
            (),
        ),
        (
            "product",
            ("/products/{code}", "/products/"),
            (
                "/products/search",
                "/products/directives/",
                "/products/exclusive-raw-materials/",
            ),
        ),
        ("production_consumption", ("/production/consumption/",), ()),
        ("production_losses", ("/production/losses/",), ()),
        ("production_schedule", ("/production/schedule/",), ()),
        ("production_orders", ("/production/orders/",), ()),
        ("production_work_centers", ("/production/work-centers/",), ()),
        ("purchases_ranking", ("/purchases/top-products",), ()),
        ("quality_action_plans", ("/quality/action-plans/",), ()),
        (
            "department_idd",
            (
                "/dashboard/department-idd",
                "/dashboard/department-indicators",
                "/dashboard/departments-indicators",
            ),
            (),
        ),
        ("safety_stock", ("/supplies/safety-stock/",), ()),
        ("supplies_kpi", ("/supplies/",), ("/supplies/safety-stock/",)),
        (
            "department_kpi",
            (
                "/commercial/",
                "/financial/",
                "/production/",
                "/hr/",
                "/quality/",
            ),
            (
                "/production/consumption/",
                "/production/losses/",
                "/production/schedule/",
                "/production/orders/",
                "/production/work-centers/",
                "/production/allocation-gaps",
                "/production/planned-vs-real-time",
                "/quality/action-plans/",
            ),
        ),
        ("open_sales_orders", ("/pedidos-venda-abertos/",), ()),
        ("commercial_proposal_documents", ("/propostas-comerciais/",), ()),
        ("process_inspection_plans", ("/process-inspection-plans/",), ()),
        ("lmp", ("/lmp", "/transforma"), ()),
        ("sql", ("/data/sql", "/data/"), ()),
        ("system", ("/system/",), ()),
    )

    @classmethod
    def infer_from_action(cls, action: dict[str, Any] | None) -> str:
        payload = action if isinstance(action, dict) else {}
        explicit = cls._explicit_domain(payload)
        if explicit:
            return explicit

        path = str(payload.get("path") or "").strip()
        operation_id = str(
            payload.get("operationId") or payload.get("operation_id") or ""
        ).strip()
        return cls.infer_from_path(path, operation_id=operation_id)

    @classmethod
    def infer_from_path(cls, path: str, *, operation_id: str = "") -> str:
        lowered = str(path or "").lower().strip()
        if not lowered:
            return "generic"

        # operation_id reserved for future OpenAPI signals; matching is path-based
        # to preserve former api_route_domains pathMarkers semantics.
        _ = str(operation_id or "").strip().lower()

        for domain_id, markers, excludes in cls._DOMAIN_RULES:
            if not markers:
                continue
            if any(marker in lowered for marker in excludes):
                continue
            if any(marker in lowered for marker in markers):
                return domain_id

        return "generic"

    @classmethod
    def _explicit_domain(cls, action: dict[str, Any]) -> str:
        top = str(action.get("apiRouteDomain") or action.get("api_route_domain") or "").strip()
        if top:
            return top.lower()

        metadata = action.get("delpiMetadata") or action.get("delpi_metadata") or {}
        if isinstance(metadata, dict):
            nested = str(
                metadata.get("apiRouteDomain") or metadata.get("api_route_domain") or ""
            ).strip()
            if nested:
                return nested.lower()

        return ""
