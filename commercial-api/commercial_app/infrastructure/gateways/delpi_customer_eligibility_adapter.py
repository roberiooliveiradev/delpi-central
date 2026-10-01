"""Elegibilidade SA1 via api-delpi `/customers/enrichment` (batch por pares).

O campo `blocked` vem de `SA1.A1_MSBLQL`:
- item ausente na resposta ou `blocked` None → par não existe na SA1;
- `'1'` → cliente bloqueado/inativo;
- `'2'`/'' → cliente ativo.
"""

from __future__ import annotations

import logging
from typing import Mapping, Sequence

from commercial_app.domain.ports.customer_eligibility_port import (
    CustomerEligibility,
    CustomerEligibilityPort,
)
from commercial_app.infrastructure.gateways.delpi_commercial_gateway import (
    DelpiCommercialGateway,
)

logger = logging.getLogger("commercial.customer_eligibility")


class DelpiCustomerEligibilityAdapter(CustomerEligibilityPort):
    def __init__(self, gateway: DelpiCommercialGateway | None = None) -> None:
        self._gateway = gateway or DelpiCommercialGateway()

    def lookup(
        self,
        customers: Sequence[tuple[str, str]],
    ) -> Mapping[tuple[str, str], CustomerEligibility]:
        pairs = [
            (str(code or "").strip(), str(store or "").strip())
            for code, store in customers
            if str(code or "").strip() and str(store or "").strip()
        ]
        if not pairs:
            return {}

        response = self._gateway.enrich_portfolio_customers(
            payload={
                "customers": [
                    {"customer_code": code, "customer_store": store}
                    for code, store in pairs
                ]
            }
        )
        data = response.get("data") if isinstance(response, dict) else None
        if not isinstance(data, dict):
            data = response if isinstance(response, dict) else {}
        items = data.get("items") if isinstance(data, dict) else None

        found: dict[tuple[str, str], CustomerEligibility] = {}
        for item in items or []:
            if not isinstance(item, dict):
                continue
            code = str(item.get("customer_code") or "").strip()
            store = str(item.get("customer_store") or "").strip()
            if not code or not store:
                continue
            blocked = item.get("blocked")
            found[(code, store)] = CustomerEligibility(
                exists=blocked is not None,
                active=blocked is not None and str(blocked).strip() != "1",
            )
        return found
