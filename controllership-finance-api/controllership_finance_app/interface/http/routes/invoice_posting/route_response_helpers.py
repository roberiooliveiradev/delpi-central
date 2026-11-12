from __future__ import annotations
from typing import Any
from controllership_finance_app.interface.http.routes.invoice_posting.response_meta_builder import ResponseMetaBuilder
from controllership_finance_app.interface.http.routes.invoice_posting.responses import success_response
from controllership_finance_app.interface.http.routes.invoice_posting.route_contract_registry import resolve_contract

def api_delpi_success(data: Any, *, operation_id: str, message: str = "Operação realizada com sucesso", entity: str | None = None, shape: str | None = None, code: str | None = None, fields=None, field_formats=None, sections=None, related_routes=None):
    resolved_entity, resolved_shape = resolve_contract(operation_id, entity=entity, shape=shape)
    if shape is None and resolved_shape == "scalar":
        resolved_shape = ResponseMetaBuilder.infer_shape(data)
    meta = ResponseMetaBuilder.build(
        operation_id=operation_id,
        entity=resolved_entity,
        shape=resolved_shape,
        pagination=ResponseMetaBuilder.pagination_from_data(data),
        fields=fields,
        field_formats=field_formats,
        related_routes=related_routes,
        sections=sections,
    )
    return success_response(data=data, message=message, meta=meta)
