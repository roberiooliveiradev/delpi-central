from unittest.mock import MagicMock

from app.application.use_cases.pedidos_venda_abertos.list_customer_open_order_metrics_use_case import (
    ListCustomerOpenOrderMetricsRequest,
    ListCustomerOpenOrderMetricsUseCase,
)


def test_list_customer_open_order_metrics_maps_rows() -> None:
    repository = MagicMock()
    repository.aggregate_customer_open_order_metrics.return_value = [
        {
            "customer_code": "100",
            "customer_store": "01",
            "customer_name": "Cliente A",
            "open_value": 1500.5,
            "has_overdue": 1,
        },
        {
            "customer_code": "200",
            "customer_store": "01",
            "customer_name": None,
            "open_value": 10,
            "has_overdue": 0,
        },
    ]
    use_case = ListCustomerOpenOrderMetricsUseCase(repository)
    items = use_case.execute(ListCustomerOpenOrderMetricsRequest(customers=(("100", "01"),)))

    repository.aggregate_customer_open_order_metrics.assert_called_once_with(
        [("100", "01")]
    )
    assert len(items) == 2
    assert items[0].customer_code == "100"
    assert items[0].open_value == 1500.5
    assert items[0].has_overdue is True
    assert items[1].has_overdue is False
    assert items[0].to_dict()["customer_name"] == "Cliente A"


def test_list_customer_open_order_metrics_operation_id_in_router() -> None:
    from pathlib import Path

    router = Path(
        "app/interface/http/routes/pedidos_venda_abertos/pedidos_venda_abertos_router.py"
    ).read_text(encoding="utf-8")
    assert "list_customer_open_order_metrics" in router
    assert "/customers/open-order-metrics" in router


def test_aggregate_customer_open_order_metrics_filters_entity_and_blocked() -> None:
    """Semântica CUSTOMER: ignora linhas FORNECEDOR (colisão SA1×SA2 por
    código/loja) e clientes bloqueados/inativos (A1_MSBLQL='1')."""
    from pathlib import Path

    src = Path(
        "app/infrastructure/persistence/totvs/pedidos_venda_abertos/"
        "pedidos_venda_abertos_query_repository.py"
    ).read_text(encoding="utf-8")
    method = src.split("def aggregate_customer_open_order_metrics", 1)[1]
    assert "RTRIM(v.tipo_entidade) = 'CLIENTE'" in method
    assert "RTRIM(SA1.A1_MSBLQL) <> '1'" in method
    # View compartilhada não recebeu filtro global de entidade.
    list_orders = src.split("def list_open_orders(", 1)[1].split(
        "def list_open_orders_for_customer", 1
    )[0]
    assert "tipo_entidade = 'CLIENTE'" not in list_orders
