"""Portal safety stock — BFF over api-delpi safety-stock.

E11 rules:
- capability supplies.access (enforced by route policy)
- branch is a data filter only: all|01|02 (OPERATIONAL_UNITS)
- `all` is forwarded upstream as one scope — no BFF fan-out
- details/suppliers require a concrete branch (01|02)
- producer `authorized_branches` is legacy consumer scope — never
  surfaced; the Portal exposes `branch_catalog` = OPERATIONAL_UNITS
- never recompute classification/deficit/stock fields — passthrough
"""

from __future__ import annotations

from typing import Any

from app.application.security.supplies_permissions import OPERATIONAL_UNITS
from app.application.services.authorization_service import AuthorizationService
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError
from app.infrastructure.gateways.supplies_delpi_reads import SuppliesDelpiReads

ALL_SCOPE = "all"
BRANCH_SCOPES = frozenset({ALL_SCOPE, *OPERATIONAL_UNITS})

ALLOWED_STATUSES = frozenset(
    {
        "without_safety_stock",
        "below_safety_stock",
        "at_safety_stock",
        "above_safety_stock",
    }
)

ALLOWED_SORT_FIELDS = frozenset(
    {
        "product_code",
        "product_description",
        "product_group",
        "unit",
        "safety_stock",
        "primary_stock",
        "work_in_process_stock",
        "deficit_quantity",
        "status",
    }
)

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def _parse_positive_int(raw: str | int | None, *, field: str, default: int) -> int:
    if raw is None or str(raw).strip() == "":
        return default
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}") from exc
    if value < 1:
        raise ValueError(f"Invalid {field}")
    return value


def _parse_bool(raw: str | None, *, default: bool) -> bool:
    if raw is None or str(raw).strip() == "":
        return default
    normalized = str(raw).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError("Invalid boolean filter")


def _clean(value: str | None) -> str | None:
    text = (value or "").strip()
    return text or None


class SafetyStockService:
    def __init__(
        self,
        *,
        delpi_reads: SuppliesDelpiReads | None = None,
        authorization: AuthorizationService | None = None,
    ) -> None:
        self.delpi_reads = delpi_reads or SuppliesDelpiReads()
        self.authorization = authorization or AuthorizationService()

    def _require_access(self, user: EffectiveUser) -> None:
        if not self.authorization.allowed_units(user) and not user.is_superadmin:
            raise AuthorizationError("Forbidden")

    def _scope(self, raw: str | None) -> str:
        """all|01|02 — empty defaults to all. Unknown branch is a 422."""
        text = (raw or "").strip()
        if not text:
            return ALL_SCOPE
        if text in BRANCH_SCOPES:
            return text
        raise ValueError(f"Unknown branch: {text}")

    def _concrete_branch(self, raw: str | None) -> str:
        """Details/suppliers require one concrete operational branch."""
        text = (raw or "").strip()
        if text not in OPERATIONAL_UNITS:
            raise ValueError("A concrete branch (01 or 02) is required")
        return text

    def get_filters(
        self,
        user: EffectiveUser,
        *,
        branch: str | None,
        include_blocked: str | None = None,
    ) -> dict[str, Any]:
        self._require_access(user)
        scope = self._scope(branch)
        blocked = _parse_bool(include_blocked, default=False)
        data = self.delpi_reads.get_safety_stock_filters(
            access_token=user.access_token or "",
            branch=scope,
            include_blocked=blocked,
        )
        if not isinstance(data, dict):
            data = {}
        data.pop("authorized_branches", None)
        data["branch"] = scope
        data["branch_catalog"] = list(OPERATIONAL_UNITS)
        data["all_scope"] = ALL_SCOPE
        return data

    def get_summary(
        self,
        user: EffectiveUser,
        *,
        branch: str | None,
        include_blocked: str | None = None,
        product_group: str | None = None,
        unit: str | None = None,
        search: str | None = None,
        status: str | None = None,
        include_without_safety_stock: str | None = None,
    ) -> dict[str, Any]:
        self._require_access(user)
        scope = self._scope(branch)
        status_code = self._status(status)
        data = self.delpi_reads.get_safety_stock_summary(
            access_token=user.access_token or "",
            branch=scope,
            include_blocked=_parse_bool(include_blocked, default=False),
            product_group=_clean(product_group),
            unit=_clean(unit),
            search=_clean(search),
            status=status_code,
            include_without_safety_stock=_parse_bool(
                include_without_safety_stock, default=True
            ),
        )
        return data if isinstance(data, dict) else {}

    def list_items(
        self,
        user: EffectiveUser,
        *,
        branch: str | None,
        page: str | int | None,
        page_size: str | int | None,
        sort_by: str | None,
        sort_direction: str | None,
        include_blocked: str | None = None,
        product_group: str | None = None,
        unit: str | None = None,
        search: str | None = None,
        status: str | None = None,
        include_without_safety_stock: str | None = None,
    ) -> dict[str, Any]:
        self._require_access(user)
        scope = self._scope(branch)
        page_number = _parse_positive_int(page, field="page", default=DEFAULT_PAGE)
        size = _parse_positive_int(
            page_size, field="page_size", default=DEFAULT_PAGE_SIZE
        )
        if size > MAX_PAGE_SIZE:
            raise ValueError("Invalid page_size")

        resolved_sort = (sort_by or "product_code").strip() or "product_code"
        if resolved_sort not in ALLOWED_SORT_FIELDS:
            raise ValueError("Invalid sort_by")
        direction = (sort_direction or "asc").strip().lower()
        if direction not in {"asc", "desc"}:
            raise ValueError("Invalid sort_direction")

        return self.delpi_reads.get_safety_stock_items(
            access_token=user.access_token or "",
            branch=scope,
            status=self._status(status),
            product_group=_clean(product_group),
            unit=_clean(unit),
            search=_clean(search),
            include_blocked=_parse_bool(include_blocked, default=False),
            include_without_safety_stock=_parse_bool(
                include_without_safety_stock, default=True
            ),
            page=page_number,
            page_size=size,
            sort_by=resolved_sort,
            sort_direction=direction,
        )

    def get_item_details(
        self,
        user: EffectiveUser,
        *,
        code: str,
        branch: str | None,
    ) -> dict[str, Any]:
        self._require_access(user)
        concrete = self._concrete_branch(branch)
        product_code = (code or "").strip()
        if not product_code:
            raise ValueError("Invalid product_code")
        return self.delpi_reads.get_safety_stock_item_details(
            access_token=user.access_token or "",
            branch=concrete,
            product_code=product_code,
        )

    def get_item_suppliers(
        self,
        user: EffectiveUser,
        *,
        code: str,
        branch: str | None,
    ) -> dict[str, Any]:
        self._require_access(user)
        concrete = self._concrete_branch(branch)
        product_code = (code or "").strip()
        if not product_code:
            raise ValueError("Invalid product_code")
        return self.delpi_reads.get_safety_stock_item_suppliers(
            access_token=user.access_token or "",
            branch=concrete,
            product_code=product_code,
        )

    @staticmethod
    def _status(raw: str | None) -> str | None:
        text = (raw or "").strip()
        if not text:
            return None
        if text not in ALLOWED_STATUSES:
            raise ValueError("Invalid status")
        return text
