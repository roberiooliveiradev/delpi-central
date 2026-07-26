from datetime import datetime, timedelta

from app.application.services.product.product_playbook_service import (
    resolve_exclusive_end_date,
    resolve_protheus_date,
)


def _to_float(value) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def resolve_history_date_range(
    date_start: str | None,
    date_end: str | None,
) -> tuple[str, str]:
    if date_end:
        end_base_str = resolve_protheus_date(date_end)
    else:
        end_base_str = datetime.now().strftime("%Y%m%d")

    end_exclusive = resolve_exclusive_end_date(date_end, end_base_str)

    if date_start:
        start = resolve_protheus_date(date_start)
    else:
        end_base = datetime.strptime(end_base_str, "%Y%m%d")
        start = (end_base - timedelta(days=365)).strftime("%Y%m%d")

    return start, end_exclusive


def enrich_price_history_with_variation(items: list[dict]) -> list[dict]:
    enriched: list[dict] = []
    for index, item in enumerate(items):
        unit_price = _to_float(item.get("unit_price"))
        previous_price = (
            _to_float(items[index + 1].get("unit_price"))
            if index + 1 < len(items)
            else None
        )
        variation_percent = None
        if previous_price is not None and previous_price > 0:
            variation_percent = ((unit_price - previous_price) / previous_price) * 100

        enriched.append(
            {
                **item,
                "unit_price": unit_price,
                "icms_value": _to_float(item.get("icms_value")),
                "icms_rate": _to_float(item.get("icms_rate")),
                "quantity": _to_float(item.get("quantity")),
                "total_value": _to_float(item.get("total_value")),
                "previous_unit_price": previous_price,
                "variation_percent": variation_percent,
            }
        )
    return enriched


def summarize_price_history(items: list[dict]) -> dict:
    if not items:
        return {
            "total_purchases": 0,
            "min_unit_price": None,
            "max_unit_price": None,
            "avg_unit_price": None,
            "last_variation_percent": None,
        }

    prices = [_to_float(item.get("unit_price")) for item in items]
    last_variation = items[0].get("variation_percent") if items else None

    return {
        "total_purchases": len(items),
        "min_unit_price": min(prices),
        "max_unit_price": max(prices),
        "avg_unit_price": sum(prices) / len(prices),
        "last_variation_percent": last_variation,
    }


def summarize_budget_history(items: list[dict]) -> dict:
    requisitions = [item for item in items if item.get("source") == "SC1010"]
    purchase_orders = [item for item in items if item.get("source") == "SC7010"]

    return {
        "total_items": len(items),
        "total_requisitions": len(requisitions),
        "total_purchase_orders": len(purchase_orders),
    }


def classify_price_status(
    *,
    price_history: list[dict],
    last_purchase: dict | None,
) -> str:
    if not price_history and not last_purchase:
        return "SEM HISTORICO DE COMPRA"

    last_variation = None
    if price_history:
        last_variation = price_history[0].get("variation_percent")

    if last_variation is None:
        return "ESTAVEL"

    if -2 <= last_variation <= 2:
        return "ESTAVEL"
    if last_variation > 2:
        return "ALTA DE PRECO"
    return "QUEDA DE PRECO"


def build_indicators(
    *,
    product: dict | None,
    last_purchase: dict | None,
    price_history: list[dict],
) -> dict:
    registered_price = _to_float(product.get("registered_last_purchase_price")) if product else 0.0
    last_nf_price = _to_float(last_purchase.get("unit_price")) if last_purchase else 0.0

    registered_vs_last_nf = None
    if registered_price > 0 and last_nf_price > 0:
        registered_vs_last_nf = ((last_nf_price - registered_price) / registered_price) * 100

    supplier_counts: dict[str, int] = {}
    for item in price_history:
        supplier = str(item.get("supplier_code") or "").strip()
        if supplier:
            supplier_counts[supplier] = supplier_counts.get(supplier, 0) + 1

    dominant_supplier = None
    dominant_share = None
    if supplier_counts and price_history:
        dominant_supplier = max(supplier_counts, key=supplier_counts.get)
        dominant_share = (supplier_counts[dominant_supplier] / len(price_history)) * 100

    return {
        "registered_vs_last_nf_diff_percent": registered_vs_last_nf,
        "dominant_supplier_code": dominant_supplier,
        "dominant_supplier_share_percent": dominant_share,
    }


def build_raw_material_price_intelligence(
    *,
    product: dict | None,
    last_purchase: dict | None,
    price_history_raw: list[dict],
    budget_history_raw: list[dict],
    date_start: str,
    date_end_exclusive: str,
    branch: str | None,
) -> dict:
    price_history_items = enrich_price_history_with_variation(price_history_raw)
    price_summary = summarize_price_history(price_history_items)
    budget_summary = summarize_budget_history(budget_history_raw)
    price_status = classify_price_status(
        price_history=price_history_items,
        last_purchase=last_purchase,
    )
    indicators = build_indicators(
        product=product,
        last_purchase=last_purchase,
        price_history=price_history_items,
    )

    warnings: list[str] = []
    if product and product.get("product_type") not in (None, "", "MP"):
        warnings.append(
            f"Produto cadastrado como {product.get('product_type')}, não MP; "
            "dados de compra retornados mesmo assim."
        )

    return {
        "product": product,
        "start_date": date_start,
        "date_end_exclusive": date_end_exclusive,
        "branch": branch,
        "warnings": warnings,
        "last_purchase": last_purchase,
        "budget_history": {
            "items": budget_history_raw,
            "summary": budget_summary,
        },
        "price_history": {
            "items": price_history_items,
            "summary": price_summary,
        },
        "price_variation": price_summary,
        "price_status": price_status,
        "indicators": indicators,
    }
