from typing import Any

from app.interface.http.route_response_helpers import api_delpi_success

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
    sections: list[dict[str, Any]] | None = None,
    message: str = "Operação realizada com sucesso",
):
    return api_delpi_success(
        data,
        operation_id=operation_id,
        entity=entity,
        shape=shape,
        code=code,
        fields=fields,
        sections=sections,
        message=message,
    )
