from datetime import datetime, timedelta

from app.application.services.product.protheus_field_normalizer import is_protheus_yes
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def _to_float(value) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def resolve_protheus_date(value: str | None) -> str:
    if value:
        converted = QueryBuilder().convert_date_to_protheus(value)
        if converted:
            return converted
        raise ValueError("Data inválida. Use YYYY-MM-DD ou DD/MM/YYYY.")

    return datetime.now().strftime("%Y%m%d")


def resolve_exclusive_end_date(value: str | None, fallback_start: str) -> str:
    if value:
        converted = QueryBuilder().convert_date_to_protheus(value)
        if not converted:
            raise ValueError("Data final inválida. Use YYYY-MM-DD ou DD/MM/YYYY.")
        parsed = datetime.strptime(converted, "%Y%m%d")
        return (parsed + timedelta(days=1)).strftime("%Y%m%d")

    parsed = datetime.strptime(fallback_start, "%Y%m%d")
    return (parsed + timedelta(days=1)).strftime("%Y%m%d")


def summarize_structure(items: list[dict]) -> dict:
    pis = [item for item in items if item.get("component_type") == "PI"]
    mps = [item for item in items if item.get("component_type") == "MP"]
    exclusive_mps = [
        item for item in mps if is_protheus_yes(item.get("exclusive_raw_material"))
    ]

    return {
        "total_components": len(items),
        "total_intermediates": len(pis),
        "total_raw_materials": len(mps),
        "total_exclusive_raw_materials": len(exclusive_mps),
    }


def summarize_raw_material_stock(items: list[dict]) -> dict:
    by_code: dict[str, dict] = {}

    for item in items:
        code = item.get("raw_material_code")
        if not code:
            continue

        entry = by_code.setdefault(
            code,
            {
                "raw_material_code": code,
                "raw_material_description": item.get("raw_material_description"),
                "quantity_required_for_one_pa": item.get("quantity_required_for_one_pa"),
                "available_quantity": 0.0,
                "has_stock_for_one_pa": "NAO",
            },
        )
        entry["available_quantity"] += _to_float(item.get("available_quantity"))
        if is_protheus_yes(item.get("has_stock_for_one_pa")):
            entry["has_stock_for_one_pa"] = "SIM"

    without_stock = [
        code
        for code, entry in by_code.items()
        if not is_protheus_yes(entry["has_stock_for_one_pa"])
    ]

    return {
        "total_raw_materials": len(by_code),
        "total_without_stock_for_one_pa": len(without_stock),
        "raw_materials_without_stock_for_one_pa": without_stock,
    }


def summarize_production(items: list[dict]) -> dict:
    pa_items = [item for item in items if item.get("level") == 0]
    pi_items = [item for item in items if item.get("level", 0) > 0]

    def _started_rows(rows: list[dict]) -> list[dict]:
        return [
            row
            for row in rows
            if is_protheus_yes(row.get("production_started"))
        ]

    pa_started = _started_rows(pa_items)
    pi_started = _started_rows(pi_items)

    pa_ops = [row for row in pa_items if row.get("production_order")]
    pi_ops = [row for row in pi_items if row.get("production_order")]

    return {
        "total_pa_orders": len({row.get("production_order") for row in pa_ops if row.get("production_order")}),
        "total_pi_orders": len({row.get("production_order") for row in pi_ops if row.get("production_order")}),
        "pa_production_started": "SIM" if pa_started else "NAO",
        "pi_production_started": "SIM" if pi_started else "NAO",
        "total_pa_reported_quantity": sum(_to_float(row.get("reported_quantity")) for row in pa_items),
        "total_pi_reported_quantity": sum(_to_float(row.get("reported_quantity")) for row in pi_items),
    }


def summarize_shipping(items: list[dict]) -> dict:
    shipped = sum(_to_float(item.get("shipped_quantity")) for item in items)
    loss = sum(_to_float(item.get("inspection_loss_quantity")) for item in items)

    return {
        "total_shipped_quantity": shipped,
        "total_inspection_loss_quantity": loss,
        "total_reports": sum(int(item.get("total_reports") or 0) for item in items),
    }


def build_exclusive_catalog_by_material_items(rows: list[dict]) -> list[dict]:
    return [
        {
            **row,
            "exclusive_raw_material": True,
        }
        for row in rows
    ]


