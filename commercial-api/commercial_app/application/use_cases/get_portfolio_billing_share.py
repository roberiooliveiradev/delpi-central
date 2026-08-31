"""Share faturamento carteira ÷ empresa (KPI-PORTFOLIO-SHARE)."""

from __future__ import annotations

from typing import Any, Protocol

from commercial_app.application.services.analytics_customer_codes_service import (
    AnalyticsCustomerCodesService,
)
from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)

HEAD_OFFICE_ROL_PATH = "/head_office_rol_target_pct"
BRANCH_ROL_PATH = "/branch_rol_target_pct"
NATURE_PORTFOLIO_BILLING_SHARE = "portfolio_billing_share"
BILLING_AMOUNT_NATURES = ("gross", "net")
DEFAULT_BILLING_AMOUNT_NATURE = "gross"


def normalize_billing_amount_nature(value: str | None) -> str:
    if not isinstance(value, str):
        value = None
    nature = (value or DEFAULT_BILLING_AMOUNT_NATURE).strip().lower()
    if nature not in BILLING_AMOUNT_NATURES:
        raise ValueError("nature inválida. Use gross ou net.")
    return nature


class CommercialAnalyticsGatewayPort(Protocol):
    def get_commercial_analytics(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _unwrap_data(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload.get("data")
    return payload


def extract_rol_from_target_payload(raw: Any) -> float:
    """Lê `rol` do envelope target pct (api-delpi)."""
    data = _unwrap_data(raw)
    if not isinstance(data, dict):
        return 0.0
    return _as_float(data.get("rol"))


def extract_amount_from_target_payload(raw: Any, *, nature: str) -> float:
    """net → rol; gross → gross_revenue (fallback rol se ausente)."""
    data = _unwrap_data(raw)
    if not isinstance(data, dict):
        return 0.0
    nature = normalize_billing_amount_nature(nature)
    if nature == "gross":
        if data.get("gross_revenue") is not None:
            return _as_float(data.get("gross_revenue"))
    return _as_float(data.get("rol"))


def resolve_rol_paths_for_branch(branch: str | None) -> tuple[str, ...]:
    """Paridade Overview: unidade 01 = matriz; 02 = filial; vazio = soma das duas."""
    code = (branch or "").strip()
    if code == "01":
        return (HEAD_OFFICE_ROL_PATH,)
    if code == "02":
        return (BRANCH_ROL_PATH,)
    return (HEAD_OFFICE_ROL_PATH, BRANCH_ROL_PATH)


def compute_share_pct(portfolio_rol: float, company_rol: float) -> float | None:
    if company_rol <= 0:
        return None
    return round((portfolio_rol / company_rol) * 100, 1)


def _totvs_params(
    scope: CommercialCustomerScope,
    base: dict[str, object | None],
) -> dict[str, object]:
    params: dict[str, object] = {
        key: value
        for key, value in base.items()
        if value is not None and value != ""
    }
    codes = AnalyticsCustomerCodesService.codes_param(scope)
    if codes is not None:
        params["customer_codes"] = codes
    return params


class GetPortfolioBillingShareUseCase:
    """Numerador = ROL do escopo; denominador = ROL empresa (sem customer_codes)."""

    def execute(
        self,
        gateway: CommercialAnalyticsGatewayPort,
        portfolio_scope: CommercialCustomerScope,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None = None,
        customer_segment: str | None = None,
        nature: str | None = None,
    ) -> dict[str, Any]:
        amount_nature = normalize_billing_amount_nature(nature)
        company_scope = CommercialCustomerScope(
            unrestricted=True,
            allowed_customers=None,
        )
        base: dict[str, object | None] = {
            "start_date": start_date,
            "end_date": end_date,
            "customer_segment": customer_segment,
        }
        portfolio_rol = self._sum_amount(
            gateway, portfolio_scope, base, branch, amount_nature
        )
        company_rol = self._sum_amount(
            gateway, company_scope, base, branch, amount_nature
        )
        return {
            "portfolioRol": round(portfolio_rol, 2),
            "companyRol": round(company_rol, 2),
            "sharePct": compute_share_pct(portfolio_rol, company_rol),
            "startDate": start_date,
            "endDate": end_date,
            "branch": branch,
            "nature": amount_nature,
            "billingNature": amount_nature,
            "kpiNature": NATURE_PORTFOLIO_BILLING_SHARE,
            "supportedNatures": list(BILLING_AMOUNT_NATURES),
        }

    def _sum_amount(
        self,
        gateway: CommercialAnalyticsGatewayPort,
        scope: CommercialCustomerScope,
        base: dict[str, object | None],
        branch: str | None,
        nature: str,
    ) -> float:
        params = _totvs_params(scope, base)
        total = 0.0
        for path in resolve_rol_paths_for_branch(branch):
            payload = gateway.get_commercial_analytics(path, params=params)
            total += extract_amount_from_target_payload(payload, nature=nature)
        return total

    def _sum_rol(
        self,
        gateway: CommercialAnalyticsGatewayPort,
        scope: CommercialCustomerScope,
        base: dict[str, object | None],
        branch: str | None,
    ) -> float:
        return self._sum_amount(gateway, scope, base, branch, "net")
