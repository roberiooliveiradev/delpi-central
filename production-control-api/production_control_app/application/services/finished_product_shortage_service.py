"""Consulta de ruptura de MP no conjunto do PA.

A api-delpi entrega o pegging (BOM MP + extrato + OPs mãe). Este BFF
autoriza, valida o código, classifica o estado de tela e cacheia.
"""

from __future__ import annotations

import re
import time
from typing import Any

from production_control_app.application.services.materials_settings import (
    setting_int,
    setting_list,
    setting_map,
    setting_str,
)
from production_control_app.core.security import PC_MATERIALS_VIEW, can
from production_control_app.domain.errors import DelpiGatewayError, InvalidProductCode
from production_control_app.domain.ports.production_orders_gateway import (
    ProductionOrdersGateway,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService

_PRODUCT_DIGITS = re.compile(r"^\d+$")
_SET_STATUSES = frozenset({"shortage", "no_commitment", "ok", "all"})
_STATE_OK = "ok"
_STATE_NOT_FOUND = "not_found"
_STATE_NOT_FINISHED = "not_finished_product"
_STATE_NO_OPEN_SETS = "no_open_sets"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _unwrap_data(payload: Any) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    return data if isinstance(data, dict) else payload if isinstance(payload, dict) else {}


def _format_state(key: str, *, code: str) -> str:
    states = setting_map("states")
    template = _text(states.get(key))
    return template.format(code=code) if template else key


class _ShortageCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = max(ttl_seconds, 0)
        self._entries: dict[str, tuple[float, dict[str, Any]]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, payload = entry
        if self._ttl and (time.monotonic() - stored_at) > self._ttl:
            self._entries.pop(key, None)
            return None
        return payload

    def set(self, key: str, payload: dict[str, Any]) -> None:
        self._entries[key] = (time.monotonic(), payload)


_CACHE = _ShortageCache(setting_int("cacheTtlSeconds", 120))


class FinishedProductShortageService:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        branch_access: BranchAccessService | None = None,
        cache: _ShortageCache | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()
        self._cache = cache if cache is not None else _CACHE

    def _authorize(self, user: object | None, *, branch: str) -> None:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_MATERIALS_VIEW):
            raise PermissionError("Você não tem permissão para ver os materiais.")

    def _normalize_product(self, product: str) -> str:
        code = _text(product)
        minimum = setting_int("minProductDigits", 8)
        if len(code) < minimum or not _PRODUCT_DIGITS.fullmatch(code):
            raise InvalidProductCode(_format_state("invalidCode", code=code))
        return code

    def _normalize_status(self, status: str | None) -> str:
        requested = _text(status).lower()
        allowed = set(setting_list("setStatuses")) or _SET_STATUSES
        if requested in allowed:
            return requested
        return "all"

    def _load_dump(
        self, *, branch: str, product: str, refresh: bool
    ) -> dict[str, Any]:
        cache_key = f"{branch}:{product}"
        if not refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
        try:
            raw = self._gateway.fetch_finished_product_shortages(
                product_code=product, branch=branch
            )
            dump = _unwrap_data(raw)
        except DelpiGatewayError as exc:
            if exc.status_code == 404:
                dump = {"state": _STATE_NOT_FOUND}
            else:
                raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError(
                "Não foi possível consultar a ruptura de matéria-prima no conjunto."
            ) from exc
        self._cache.set(cache_key, dump)
        return dump

    def get_shortages(
        self,
        user: object | None,
        *,
        branch: str,
        product: str,
        status: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        code = self._branch_access.assert_valid_branch(branch)
        self._authorize(user, branch=code)
        product_code = self._normalize_product(product)
        status_filter = self._normalize_status(status)
        dump = self._load_dump(branch=code, product=product_code, refresh=refresh)
        return self._present(
            dump,
            branch=code,
            product_code=product_code,
            status_filter=status_filter,
        )

    def _present(
        self,
        dump: dict[str, Any],
        *,
        branch: str,
        product_code: str,
        status_filter: str,
    ) -> dict[str, Any]:
        product = dump.get("product") if isinstance(dump.get("product"), dict) else None
        sets = dump.get("sets") if isinstance(dump.get("sets"), list) else []
        materials = dump.get("materials") if isinstance(dump.get("materials"), list) else []
        summary = dump.get("summary") if isinstance(dump.get("summary"), dict) else {}
        product_type = _text((product or {}).get("product_type"))
        finished_type = setting_str("finishedProductType", "PA")

        if dump.get("state") == _STATE_NOT_FOUND or (
            product is None and not sets and not summary
        ):
            state = _STATE_NOT_FOUND
            message = _format_state("notFound", code=product_code)
        elif product is not None and product_type and product_type != finished_type:
            state = _STATE_NOT_FINISHED
            message = _format_state("notFinishedProduct", code=product_code)
            sets = []
        elif not sets:
            state = _STATE_NO_OPEN_SETS
            message = _format_state("noOpenSets", code=product_code)
        else:
            state = _STATE_OK
            message = ""

        visible = [
            item
            for item in sets
            if status_filter == "all" or _text(item.get("status")) == status_filter
        ]

        return {
            "branch": branch,
            "state": state,
            "message": message,
            "product": product
            or {"product_code": product_code, "product_description": "", "product_type": ""},
            "summary": {
                "open_set_count": int(summary.get("open_set_count") or 0),
                "at_risk_set_count": int(summary.get("at_risk_set_count") or 0),
                "short_mp_count": int(summary.get("short_mp_count") or 0),
                "first_shortage_date": summary.get("first_shortage_date"),
                "ok_set_count": int(summary.get("ok_set_count") or 0),
                "no_commitment_set_count": int(summary.get("no_commitment_set_count") or 0),
            },
            "sets": visible,
            "materials": materials,
            "didactic": setting_map("didactic"),
            "filters": {
                "product": product_code,
                "status": status_filter,
            },
        }
