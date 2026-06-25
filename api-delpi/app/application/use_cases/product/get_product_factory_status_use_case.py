from app.application.dto.product.product_playbook_request import ProductPlaybookRequest
from app.application.services.product.product_factory_status_cache import (
    get_cached_product_factory_status,
    product_factory_status_cache_key,
    set_cached_product_factory_status,
)
from app.application.services.product.product_playbook_service import (
    apply_pa_bom_reference_to_production_items,
    apply_pa_bom_reference_to_stock_items,
    attach_pa_reference,
    classify_factory_status,
    resolve_exclusive_end_date,
    resolve_protheus_date,
    summarize_production,
    summarize_raw_material_stock,
    summarize_shipping,
    summarize_structure,
)
from app.domain.ports.product.product_playbook_repository_port import ProductPlaybookRepositoryPort


class GetProductFactoryStatusUseCase:

    DEFAULT_MAX_DEPTH = 50

    def __init__(self, repository: ProductPlaybookRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductPlaybookRequest) -> dict:
        max_depth = request.max_depth or self.DEFAULT_MAX_DEPTH
        cache_key = product_factory_status_cache_key(request, max_depth=max_depth)
        cached = get_cached_product_factory_status(cache_key)
        if cached is not None:
            return cached

        reference_date = resolve_protheus_date(request.reference_date)
        date_start = resolve_protheus_date(request.date_start or reference_date)
        date_end_exclusive = resolve_exclusive_end_date(request.date_end, date_start)

        header = self._repository.fetch_product_header(request.code)
        structure_items = self._repository.fetch_structure_with_exclusivity(
            request.code,
            max_depth,
            reference_date=reference_date,
        )
        stock_items = self._repository.fetch_raw_material_stock(
            request.code,
            max_depth,
            reference_date=reference_date,
        )
        product_unit = str((header or {}).get("unit") or "").strip() or None
        stock_items = apply_pa_bom_reference_to_stock_items(stock_items, product_unit)
        production_items = self._repository.fetch_production_status(
            request.code,
            reference_date,
            max_depth,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.branch,
        )
        production_items = apply_pa_bom_reference_to_production_items(
            production_items,
            product_unit,
        )
        shipping_items = self._repository.fetch_shipping_status(
            request.code,
            date_start,
            date_end_exclusive,
            branch=request.branch,
        )

        structure_summary = summarize_structure(structure_items)
        stock_summary = summarize_raw_material_stock(stock_items, product_unit=product_unit)
        production_summary = summarize_production(production_items)
        shipping_summary = summarize_shipping(shipping_items)

        factory_status = classify_factory_status(
            has_structure=bool(structure_items),
            production_summary=production_summary,
            shipping_summary=shipping_summary,
            shipping_items=shipping_items,
        )

        result = attach_pa_reference(
            {
            "product": header,
            "reference_date": reference_date,
            "date_start": date_start,
            "date_end_exclusive": date_end_exclusive,
            "factory_status": factory_status,
            "structure": {
                "items": structure_items,
                "summary": structure_summary,
            },
            "raw_material_stock": {
                "items": stock_items,
                "summary": stock_summary,
            },
            "production": {
                "items": production_items,
                "summary": production_summary,
            },
            "shipping": {
                "items": shipping_items,
                "summary": shipping_summary,
            },
            "indicators": {
                "total_intermediates": structure_summary["total_intermediates"],
                "total_raw_materials": structure_summary["total_raw_materials"],
                "total_exclusive_raw_materials": structure_summary["total_exclusive_raw_materials"],
                "total_raw_materials_without_stock_for_one_pa": stock_summary[
                    "total_without_stock_for_one_pa"
                ],
                "max_pa_producible_from_stock": stock_summary.get("max_pa_producible_from_stock"),
                "limiting_raw_material_code": stock_summary.get("limiting_raw_material_code"),
                "total_pa_orders": production_summary["total_pa_orders"],
                "total_pi_orders": production_summary["total_pi_orders"],
                "total_pa_reported_quantity": production_summary["total_pa_reported_quantity"],
                "total_pi_reported_quantity": production_summary["total_pi_reported_quantity"],
                "total_pa_shipped_quantity": shipping_summary["total_shipped_quantity"],
                "total_inspection_loss_quantity": shipping_summary[
                    "total_inspection_loss_quantity"
                ],
            },
        },
            header,
        )
        set_cached_product_factory_status(cache_key, result)
        return result
