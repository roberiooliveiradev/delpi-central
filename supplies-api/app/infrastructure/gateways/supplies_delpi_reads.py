from __future__ import annotations

from typing import Any

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGateway
from app.infrastructure.gateways.delpi_envelope import summary_dict, unwrap_delpi_envelope


class SuppliesDelpiReads:
    """Typed reads for Overview KPIs against api-delpi supplies routes."""

    def __init__(self, gateway: DelpiApiGateway | None = None) -> None:
        self.gateway = gateway or DelpiApiGateway()

    def _params(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if branch:
            params["branch"] = branch
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if extra:
            params.update(extra)
        return params

    def get_otd(
        self,
        *,
        access_token: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return summary_dict(
            self.gateway.get(
                "/supplies/otd",
                access_token=access_token,
                params=self._params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                    extra={"top_limit": 10, "details_limit": 50},
                ),
            )
        )

    def get_stock_value(
        self,
        *,
        access_token: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return summary_dict(
            self.gateway.get(
                "/supplies/stock-value",
                access_token=access_token,
                params=self._params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                    extra={"summary_only": "true", "top_limit": 20},
                ),
            )
        )

    def get_inventory_turnover(
        self,
        *,
        access_token: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return summary_dict(
            self.gateway.get(
                "/supplies/inventory-turnover",
                access_token=access_token,
                params=self._params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                ),
            )
        )

    def get_cpv(
        self,
        *,
        access_token: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return summary_dict(
            self.gateway.get(
                "/supplies/cpv",
                access_token=access_token,
                params=self._params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                    extra={"top_limit": 15},
                ),
            )
        )

    def get_negotiation_savings(
        self,
        *,
        access_token: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return summary_dict(
            self.gateway.get(
                "/supplies/negotiation-savings/summary",
                access_token=access_token,
                params=self._params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                ),
            )
        )

    def get_safety_stock_summary(
        self,
        *,
        access_token: str,
        branch: str | None,
    ) -> dict[str, Any]:
        data = unwrap_delpi_envelope(
            self.gateway.get(
                "/supplies/safety-stock/summary",
                access_token=access_token,
                params=self._params(
                    branch=branch,
                    start_date=None,
                    end_date=None,
                ),
            )
        )
        return data if isinstance(data, dict) else {}

    def get_purchase_order_otd_series(
        self,
        *,
        access_token: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        granularity: str = "month",
    ) -> dict[str, Any]:
        data = unwrap_delpi_envelope(
            self.gateway.get(
                "/supplies/purchase-order-otd/series",
                access_token=access_token,
                params=self._params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                    extra={"granularity": granularity},
                ),
            )
        )
        return data if isinstance(data, dict) else {}

    def get_purchase_order_otd_panel(
        self,
        *,
        access_token: str,
        branch: str,
        start_date: str | None,
        end_date: str | None,
        status: str | None,
        page: int,
        page_size: int,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> dict[str, Any]:
        """Panel lines for one concrete branch. Never call with branch omitted."""
        concrete = str(branch or "").strip()
        if not concrete:
            raise ValueError("branch is required for purchase-order-otd panel reads")
        extra: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        if status:
            extra["status"] = status
        if sort_by:
            extra["sort_by"] = sort_by
        if sort_dir:
            extra["sort_dir"] = sort_dir
        data = unwrap_delpi_envelope(
            self.gateway.get(
                "/supplies/purchase-order-otd/panel",
                access_token=access_token,
                params=self._params(
                    branch=concrete,
                    start_date=start_date,
                    end_date=end_date,
                    extra=extra,
                ),
            )
        )
        return data if isinstance(data, dict) else {}
