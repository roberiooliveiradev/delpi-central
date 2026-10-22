"""Adapters for the supplier enrichment review ports (S2).

- ``DelpiCanonicalSupplierReader``: canonical SA2 read through the existing
  S2S gateway (read-only, same path used by Supplier 360 detail).
- ``UnavailableCompanyRegistryProvider``: production provider — fail-closed.
  S2 ships no real registry source; only test fixtures implement the port.
"""

from __future__ import annotations

from typing import Any

from app.application.services.supplier_enrichment.contracts import (
    EnrichmentSourceUnavailableError,
)
from app.domain.supplier_enrichment.field_mapping import CNPJ_SA2_MAPPING_V1
from app.domain.supplier_enrichment.models import (
    CanonicalSupplierSnapshot,
    ExternalRegistrySnapshot,
    SupplierRef,
    digits_only,
)
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.infrastructure.gateways.delpi_s2s_gateway import DelpiS2SApiGateway


class DelpiCanonicalSupplierReader:
    """Canonical supplier read via the existing api-delpi S2S path."""

    def __init__(self, gateway: DelpiS2SApiGateway | None = None) -> None:
        self._gateway = gateway or DelpiS2SApiGateway()

    def read(
        self, supplier_code: str, supplier_store: str, *, access_token: str
    ) -> CanonicalSupplierSnapshot | None:
        supplier_id = f"{supplier_code.zfill(6)}{supplier_store.zfill(2)}"
        try:
            payload = self._gateway.get(
                f"/integrations/protheus/suppliers/{supplier_id}",
                access_token=access_token,
            )
        except DelpiApiGatewayError as exc:
            if exc.status_code == 404:
                return None
            raise
        data = unwrap_delpi_envelope(payload)
        source: dict[str, Any] = {}
        if isinstance(data, dict):
            candidate = data.get("fornecedor")
            if isinstance(candidate, dict):
                source = candidate
            elif isinstance(candidate, list) and candidate:
                source = candidate[0] if isinstance(candidate[0], dict) else {}
        if not source:
            return None
        fields = {
            spec.field_key: (
                str(source.get(spec.field_key)).strip()
                if source.get(spec.field_key) is not None
                else None
            )
            for spec in CNPJ_SA2_MAPPING_V1.specs
        }
        return CanonicalSupplierSnapshot(
            supplier=SupplierRef(
                code=str(
                    source.get("supplier_code") or source.get("code") or supplier_code
                ),
                store=str(
                    source.get("supplier_store") or source.get("store") or supplier_store
                ),
            ),
            tax_id=digits_only(source.get("tax_id")),
            person_type=str(source.get("person_type") or "").strip().upper(),
            fields=fields,
        )


class UnavailableCompanyRegistryProvider:
    """Fail-closed provider — no real registry source exists in S2."""

    def fetch(self, tax_id: str) -> ExternalRegistrySnapshot:
        raise EnrichmentSourceUnavailableError(
            "no trusted company-registry source is configured"
        )


def company_registry_provider() -> Any:
    """Resolve the configured company-registry adapter.

    ``COMPANY_REGISTRY_PROVIDER=unavailable`` (default) keeps the fail-closed
    behaviour; ``brasilapi`` wires the S3.1 community provider. Unknown values
    fall back to the fail-closed adapter.
    """
    from app.infrastructure.config.settings import Settings

    if Settings.COMPANY_REGISTRY_PROVIDER == "brasilapi":
        from app.infrastructure.gateways.brasilapi_registry_provider import (
            BrasilApiCompanyRegistryProvider,
        )

        return BrasilApiCompanyRegistryProvider()
    return UnavailableCompanyRegistryProvider()
