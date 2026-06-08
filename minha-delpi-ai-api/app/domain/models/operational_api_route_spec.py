"""Contrato de roteamento operacional — independente de produto, KPI ou outro domínio."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperationalApiRouteSpec:
    """Descreve *o que* buscar na API sem acoplar ao tipo concreto no chamador."""

    domain: str
    reason: str
    path_tokens: tuple[str, ...] = ()
    path_prefixes: tuple[str, ...] = ()
    operation_tokens: tuple[str, ...] = ()
    parameter_strategy: str = "date_branch"
    method: str = "GET"
    entity_code: str | None = None
    route_segment: str | None = None
    prioritize: str | None = None

    @classmethod
    def from_department_kpi(cls, match) -> OperationalApiRouteSpec:
        path_token = str(getattr(match, "path_token", "") or "").lower()
        domain_prefix = str(getattr(match, "domain_prefix", "") or "").lower()
        operation_hint = str(getattr(match, "operation_hint", "") or "").strip()
        operation_token = (
            operation_hint.lower()
            if operation_hint
            else path_token.rsplit("/", maxsplit=1)[-1].replace("-", "_")
        )

        return cls(
            domain="department_kpi",
            reason=str(getattr(match, "reason", "") or "").strip()
            or "A pergunta solicita um indicador departamental.",
            path_tokens=(path_token,) if path_token else (),
            path_prefixes=(domain_prefix,) if domain_prefix else (),
            operation_tokens=(operation_token,) if operation_token else (),
            parameter_strategy="date_branch",
        )

    @classmethod
    def from_supplies_metric(
        cls,
        *,
        path_token: str,
        operation_token: str,
        reason: str,
    ) -> OperationalApiRouteSpec:
        token = str(path_token or "").lower().strip()
        operation = str(operation_token or "").lower().strip()

        return cls(
            domain="supplies_kpi",
            reason=str(reason or "").strip()
            or "A pergunta solicita um indicador de suprimentos.",
            path_tokens=(token,) if token else (),
            operation_tokens=(operation,) if operation else (),
            parameter_strategy="date_branch",
            prioritize="supplies_otd" if token == "otd" else None,
        )

    @classmethod
    def from_product(
        cls,
        *,
        product_code: str,
        reason: str,
        route_segment: str | None = None,
    ) -> OperationalApiRouteSpec:
        code = str(product_code or "").strip()

        return cls(
            domain="product",
            reason=str(reason or "").strip()
            or "A pergunta solicita informações operacionais de produto via OpenAPI.",
            path_prefixes=("/products/",),
            path_tokens=(f"/{route_segment}",) if route_segment else (),
            parameter_strategy="product_code",
            entity_code=code or None,
            route_segment=route_segment,
        )
