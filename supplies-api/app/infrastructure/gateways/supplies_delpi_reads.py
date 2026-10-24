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

    def get_purchase_orders(
        self,
        *,
        access_token: str,
        branches: list[str],
        late_only: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Open PO lines list (summary ignores late_only/pagination — owner rule)."""
        codes = [str(code).strip() for code in branches if str(code).strip()]
        if not codes:
            raise ValueError("at least one concrete branch is required")
        params: dict[str, Any] = {
            "branch": codes,
            "page": page,
            "page_size": page_size,
        }
        if late_only:
            params["late_only"] = "true"
        data = unwrap_delpi_envelope(
            self.gateway.get(
                "/supplies/purchase-orders",
                access_token=access_token,
                params=params,
            )
        )
        return data if isinstance(data, dict) else {}

    def get_safety_stock_filters(
        self,
        *,
        access_token: str,
        branch: str | None,
        include_blocked: bool = False,
    ) -> dict[str, Any]:
        data = unwrap_delpi_envelope(
            self.gateway.get(
                "/supplies/safety-stock/filters",
                access_token=access_token,
                params={
                    "branch": branch or "all",
                    "includeBlocked": "true" if include_blocked else "false",
                },
            )
        )
        return data if isinstance(data, dict) else {}

    def get_safety_stock_summary(
        self,
        *,
        access_token: str,
        branch: str | None,
        include_blocked: bool | None = None,
        product_group: str | None = None,
        unit: str | None = None,
        search: str | None = None,
        status: str | None = None,
        include_without_safety_stock: bool | None = None,
    ) -> dict[str, Any]:
        extra: dict[str, Any] = {}
        if include_blocked is not None:
            extra["includeBlocked"] = "true" if include_blocked else "false"
        if product_group:
            extra["productGroup"] = product_group
        if unit:
            extra["unit"] = unit
        if search:
            extra["search"] = search
        if status:
            extra["status"] = status
        if include_without_safety_stock is not None:
            extra["includeWithoutSafetyStock"] = (
                "true" if include_without_safety_stock else "false"
            )
        data = unwrap_delpi_envelope(
            self.gateway.get(
                "/supplies/safety-stock/summary",
                access_token=access_token,
                params=self._params(
                    branch=branch,
                    start_date=None,
                    end_date=None,
                    extra=extra or None,
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

    def _stock_balances_params(
        self,
        *,
        branches: list[str],
        warehouse: str | None,
        only_positive: bool,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        codes = [str(code).strip() for code in branches if str(code).strip()]
        if not codes:
            raise ValueError("at least one concrete branch is required")
        params: dict[str, Any] = {
            "branch": codes,
            "only_positive": "true" if only_positive else "false",
        }
        if warehouse:
            params["warehouse"] = warehouse
        if extra:
            params.update(extra)
        return params

    def get_stock_balances_summary(
        self,
        *,
        access_token: str,
        branches: list[str],
        warehouse: str | None = None,
        only_positive: bool = False,
    ) -> dict[str, Any]:
        """Stock balances summary. Always send concrete branch list (never omit/all)."""
        data = unwrap_delpi_envelope(
            self.gateway.get(
                "/supplies/stock-balances/summary",
                access_token=access_token,
                params=self._stock_balances_params(
                    branches=branches,
                    warehouse=warehouse,
                    only_positive=only_positive,
                ),
            )
        )
        return data if isinstance(data, dict) else {}

    def get_stock_balances_items(
        self,
        *,
        access_token: str,
        branches: list[str],
        warehouse: str | None = None,
        only_positive: bool = False,
        page: int = 1,
        page_size: int = 50,
        sort: str = "stock_value_desc",
    ) -> dict[str, Any]:
        """Paged stock balance items. Always send concrete branch list."""
        data = unwrap_delpi_envelope(
            self.gateway.get(
                "/supplies/stock-balances/items",
                access_token=access_token,
                params=self._stock_balances_params(
                    branches=branches,
                    warehouse=warehouse,
                    only_positive=only_positive,
                    extra={
                        "page": page,
                        "page_size": page_size,
                        "sort": sort,
                    },
                ),
            )
        )
        return data if isinstance(data, dict) else {}

    def get_safety_stock_items(
        self,
        *,
        access_token: str,
        branch: str,
        status: str | None = None,
        product_group: str | None = None,
        unit: str | None = None,
        search: str | None = None,
        include_blocked: bool | None = None,
        include_without_safety_stock: bool | None = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str | None = None,
        sort_direction: str | None = None,
    ) -> dict[str, Any]:
        """Safety-stock items for one branch scope (all|01|02)."""
        concrete = str(branch or "").strip()
        if not concrete:
            raise ValueError("branch is required for safety-stock items reads")
        params: dict[str, Any] = {
            "branch": concrete,
            "page": page,
            "page_size": page_size,
        }
        if status:
            params["status"] = status
        if product_group:
            params["productGroup"] = product_group
        if unit:
            params["unit"] = unit
        if search:
            params["search"] = search
        if include_blocked is not None:
            params["includeBlocked"] = "true" if include_blocked else "false"
        if include_without_safety_stock is not None:
            params["includeWithoutSafetyStock"] = (
                "true" if include_without_safety_stock else "false"
            )
        if sort_by:
            params["sortBy"] = sort_by
        if sort_direction:
            params["sortDirection"] = sort_direction
        data = unwrap_delpi_envelope(
            self.gateway.get(
                "/supplies/safety-stock/items",
                access_token=access_token,
                params=params,
            )
        )
        return data if isinstance(data, dict) else {}

    def get_safety_stock_item_details(
        self,
        *,
        access_token: str,
        branch: str,
        product_code: str,
    ) -> dict[str, Any]:
        """Item details; requires one concrete branch (producer computes peer)."""
        concrete = str(branch or "").strip()
        if not concrete:
            raise ValueError("branch is required for safety-stock item details")
        data = unwrap_delpi_envelope(
            self.gateway.get(
                f"/supplies/safety-stock/items/{product_code}/details",
                access_token=access_token,
                params={"branch": concrete},
            )
        )
        return data if isinstance(data, dict) else {}

    def get_safety_stock_item_suppliers(
        self,
        *,
        access_token: str,
        branch: str,
        product_code: str,
    ) -> dict[str, Any]:
        """Linked suppliers for one item under a concrete branch."""
        concrete = str(branch or "").strip()
        if not concrete:
            raise ValueError("branch is required for safety-stock item suppliers")
        data = unwrap_delpi_envelope(
            self.gateway.get(
                f"/supplies/safety-stock/items/{product_code}/suppliers",
                access_token=access_token,
                params={"branch": concrete},
            )
        )
        return data if isinstance(data, dict) else {}
