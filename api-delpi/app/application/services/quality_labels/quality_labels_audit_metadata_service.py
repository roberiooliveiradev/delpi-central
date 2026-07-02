from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.application.dto.product.list_product_guide_request import ListProductGuideRequest
from app.application.dto.product.list_product_inspection_request import (
    ListProductInspectionRequest,
)
from app.application.dto.product.list_product_structured_request import (
    ListProductStructureRequest,
)
from app.application.dto.production.get_production_order_by_op_request import (
    GetProductionOrderByOpRequest,
)
from app.application.use_cases.product.list_product_guide_use_case import (
    ListProductGuideUseCase,
)
from app.application.use_cases.product.list_product_inspection_use_case import (
    ListProductInspectionUseCase,
)
from app.application.use_cases.product.list_product_structure_use_case import (
    ListProductStructureUseCase,
)
from app.application.use_cases.production.get_production_order_by_op_use_case import (
    GetProductionOrderByOpUseCase,
)

_SNAPSHOT_VERSION = 1
_DEFAULT_MAX_DEPTH = 6
_MAX_LINKED_ORDERS = 50


class QualityLabelsAuditMetadataService:
    """Monta snapshot imutável de OP/produto para auditoria futura."""

    def __init__(
        self,
        *,
        production_order_use_case: GetProductionOrderByOpUseCase,
        structure_use_case: ListProductStructureUseCase,
        guide_use_case: ListProductGuideUseCase,
        inspection_use_case: ListProductInspectionUseCase,
        max_depth: int = _DEFAULT_MAX_DEPTH,
    ) -> None:
        self._production_order_use_case = production_order_use_case
        self._structure_use_case = structure_use_case
        self._guide_use_case = guide_use_case
        self._inspection_use_case = inspection_use_case
        self._max_depth = max_depth

    def build(
        self,
        *,
        production_order: str,
        branch: str | None,
    ) -> dict[str, Any]:
        captured_at = datetime.now(UTC).isoformat()
        sources: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []

        op_payload = self._capture_production_order(
            production_order=production_order,
            branch=branch,
            sources=sources,
            errors=errors,
        )
        order = (op_payload or {}).get("order") or {}
        product_code = str(order.get("product_code") or "").strip()
        resolved_branch = order.get("branch") or branch

        product_payload: dict[str, Any] = {"code": product_code or None}
        if product_code:
            self._capture_product_sections(
                product_code=product_code,
                branch=resolved_branch,
                product_payload=product_payload,
                sources=sources,
                errors=errors,
            )

        return {
            "snapshotVersion": _SNAPSHOT_VERSION,
            "capturedAt": captured_at,
            "productionOrder": op_payload,
            "product": product_payload,
            "sources": sources,
            "errors": errors,
        }

    def _capture_production_order(
        self,
        *,
        production_order: str,
        branch: str | None,
        sources: list[dict[str, Any]],
        errors: list[dict[str, str]],
    ) -> dict[str, Any] | None:
        params = {"production_order": production_order, "branch": branch}
        try:
            result = self._production_order_use_case.execute(
                GetProductionOrderByOpRequest(
                    production_order=production_order,
                    branch=branch,
                )
            )
            sources.append(
                {
                    "operationId": "get_production_order_by_op",
                    "params": params,
                    "ok": result is not None,
                }
            )
            if not result:
                return None

            linked = result.get("linked_orders") or []
            if len(linked) > _MAX_LINKED_ORDERS:
                linked = linked[:_MAX_LINKED_ORDERS]

            return {
                "order": result.get("order"),
                "linkSummary": result.get("link_summary"),
                "linkedOrders": linked,
                "linkedOrdersTruncated": len(result.get("linked_orders") or [])
                > _MAX_LINKED_ORDERS,
            }
        except Exception as exc:
            errors.append(
                {
                    "operationId": "get_production_order_by_op",
                    "message": str(exc),
                }
            )
            sources.append(
                {
                    "operationId": "get_production_order_by_op",
                    "params": params,
                    "ok": False,
                }
            )
            return None

    def _capture_product_sections(
        self,
        *,
        product_code: str,
        branch: str | None,
        product_payload: dict[str, Any],
        sources: list[dict[str, Any]],
        errors: list[dict[str, str]],
    ) -> None:
        structure_params = {"code": product_code, "max_depth": self._max_depth}
        try:
            product_payload["structure"] = self._structure_use_case.execute(
                ListProductStructureRequest(
                    code=product_code,
                    max_depth=self._max_depth,
                )
            )
            sources.append(
                {
                    "operationId": "get_product_structure",
                    "params": structure_params,
                    "ok": True,
                }
            )
        except Exception as exc:
            errors.append(
                {"operationId": "get_product_structure", "message": str(exc)}
            )
            sources.append(
                {
                    "operationId": "get_product_structure",
                    "params": structure_params,
                    "ok": False,
                }
            )

        guide_params = {
            "code": product_code,
            "branch": branch,
            "max_depth": self._max_depth,
        }
        try:
            product_payload["routing"] = self._guide_use_case.execute(
                ListProductGuideRequest(
                    code=product_code,
                    branch=branch,
                    max_depth=self._max_depth,
                )
            )
            sources.append(
                {
                    "operationId": "get_product_guide",
                    "params": guide_params,
                    "ok": True,
                }
            )
        except Exception as exc:
            errors.append({"operationId": "get_product_guide", "message": str(exc)})
            sources.append(
                {"operationId": "get_product_guide", "params": guide_params, "ok": False}
            )

        inspection_params = {"code": product_code, "max_depth": self._max_depth}
        try:
            product_payload["inspection"] = self._inspection_use_case.execute(
                ListProductInspectionRequest(
                    code=product_code,
                    max_depth=self._max_depth,
                )
            )
            sources.append(
                {
                    "operationId": "get_product_inspection",
                    "params": inspection_params,
                    "ok": True,
                }
            )
        except Exception as exc:
            errors.append(
                {"operationId": "get_product_inspection", "message": str(exc)}
            )
            sources.append(
                {
                    "operationId": "get_product_inspection",
                    "params": inspection_params,
                    "ok": False,
                }
            )