def group_exclusive_catalog_by_finished_product(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}

    for row in rows:
        code = row.get("finished_product_code")
        if not code:
            continue

        entry = grouped.setdefault(
            code,
            {
                "finished_product_code": code,
                "finished_product_description": row.get("finished_product_description"),
                "finished_product_unit": row.get("finished_product_unit"),
                "exclusive_raw_material_count": int(
                    row.get("exclusive_raw_material_count") or 0
                ),
                "exclusive_raw_materials": [],
            },
        )

        mp_code = row.get("raw_material_code")
        if not mp_code:
            continue

        entry["exclusive_raw_materials"].append(
            {
                "raw_material_code": mp_code,
                "raw_material_description": row.get("raw_material_description"),
                "raw_material_unit": row.get("raw_material_unit"),
                "raw_material_group": row.get("raw_material_group"),
            }
        )

    return list(grouped.values())


def group_exclusive_catalog_by_finished_product_from_material_rows(
    rows: list[dict],
    *,
    pa_limit: int,
) -> list[dict]:
    grouped = group_exclusive_catalog_by_finished_product(
        [
            {
                **row,
                "exclusive_raw_material_count": 0,
            }
            for row in rows
        ]
    )

    for entry in grouped:
        materials = entry.get("exclusive_raw_materials") or []
        entry["exclusive_raw_material_count"] = len(materials)

    grouped.sort(key=lambda item: str(item.get("finished_product_code") or ""))
    return grouped[: max(pa_limit, 0)]


def summarize_exclusive_catalog_by_material(
    totals: dict,
    *,
    returned_links: int = 0,
    include_totals: bool = True,
) -> dict:
    from app.domain.constants.product_exclusivity import TEST_FINISHED_PRODUCT_PREFIXES

    summary = {
        "excluded_test_product_prefixes": list(TEST_FINISHED_PRODUCT_PREFIXES),
        "returned_exclusive_links": returned_links,
    }

    if not include_totals:
        summary["totals_available"] = False
        return summary

    summary["totals_available"] = True
    summary["total_exclusive_materials"] = int(totals.get("total_exclusive_materials") or 0)
    summary["total_finished_products_with_exclusive"] = int(
        totals.get("total_finished_products_with_exclusive") or 0
    )
    return summary


def summarize_exclusive_catalog_by_finished_product(
    totals: dict,
    *,
    returned_links: int = 0,
    include_totals: bool = True,
) -> dict:
    summary = {
        "returned_exclusive_links": returned_links,
    }

    if not include_totals:
        summary["totals_available"] = False
        return summary

    summary["totals_available"] = True
    summary["total_finished_products"] = int(
        totals.get("total_finished_products_with_exclusive") or 0
    )
    summary["total_exclusive_links"] = int(totals.get("total_exclusive_links") or 0)
    return summary


def classify_factory_status(
    *,
    has_structure: bool,
    production_summary: dict,
    shipping_summary: dict,
    shipping_items: list[dict],
) -> str:
    if not has_structure:
        return "SEM ESTRUTURA VIGENTE"

    total_orders = (
        production_summary.get("total_pa_orders", 0)
        + production_summary.get("total_pi_orders", 0)
    )
    if total_orders == 0:
        return "ESTRUTURA OK, SEM OP LOCALIZADA"

    production_started = (
        is_protheus_yes(production_summary.get("pa_production_started"))
        or is_protheus_yes(production_summary.get("pi_production_started"))
    )
    if not production_started:
        return "OP ABERTA / NÃO INICIADO"

    shipped = shipping_summary.get("total_shipped_quantity", 0)
    loss = shipping_summary.get("total_inspection_loss_quantity", 0)
    has_inspection_reports = bool(shipping_items)

    if has_inspection_reports and shipped > 0:
        return "PA FINALIZADO / LIBERADO PARA EXPEDIÇÃO"

    if has_inspection_reports and shipped == 0 and loss > 0:
        return "PA INSPECIONADO COM PERDA"

    pa_started = is_protheus_yes(production_summary.get("pa_production_started"))
    pi_started = is_protheus_yes(production_summary.get("pi_production_started"))

    if pi_started and not has_inspection_reports:
        return "INTERMEDIÁRIOS EM PRODUÇÃO / PA NÃO FINALIZADO"

    if pa_started and not has_inspection_reports:
        return "PA PRODUZIDO / AGUARDANDO INSPEÇÃO FINAL"

    return "PRODUÇÃO INICIADA"
