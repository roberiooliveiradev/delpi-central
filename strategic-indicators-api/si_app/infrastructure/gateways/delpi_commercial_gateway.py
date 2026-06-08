from __future__ import annotations

from typing import Any, Callable

from si_app.infrastructure.gateways.http_params import std_http_params
from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient


class DelpiCommercialGateway:
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_new_business_rol_pct(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return self._client.get_new_business_rol_pct(
            params=std_http_params(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            ),
            authorization=bearer_authorization_from_context(),
        )

    def get_sales_conversion_rate(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return self._client.get_sales_conversion_rate(
            params=std_http_params(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            ),
            authorization=bearer_authorization_from_context(),
        )

    def get_sales_order_otd(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return self._client.get_sales_order_otd(
            params=std_http_params(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            ),
            authorization=bearer_authorization_from_context(),
        )
