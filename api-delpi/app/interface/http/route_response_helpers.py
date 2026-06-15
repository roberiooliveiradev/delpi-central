"""Respostas HTTP padronizadas com meta semântico (Playbook 10)."""

from __future__ import annotations

from typing import Any

from app.application.services.response_meta_builder import ResponseMetaBuilder
from app.core.responses import success_response
from app.interface.http.kpi_field_labels import infer_scalar_field_formats
from app.interface.http.route_contract_registry import resolve_contract


def api_delpi_success(
    data: Any,
    *,
    operation_id: str,
    message: str = "Operação realizada com sucesso",
    entity: str | None = None,
    shape: str | None = None,
    code: str | None = None,
    fields: dict[str, str] | None = None,
    field_formats: dict[str, str] | None = None,
    sections: list[dict[str, Any]] | None = None,
    related_routes: dict[str, str] | None = None,
):
    resolved_entity, resolved_shape = resolve_contract(
        operation_id,
        entity=entity,
        shape=shape,
    )
    if shape is None and resolved_shape == "scalar":
        resolved_shape = ResponseMetaBuilder.infer_shape(data)

    resolved_related = related_routes or (
        ResponseMetaBuilder.product_related_routes(code) if code else None
    )
    resolved_field_formats = field_formats or infer_scalar_field_formats(fields)
    meta = ResponseMetaBuilder.build(
        operation_id=operation_id,
        entity=resolved_entity,
        shape=resolved_shape,
        pagination=ResponseMetaBuilder.pagination_from_data(data),
        fields=fields,
        field_formats=resolved_field_formats or None,
        related_routes=resolved_related,
        sections=sections,
    )
    return success_response(data=data, message=message, meta=meta)
