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
    def parse_codes_csv(raw: object | None) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        if not isinstance(raw, str) or not raw.strip():
            return out
        for part in str(raw).split(","):
            code = part.strip()
            if not code or code in seen:
                continue
            seen.add(code)
            out.append(code)
        return out

    @staticmethod
    def apply_selection(scope_codes: str | None, selected: list[str]) -> str | None:
        """Intersecta seleção do MFE com o escopo; não amplia membership."""
        if not selected:
            return scope_codes
        if scope_codes is None:
            return ",".join(selected)
        if scope_codes == _EMPTY_SCOPE_SENTINEL:
            return _EMPTY_SCOPE_SENTINEL
        allowed = set(scope_codes.split(","))
        intersected = [code for code in selected if code in allowed]
        if not intersected:
            return _EMPTY_SCOPE_SENTINEL
        return ",".join(intersected)

    @staticmethod
    def codes_param(scope: CommercialCustomerScope) -> str | None:
        if scope.unrestricted and scope.allowed_customers is None:
            return None
        allowed = scope.allowed_customers or frozenset()
        codes = sorted({code for code, _store in allowed if code})
        if not codes:
            return _EMPTY_SCOPE_SENTINEL
        return ",".join(codes)

    @classmethod
    def codes_param_for_selection(
        cls,
        scope: CommercialCustomerScope,
        selected_codes: str | None = None,
    ) -> str | None:
        return cls.apply_selection(
            cls.codes_param(scope),
            cls.parse_codes_csv(selected_codes),
        )
