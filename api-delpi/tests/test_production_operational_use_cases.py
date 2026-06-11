from unittest.mock import MagicMock

from app.application.dto.production.production_operational_request import (
    ProductionOperationalRequest,
)
from app.application.use_cases.production.get_production_consumption_top_items_use_case import (
    GetProductionConsumptionTopItemsUseCase,
)
from app.application.use_cases.production.get_production_losses_top_materials_use_case import (
    GetProductionLossesTopMaterialsUseCase,
)
from app.application.use_cases.production.get_production_schedule_today_use_case import (
    GetProductionScheduleTodayUseCase,
)
from app.application.use_cases.purchases.get_purchases_top_products_use_case import (
    GetPurchasesTopProductsUseCase,
)


def test_consumption_top_items_use_case_returns_summary() -> None:
    repository = MagicMock()
    repository.fetch_top_items.return_value = [
        {
            "item_code": "10010032",
            "description": "MP TESTE",
            "unit": "KG",
            "real_consumption_qty": 120.0,
        }
    ]

    use_case = GetProductionConsumptionTopItemsUseCase(repository)
    result = use_case.execute(
        ProductionOperationalRequest(
            date_start="2026-03-01",
            date_end="2026-03-31",
            limit=5,
        )
    )

    assert result["group_by"] == "general"
    assert len(result["items"]) == 1
    assert result["summary"]["total_records"] == 1
    assert result["summary"]["period"]["start"] == "20260301"
    repository.fetch_top_items.assert_called_once()


def test_purchases_top_products_use_case_returns_items() -> None:
    repository = MagicMock()
    repository.fetch_top_products.return_value = [
        {
            "product_code": "10080001",
            "description": "PRODUTO",
            "total_quantity": 50.0,
        }
    ]

    use_case = GetPurchasesTopProductsUseCase(repository)
    result = use_case.execute(ProductionOperationalRequest(limit=10))

    assert result["pagination"]["returned"] == 1
    repository.fetch_top_products.assert_called_once()


def test_losses_top_materials_use_case_passes_loss_type() -> None:
    repository = MagicMock()
    repository.fetch_top_materials.return_value = []

    use_case = GetProductionLossesTopMaterialsUseCase(repository)
    result = use_case.execute(ProductionOperationalRequest(loss_type="refugo"))

    assert result["loss_type"] == "refugo"
    kwargs = repository.fetch_top_materials.call_args.kwargs
    assert kwargs["loss_type"] == "refugo"


def test_schedule_today_use_case_uses_reference_date() -> None:
    repository = MagicMock()
    repository.fetch_schedule_today.return_value = [
        {"product_code": "90261255", "planned_qty": 10}
    ]

    use_case = GetProductionScheduleTodayUseCase(repository)
    result = use_case.execute(
        ProductionOperationalRequest(reference_date="2026-06-11", limit=20)
    )

    assert result["reference_date"] == "20260611"
    assert result["items"][0]["product_code"] == "90261255"


def test_orders_open_use_case_returns_items() -> None:
    from app.application.use_cases.production.get_production_orders_open_use_case import (
        GetProductionOrdersOpenUseCase,
    )

    repository = MagicMock()
    repository.fetch_open_orders.return_value = [
        {"production_order": "000001", "pending_qty": 5}
    ]

    use_case = GetProductionOrdersOpenUseCase(repository)
    result = use_case.execute(ProductionOperationalRequest(reference_date="2026-06-11"))

    assert result["items"][0]["production_order"] == "000001"
    repository.fetch_open_orders.assert_called_once()


def test_consumption_validated_use_case_calls_repository() -> None:
    from app.application.use_cases.production.get_production_consumption_top_items_validated_use_case import (
        GetProductionConsumptionTopItemsValidatedUseCase,
    )

    repository = MagicMock()
    repository.fetch_top_items_validated.return_value = []

    use_case = GetProductionConsumptionTopItemsValidatedUseCase(repository)
    use_case.execute(ProductionOperationalRequest(limit=5))

    repository.fetch_top_items_validated.assert_called_once()
