"""Supplier creation preview — orchestration (X4.UX-R1.S1).

Strictly read-only: the external registry provider is consulted for prefill
suggestions and api-delpi for an *exact* canonical duplicate check. Nothing
is persisted anywhere — no supplier POST/PUT, no review record, no mirror of
the external payload in PostgreSQL.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.application.services.supplier_enrichment.contracts import (
    CompanyRegistryProvider,
)
from app.application.services.suppliers_dto import POST_SUPPLIER_FIELDS
from app.domain.supplier_creation.preview import (
    DuplicateStatus,
    build_creation_suggestions,
    classify_duplicate,
    mask_tax_id,
)
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError

# Draft fields the preview never suggests — the client supplies them
# (``tax_id`` is the request input; ``person_type`` is derived by document
# kind and returned top-level).
_NON_SUGGESTED = frozenset({"tax_id", "person_type"})


class SupplierDuplicateSearchPort(Protocol):
    """Exact canonical duplicate lookup in api-delpi (SA2)."""

    def search_by_tax_id(
        self, tax_id: str, *, access_token: str = ""
    ) -> tuple[list[dict[str, Any]], int]: ...


class SupplierCreationPreviewService:
    def __init__(
        self,
        *,
        registry_provider: CompanyRegistryProvider,
        duplicate_search: SupplierDuplicateSearchPort,
    ) -> None:
        self._registry = registry_provider
        self._duplicate_search = duplicate_search

    def preview(self, tax_id: str, *, access_token: str = "") -> dict[str, Any]:
        snapshot = self._registry.fetch(tax_id)
        suggestions = build_creation_suggestions(snapshot.fields)

        duplicate_check = self._duplicate_check(tax_id, access_token)

        suggested_keys = {s.field_key for s in suggestions}
        unavailable_fields = sorted(
            key
            for key in POST_SUPPLIER_FIELDS - suggested_keys
            if key not in _NON_SUGGESTED
        )

        return {
            "tax_id_masked": mask_tax_id(tax_id),
            "person_type": "J",
            "duplicate_check": duplicate_check,
            "suggestions": [
                {
                    "field_key": s.field_key,
                    "suggested_value": s.suggested_value,
                    "source": {
                        "provider_id": snapshot.source_id,
                        "retrieved_at": snapshot.retrieved_at,
                    },
                    "applicable": s.applicable,
                }
                for s in suggestions
            ],
            "unavailable_fields": unavailable_fields,
            # This operation never persists; the creation write path keeps its
            # own upstream gate (POST /suppliers → Protheus feature gate).
            "write_enabled": False,
        }

    def _duplicate_check(self, tax_id: str, access_token: str) -> dict[str, Any]:
        try:
            matches, total = self._duplicate_search.search_by_tax_id(
                tax_id, access_token=access_token
            )
        except DelpiApiGatewayError:
            status = classify_duplicate(None)
            return {"status": status.value, "matches": []}

        status = classify_duplicate(total)
        if status is DuplicateStatus.POSSIBLE_MATCH:
            minimal = [
                {
                    "supplier_code": item.get("supplier_code"),
                    "supplier_store": item.get("supplier_store"),
                    "supplier_name": item.get("supplier_name"),
                    "state": item.get("state"),
                    "blocked": item.get("blocked"),
                }
                for item in matches[:10]
            ]
        else:
            minimal = []
        return {"status": status.value, "matches": minimal}
