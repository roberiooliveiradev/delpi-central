"""Fachada: materialize do Data Builder → ops TvCopilotPatchV1 (sem segundo pipeline)."""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.tv_data_builder_service import TvDataBuilderService
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def materialize_session_to_copilot_ops(
    session_id: str,
    *,
    catalog: TvDataRouteCatalogService | None = None,
) -> dict[str, Any]:
    """Converte rascunho do builder em ops tipadas (upsert_data_source + transforms)."""
    service = TvDataBuilderService(catalog or TvDataRouteCatalogService())
    materialized = service.materialize(session_id)
    if materialized is None:
        return {"ok": False, "ops": [], "message": "session_not_found"}
    if not materialized.get("ok"):
        return {
            "ok": False,
            "ops": [],
            "message": materialized.get("message"),
            "draft": materialized.get("draft"),
        }

    ops: list[dict[str, Any]] = []
    for block in materialized.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        binding = block.get("dataBinding") if isinstance(block.get("dataBinding"), dict) else {}
        op: dict[str, Any] = {
            "op": "upsert_data_source",
            "blockId": str(block.get("localId") or block.get("id") or ""),
            "operationId": binding.get("operationId"),
            "params": dict(binding.get("params") or {}),
            "label": binding.get("label"),
            "displayMode": binding.get("displayMode") or "auto",
        }
        if isinstance(block.get("dataTransform"), dict):
            op["dataTransform"] = block["dataTransform"]
        ops.append(op)

    return {
        "ok": True,
        "ops": ops,
        "primaryLocalId": materialized.get("primaryLocalId"),
        "preferredView": materialized.get("preferredView"),
        "draft": materialized.get("draft"),
    }
