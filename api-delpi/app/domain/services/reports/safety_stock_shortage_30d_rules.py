"""Helpers de domínio — janela de ruptura projetada (Delpi Reports)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Mapping

from app.domain.services.supplies.safety_stock_classification_service import TOLERANCE

PROVIDER_KEY = "safety_stock_shortage_30d"
DEFAULT_HORIZON_DAYS = 30
VALID_BRANCHES = frozenset({"01", "02"})

DATASET_COLUMNS = (
    "product_code",
    "product_description",
    "branch",
    "available_stock",
    "first_shortage_date",
    "shortage_balance",
    "next_purchase",
    "observation",
)

# Colunas do e-mail — filial só no cabeçalho (não repetir na tabela).
EMAIL_COLUMNS = tuple(col for col in DATASET_COLUMNS if col != "branch")

COLUMN_LABELS_PT = {
    "product_code": "Código",
    "product_description": "Descrição",
    "branch": "Filial",
    "available_stock": "Saldo atual",
    "first_shortage_date": "Data da ruptura",
    "shortage_balance": "Saldo no evento",
    "next_purchase": "Próximo Pedido",
    "observation": "Observação",
}

BRANCH_LABELS_PT = {
    "01": "Jaraguá do Sul/SC",
    "02": "Rio Bananal/ES",
}

# Larguras relativas para Outlook.
EMAIL_COLUMN_STYLES: dict[str, str] = {
    "product_description": "min-width:160px;width:26%;",
    "first_shortage_date": "min-width:96px;width:96px;white-space:nowrap;",
    "available_stock": "width:88px;white-space:nowrap;",
    "shortage_balance": "width:96px;white-space:nowrap;",
    "next_purchase": "min-width:168px;width:26%;text-align:center;vertical-align:middle;",
    "observation": "min-width:140px;width:18%;",
}

_NO_ELIGIBLE_ORDER = "Sem pedido elegível"
THIRD_PARTY_MATERIAL_TYPE = "2"
THIRD_PARTY_OBSERVATION_BRANCHES = frozenset({"01"})
_THIRD_PARTY_PARTY_UNKNOWN = "não identificado"
SAMPLE_FINISHED_PRODUCT_PREFIX = "8"
_OBSERVATION_SEPARATOR = " | "


def format_branch_label(branch: Any) -> str:
    """Rótulo de unidade (01/02) para e-mail; desconhecido → código cru."""
    code = str(branch or "").strip()
    if not code:
        return ""
    return BRANCH_LABELS_PT.get(code, code)


def format_date_br(value: Any) -> str:
    """Converte data ISO (ou ``date``) para ``DD/MM/AAAA``; demais valores intactos."""
    if value is None:
        return ""
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    text = str(value).strip()
    if not text:
        return ""
    iso_candidate = text[:10]
    try:
        return date.fromisoformat(iso_candidate).strftime("%d/%m/%Y")
    except ValueError:
        return text


def format_number(value: Any) -> str:
    """Número compacto sem zeros desnecessários (ex.: 50, 12.5)."""
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value).strip()
    if number == int(number):
        return str(int(number))
    text = f"{number:.4g}"
    return text


def format_quantity_with_unit(value: Any, unit: Any) -> str:
    """Quantidade com UM do produto: ``50 MT`` (espaço entre número e unidade)."""
    amount = format_number(value)
    if not amount:
        return ""
    unit_code = str(unit or "").strip()
    if unit_code:
        return f"{amount} {unit_code}"
    return amount


def shortage_date_in_horizon(
    first_shortage_date: str | None,
    *,
    as_of: date,
    horizon_days: int,
) -> bool:
    """Inclui só se ``first_shortage_date`` ∈ ``[as_of, as_of + horizon_days]``."""
    if not first_shortage_date:
        return False
    try:
        shortage = date.fromisoformat(str(first_shortage_date).strip()[:10])
    except ValueError:
        return False
    end = as_of + timedelta(days=max(int(horizon_days), 0))
    return as_of <= shortage <= end


def balance_at_first_shortage(projection: Mapping[str, Any]) -> float | None:
    """``running_balance`` no primeiro evento com saldo projetado negativo."""
    for row in projection.get("items") or []:
        running = float(row.get("running_balance") or 0)
        if running + TOLERANCE < 0:
            return running
    return None


def has_open_projection_commitment(
    enriched_commitments: list[Mapping[str, Any]] | None,
) -> bool:
    """True se existe empenho elegível à projeção (demanda real em aberto)."""
    for raw in enriched_commitments or []:
        if not raw.get("projection_eligible"):
            continue
        try:
            qty = float(raw.get("open_quantity_primary_unit") or 0)
        except (TypeError, ValueError):
            continue
        if qty > TOLERANCE:
            return True
    return False


def is_third_party_material(material_type: Any) -> bool:
    """B1_TPMAT = 2 → material fornecido por terceiro."""
    return str(material_type or "").strip() == THIRD_PARTY_MATERIAL_TYPE


def should_annotate_third_party_observation(*, branch: Any, material_type: Any) -> bool:
    """Observação de terceiro só na filial 01 (cenário operacional atual)."""
    branch_code = str(branch or "").strip()
    return (
        branch_code in THIRD_PARTY_OBSERVATION_BRANCHES
        and is_third_party_material(material_type)
    )


def build_third_party_observation(party_name: Any) -> str:
    name = str(party_name or "").strip() or _THIRD_PARTY_PARTY_UNKNOWN
    return f"Material de terceiro - {name}"


def finished_product_code_at_first_shortage(projection: Mapping[str, Any]) -> str:
    """Código do PA no evento que leva o saldo projetado ao primeiro negativo."""
    for row in projection.get("items") or []:
        try:
            running = float(row.get("running_balance") or 0)
        except (TypeError, ValueError):
            continue
        if running + TOLERANCE < 0:
            return str(row.get("finished_product_code") or "").strip()
    return ""


def is_sample_finished_product(finished_product_code: Any) -> bool:
    """PA de amostra: código começa com 8."""
    code = str(finished_product_code or "").strip()
    return bool(code) and code.startswith(SAMPLE_FINISHED_PRODUCT_PREFIX)


def build_sample_observation(finished_product_code: Any) -> str:
    code = str(finished_product_code or "").strip()
    if not code:
        return ""
    return f"AMOSTRA - {code}"


def compose_observation_parts(*parts: Any) -> str:
    cleaned = [str(part).strip() for part in parts if str(part or "").strip()]
    return _OBSERVATION_SEPARATOR.join(cleaned)


def observation_from_summary(summary: Mapping[str, Any]) -> str:
    warnings = summary.get("warnings") or []
    if not isinstance(warnings, (list, tuple)):
        return ""
    parts = [str(item).strip() for item in warnings if str(item).strip()]
    return " | ".join(parts)


def next_eligible_purchase_order(
    enriched_orders: list[Mapping[str, Any]] | None,
) -> dict[str, Any] | None:
    """Pedido cobertura-elegível com a menor data de entrega prevista."""
    candidates: list[dict[str, Any]] = []
    for raw in enriched_orders or []:
        if not raw.get("coverage_eligible"):
            continue
        candidates.append(dict(raw))
    if not candidates:
        return None

    def _sort_key(order: Mapping[str, Any]) -> tuple[str, str, str]:
        delivery = str(order.get("expected_delivery_date") or "").strip()
        delivery_key = delivery if delivery else "9999-99-99"
        return (
            delivery_key,
            str(order.get("order_number") or "").strip(),
            str(order.get("order_item") or "").strip(),
        )

    return min(candidates, key=_sort_key)


def format_purchase_order_ref(order: Mapping[str, Any]) -> str:
    number = str(order.get("order_number") or "").strip()
    item = str(order.get("order_item") or "").strip()
    if number and item:
        return f"{number}/{item}"
    return number or "—"


def _order_quantity_in_product_unit(order: Mapping[str, Any]) -> Any:
    """Preferência: quantidade já convertida para UM do produto."""
    primary = order.get("open_quantity_primary_unit")
    if primary is not None:
        return primary
    return order.get("open_quantity")


def format_next_eligible_purchase_lines(
    order: Mapping[str, Any] | None,
    *,
    product_unit: Any = None,
) -> list[str]:
    """Linhas do Próximo Pedido: pedido, fornecedor, entrega, quantidade."""
    if order is None:
        return [_NO_ELIGIBLE_ORDER]
    supplier = (
        str(order.get("supplier_name") or "").strip()
        or str(order.get("supplier_code") or "").strip()
        or "—"
    )
    delivery = format_date_br(order.get("expected_delivery_date")) or "—"
    lines = [
        format_purchase_order_ref(order),
        supplier,
        f"Entrega {delivery}",
    ]
    qty = format_quantity_with_unit(
        _order_quantity_in_product_unit(order),
        product_unit,
    )
    if qty:
        lines.append(qty)
    return lines


def build_next_purchase_text(
    *,
    enriched_orders: list[Mapping[str, Any]] | None,
    product_unit: Any = None,
    summary: Mapping[str, Any] | None = None,
) -> str:
    """Texto plano da coluna Próximo Pedido (+ avisos técnicos, se houver)."""
    lines = format_next_eligible_purchase_lines(
        next_eligible_purchase_order(enriched_orders),
        product_unit=product_unit,
    )
    primary = " — ".join(lines)
    warnings = observation_from_summary(summary or {})
    if warnings:
        return f"{primary} | {warnings}"
    return primary


# Compatível com imports/testes anteriores.
def build_shortage_observation(
    *,
    summary: Mapping[str, Any],
    enriched_orders: list[Mapping[str, Any]] | None,
    product_unit: Any = None,
) -> str:
    return build_next_purchase_text(
        enriched_orders=enriched_orders,
        product_unit=product_unit,
        summary=summary,
    )
