from typing import Any

from app.application.services.response_meta_builder import ResponseMetaBuilder
from app.core.responses import success_response

STOCK_FIELD_LABELS = {
    "available_quantity": "Saldo disponível (atual - empenhado - reservado)",
    "current_quantity": "Quantidade atual no armazém",
    "warehouse": "Código do armazém",
    "branch": "Filial",
}


def product_success(
    data: Any,
    *,
    operation_id: str,
    entity: str,
    shape: str,
    code: str | None = None,
    fields: dict[str, str] | None = None,
    sections: list[dict] | None = None,
    message: str = "Operação realizada com sucesso",
):
    related = ResponseMetaBuilder.product_related_routes(code) if code else None
    meta = ResponseMetaBuilder.build(
        operation_id=operation_id,
        entity=entity,
        shape=shape,
        pagination=ResponseMetaBuilder.pagination_from_data(data),
        fields=fields,
        related_routes=related,
        sections=sections,
    )
    return success_response(data=data, message=message, meta=meta)
