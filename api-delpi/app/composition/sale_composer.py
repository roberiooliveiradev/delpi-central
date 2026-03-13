# app/composition/sale_composer.py
from app.application.use_cases.sale.list_sale_order_use_case import ListSaleOrderUseCase
from app.infrastructure.persistence.totvs.sale_orders_repositories.sale_order_query_repository import SaleQueryRepository

def build_list_sale_order_use_case() -> ListSaleOrderUseCase:
    repository = SaleQueryRepository()
    return ListSaleOrderUseCase(repository)