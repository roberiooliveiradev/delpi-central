"""Validação de dataBinding do pacote TV Deck contra o catálogo local."""

from __future__ import annotations

from typing import Any, Literal

from tv_app.application.services.data.tv_data_param_validation_service import (
    validate_data_binding,
)
from tv_app.application.services.tv_data_route_catalog_service import (
    TvDataRouteCatalogService,
)

BindingSeverity = Literal["ok", "warning", "error"]


class TvDeckBindingValidator:
    def __init__(self, catalog: TvDataRouteCatalogService | None = None) -> None:
        self._catalog = catalog or TvDataRouteCatalogService()

    def validate_index(
        self,
        bindings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Retorna relatório por binding: status ok|warning|error + message."""
        reports: list[dict[str, Any]] = []
        for item in bindings:
            if not isinstance(item, dict):
                continue
            reports.append(self.validate_one(item))
        return reports

    def validate_one(self, item: dict[str, Any]) -> dict[str, Any]:
        operation_id = str(item.get("operationId") or "").strip()
        block_type = str(item.get("blockType") or "data_source").strip() or "data_source"
        params = item.get("params") if isinstance(item.get("params"), dict) else {}
        base = {
            "operationId": operation_id,
            "slideSourceId": item.get("slideSourceId"),
            "blockId": item.get("blockId"),
            "blockType": block_type,
        }
        if not operation_id:
            return {
                **base,
                "status": "warning",
                "message": "Binding sem operationId.",
            }
        route = self._catalog.get_route(operation_id)
        if not route:
            return {
                **base,
                "status": "warning",
                "message": f"Rota não encontrada no catálogo da conta destino: {operation_id}.",
            }
        binding = {
            "operationId": operation_id,
            "params": params,
            "displayMode": item.get("displayMode") or "auto",
        }
        if item.get("maxRows") is not None:
            binding["maxRows"] = item.get("maxRows")
        try:
            validate_data_binding(binding, block_type=block_type, route=route)
        except ValueError as exc:
            return {
                **base,
                "status": "warning",
                "message": str(exc),
            }
        return {
            **base,
            "status": "ok",
            "message": "Binding compatível.",
        }

    @staticmethod
    def has_blocking_errors(
        reports: list[dict[str, Any]],
        *,
        binding_policy: Literal["lenient", "strict"] = "lenient",
    ) -> bool:
        if binding_policy == "strict":
            return any(r.get("status") in {"warning", "error"} for r in reports)
        return any(r.get("status") == "error" for r in reports)
