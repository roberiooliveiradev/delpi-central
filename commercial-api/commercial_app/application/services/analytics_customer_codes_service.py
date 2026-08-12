"""Resolve customer_codes TOTVS a partir do escopo commercial (analytics BFF)."""

from __future__ import annotations

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)

# Code that never exists in TOTVS — forces empty result set when portfolio has no customers.
_EMPTY_SCOPE_SENTINEL = "__no_customers__"


class AnalyticsCustomerCodesService:
    """
    unrestricted + sem filtro de carteira → None (consolidado TOTVS).
    membership / carteira filtrada → CSV de códigos (únicos).
    carteira vazia → sentinel (api-delpi aplica 1=0 via lista não vazia inválida… use sentinel real).
    """

    @staticmethod
    def codes_param(scope: CommercialCustomerScope) -> str | None:
        if scope.unrestricted and scope.allowed_customers is None:
            return None
        allowed = scope.allowed_customers or frozenset()
        codes = sorted({code for code, _store in allowed if code})
        if not codes:
            return _EMPTY_SCOPE_SENTINEL
        return ",".join(codes)
