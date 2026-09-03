from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from requests_app.application.errors import ApplicationError
from requests_app.domain.ports.payload_validator_port import PayloadValidatorPort

PARTY_TYPES = frozenset({"customer", "supplier"})
INVOICE_TYPES = frozenset({"sale", "return", "sample", "repair_shipment", "other"})
FREIGHT_MODES = frozenset({"cif", "fob"})


def _decimal(value: Any, *, field: str, min_value: Decimal | None = None) -> Decimal:
    try:
        parsed = Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, AttributeError) as exc:
        raise ApplicationError(
            code="payload_invalid",
            status_code=422,
            field=field,
            detail=f"{field} inválido.",
        ) from exc
    if min_value is not None and parsed < min_value:
        raise ApplicationError(
            code="payload_invalid",
            status_code=422,
            field=field,
            detail=f"{field} deve ser maior que {min_value}.",
        )
    return parsed


class InvoiceIssuancePayloadValidator(PayloadValidatorPort):
    """Structural validation for invoice-issuance payloads (no TOTVS round-trip)."""

    type_code = "invoice-issuance"

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ApplicationError(code="payload_required", status_code=422)

        party_type = str(payload.get("party_type") or "").strip()
        party_code = str(payload.get("party_code") or "").strip()
        party_store = str(payload.get("party_store") or "").strip()
        if party_type not in PARTY_TYPES or not party_code or not party_store:
            raise ApplicationError(
                code="payload_invalid",
                status_code=422,
                detail="Informe o destinatário cadastrado (tipo, código e loja).",
            )

        invoice_type = str(payload.get("invoice_type") or "").strip()
        if invoice_type not in INVOICE_TYPES:
            raise ApplicationError(
                code="payload_invalid",
                status_code=422,
                field="invoice_type",
                detail="Tipo de nota fiscal inválido.",
            )
        other = str(payload.get("invoice_type_other") or "").strip() or None
        if invoice_type == "other" and not other:
            raise ApplicationError(
                code="payload_invalid",
                status_code=422,
                field="invoice_type_other",
                detail="Descreva o tipo de nota fiscal.",
            )

        freight = str(payload.get("freight_mode") or "").strip().lower()
        if freight not in FREIGHT_MODES:
            raise ApplicationError(
                code="payload_invalid",
                status_code=422,
                field="freight_mode",
                detail="Informe a modalidade de transporte (CIF ou FOB).",
            )

        weight = _decimal(
            payload.get("weight_kg"),
            field="Peso",
            min_value=Decimal("0.001"),
        )
        try:
            volumes = int(payload.get("volume_count"))
        except (TypeError, ValueError) as exc:
            raise ApplicationError(
                code="payload_invalid",
                status_code=422,
                field="volume_count",
                detail="Informe a quantidade de volumes.",
            ) from exc
        if volumes < 1:
            raise ApplicationError(
                code="payload_invalid",
                status_code=422,
                field="volume_count",
                detail="Informe a quantidade de volumes.",
            )

        raw_items = payload.get("items")
        if not isinstance(raw_items, list) or not raw_items:
            raise ApplicationError(
                code="payload_invalid",
                status_code=422,
                field="items",
                detail="Informe ao menos um item.",
            )
        items: list[dict[str, Any]] = []
        for index, row in enumerate(raw_items, start=1):
            if not isinstance(row, dict):
                raise ApplicationError(
                    code="payload_invalid",
                    status_code=422,
                    detail=f"Item {index} inválido.",
                )
            code = str(row.get("product_code") or "").strip()
            if not code:
                raise ApplicationError(
                    code="payload_invalid",
                    status_code=422,
                    detail=f"Item {index}: informe o código.",
                )
            qty = _decimal(row.get("quantity"), field=f"Item {index} quantidade", min_value=Decimal("0.001"))
            price = _decimal(
                row.get("unit_price"),
                field=f"Item {index} preço",
                min_value=Decimal("0"),
            )
            items.append(
                {
                    "product_code": code,
                    "product_description": str(row.get("product_description") or "").strip() or None,
                    "quantity": str(qty),
                    "unit_price": str(price),
                    "sales_order": str(row.get("sales_order") or "").strip() or None,
                    "sales_order_item": str(row.get("sales_order_item") or "").strip() or None,
                }
            )

        normalized = dict(payload)
        normalized.update(
            {
                "party_type": party_type,
                "party_code": party_code,
                "party_store": party_store,
                "party_name": str(payload.get("party_name") or "").strip() or None,
                "tax_id": str(payload.get("tax_id") or "").strip() or None,
                "invoice_type": invoice_type,
                "invoice_type_other": other,
                "freight_mode": freight,
                "carrier_code": str(payload.get("carrier_code") or "").strip() or None,
                "carrier_name": str(payload.get("carrier_name") or "").strip() or None,
                "weight_kg": str(weight),
                "volume_count": volumes,
                "observation": str(payload.get("observation") or "").strip() or None,
                "stock_write_off": bool(payload.get("stock_write_off")),
                "items": items,
            }
        )
        return normalized
