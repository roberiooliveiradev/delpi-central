"""Detector — conjuntos de OP incompletos.

A api-delpi devolve o diff bruto entre a estrutura do produto raiz e as OPs do
conjunto. O que é regra do Portal fica aqui, e vem do catálogo declarativo:
severidade, recorte de emissão e exclusões de negócio.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from production_control_app.application.services.problem_analysis_settings import as_int
from production_control_app.domain.errors import DelpiGatewayError
from production_control_app.domain.ports.problem_detector import (
    DetectorPage,
    DetectorSummary,
)
from production_control_app.domain.ports.production_orders_gateway import (
    ProductionOrdersGateway,
)

DETECTOR_ID = "incomplete-order-sets"

# Um conjunto sem falta nem sobra não chega aqui, então o card só alterna entre
# a severidade de falta e a de sobra.
_DEFAULT_SEVERITY = {"missing": "critical", "extra": "attention", "clear": "ok"}


def _unwrap_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        return data
    return payload if isinstance(payload, dict) else {}


def _text(value: Any) -> str:
    return str(value or "").strip()


class IncompleteOrderSetsDetector:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        settings: dict[str, Any] | None = None,
        today: date | None = None,
    ) -> None:
        self._gateway = gateway
        self._settings = settings or {}
        self._today = today

    @property
    def id(self) -> str:
        return DETECTOR_ID

    # ---------------------------------------------------------------- config

    def _severity_map(self) -> dict[str, str]:
        raw = self._settings.get("severity")
        if not isinstance(raw, dict):
            return dict(_DEFAULT_SEVERITY)
        return {**_DEFAULT_SEVERITY, **{k: str(v) for k, v in raw.items()}}

    def _issued_from(self) -> str | None:
        """Emissão mínima da OP mãe.

        A Delpi tem centenas de conjuntos abertos desde os anos 2000 que nunca
        foram encerrados; sem recorte eles afogam o conjunto furado da semana.
        """
        days = as_int(self._settings.get("issuedFromDays"), 0)
        if days <= 0:
            return None
        reference = self._today or date.today()
        return (reference - timedelta(days=days)).isoformat()

    def _page_size(self, requested: int | None = None) -> int:
        if requested and requested > 0:
            return requested
        return as_int(self._settings.get("pageSize"), 50) or 50

    def _excluded_root_prefixes(self) -> tuple[str, ...]:
        raw = self._settings.get("excludedRootPrefixes")
        if not isinstance(raw, list):
            return ()
        return tuple(_text(item) for item in raw if _text(item))

    def _excluded_component_codes(self) -> frozenset[str]:
        raw = self._settings.get("excludedComponentCodes")
        if not isinstance(raw, list):
            return frozenset()
        return frozenset(_text(item) for item in raw if _text(item))

    # ----------------------------------------------------------- exclusions

    def _keep_set(self, item: dict[str, Any]) -> bool:
        prefixes = self._excluded_root_prefixes()
        root = _text(item.get("root_code"))
        return not (prefixes and root.startswith(prefixes))

    def _filter_components(self, components: Any) -> list[dict[str, Any]]:
        excluded = self._excluded_component_codes()
        if not isinstance(components, list):
            return []
        return [
            component
            for component in components
            if isinstance(component, dict)
            and _text(component.get("product_code")) not in excluded
        ]

    # --------------------------------------------------------------- mapping

    def _map_item(self, item: dict[str, Any]) -> dict[str, Any] | None:
        missing = self._filter_components(item.get("missing_components"))
        extra = self._filter_components(item.get("extra_components"))
        if not missing and not extra:
            return None

        severity_map = self._severity_map()
        severity = severity_map["missing"] if missing else severity_map["extra"]
        set_key = _text(item.get("set_key")) or _text(item.get("set_number"))
        return {
            "id": f"{DETECTOR_ID}:{_text(item.get('branch'))}|{set_key}",
            "kind": DETECTOR_ID,
            "severity": severity,
            "branch": _text(item.get("branch")) or None,
            "set_key": set_key or None,
            "set_number": _text(item.get("set_number")) or None,
            "set_item": _text(item.get("set_item")) or None,
            "root_code": _text(item.get("root_code")) or None,
            "root_description": _text(item.get("root_description")) or None,
            "root_order": _text(item.get("root_order")) or None,
            "due_date": _text(item.get("due_date")) or None,
            "issued_at": _text(item.get("issued_at")) or None,
            "order_count": as_int(item.get("order_count"), 0),
            "open_order_count": as_int(item.get("open_order_count"), 0),
            "expected_component_count": as_int(item.get("expected_component_count"), 0),
            "created_component_count": as_int(item.get("created_component_count"), 0),
            "missing_count": len(missing),
            "extra_count": len(extra),
            "missing_components": missing,
            "extra_components": extra,
        }

    # ------------------------------------------------------------- fetching

    def _fetch(self, *, branch: str, page: int, page_size: int) -> dict[str, Any]:
        try:
            return _unwrap_data(
                self._gateway.fetch_production_order_sets_incomplete(
                    branch=branch,
                    issued_from=self._issued_from(),
                    page=page,
                    page_size=page_size,
                )
            )
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError(
                "Não foi possível conferir os conjuntos de OP."
            ) from exc

    def _summary_from(self, payload: dict[str, Any], items: list[dict[str, Any]]) -> DetectorSummary:
        raw = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}
        total = as_int(raw.get("incomplete_set_count"), 0) or as_int(
            pagination.get("total"), len(items)
        )
        severity_map = self._severity_map()
        missing_sets = as_int(raw.get("missing_set_count"), 0)
        severity = severity_map["clear"]
        if missing_sets > 0:
            severity = severity_map["missing"]
        elif total > 0:
            severity = severity_map["extra"]
        return DetectorSummary(
            count=total,
            severity=severity,
            metrics={
                "checked_set_count": as_int(raw.get("checked_set_count"), 0),
                "missing_set_count": missing_sets,
                "extra_set_count": as_int(raw.get("extra_set_count"), 0),
                "issued_from": self._issued_from(),
            },
        )

    # ---------------------------------------------------------------- public

    def summarize(self, *, branch: str) -> DetectorSummary:
        # Página mínima: o card só precisa dos totais, que vêm no summary.
        payload = self._fetch(branch=branch, page=1, page_size=1)
        return self._summary_from(payload, [])

    def collect(self, *, branch: str, page: int, page_size: int) -> DetectorPage:
        resolved_size = self._page_size(page_size)
        resolved_page = max(page, 1)
        payload = self._fetch(branch=branch, page=resolved_page, page_size=resolved_size)

        raw_items = payload.get("items")
        source = raw_items if isinstance(raw_items, list) else []
        items = [
            mapped
            for entry in source
            if isinstance(entry, dict) and self._keep_set(entry)
            for mapped in [self._map_item(entry)]
            if mapped is not None
        ]
        summary = self._summary_from(payload, items)
        return DetectorPage(
            items=items,
            total=summary.count,
            page=resolved_page,
            page_size=resolved_size,
            summary=summary,
        )
