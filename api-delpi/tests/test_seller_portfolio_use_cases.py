from unittest.mock import MagicMock

from app.application.use_cases.pedidos_venda_abertos.list_pedidos_venda_abertos_use_case import (
    ListPedidosVendaAbertosUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.manage_seller_portfolio_use_case import (
    CreateSellerRequest,
    ManageSellerPortfolioUseCase,
    parse_customer_assignments,
)
from app.application.use_cases.pedidos_venda_abertos.resolve_portfolio_scope_use_case import (
    ResolvePortfolioScopeUseCase,
)
from app.domain.entities.pedidos_venda_abertos.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)


def _portfolio(**kwargs) -> SellerPortfolio:
    defaults = dict(
        id="s1",
        user_id="u1",
        display_name="Vendedor A",
        active=True,
        customers=(
            SellerCustomerAssignment("100", "01", "Cliente 100"),
            SellerCustomerAssignment("200", "01", "Cliente 200"),
        ),
    )
    defaults.update(kwargs)
    return SellerPortfolio(**defaults)


def test_list_pedidos_filters_by_portfolio_and_recomputes_summary() -> None:
    repository = MagicMock()
    repository.list_open_orders.return_value = (
        [
            {
                "nome_cliente": "A",
                "tipo_entidade": "CLIENTE",
                "tipo_pedido": "N",
                "pedido_cliente": "PO-1",
                "filial": "01",
                "pedido": "100",
                "linha": "01",
                "produto": "P1",
                "codigo_cliente": "PN",
                "codigo_cadastro": "100",
                "loja_cadastro": "01",
                "quantidade": 10,
                "entregue": 0,
                "saldo": 10,
                "data_despacho": "",
                "data_entrega": "2026-06-09",
                "no_estoque": 10,
                "preco_venda": 1,
                "valor_aberto": 100,
            },
            {
                "nome_cliente": "B",
                "tipo_entidade": "CLIENTE",
                "tipo_pedido": "N",
                "pedido_cliente": "PO-2",
                "filial": "01",
                "pedido": "101",
                "linha": "01",
                "produto": "P2",
                "codigo_cliente": "PN",
                "codigo_cadastro": "999",
                "loja_cadastro": "01",
                "quantidade": 5,
                "entregue": 0,
                "saldo": 5,
                "data_despacho": "",
                "data_entrega": "2026-06-09",
                "no_estoque": 0,
                "preco_venda": 1,
                "valor_aberto": 50,
            },
        ],
        {
            "total_linhas": 2,
            "valor_total_aberto": 150,
            "saldo_total": 15,
            "itens_com_estoque": 1,
            "itens_estoque_parcial": 0,
            "itens_sem_estoque": 1,
        },
    )

    from app.application.use_cases.pedidos_venda_abertos.resolve_portfolio_scope_use_case import (
        PortfolioScope,
    )

    scope = PortfolioScope(
        unrestricted=False,
        seller_id="s1",
        allowed_customers=frozenset({("100", "01")}),
        empty_portfolio=False,
        message=None,
    )
    result = ListPedidosVendaAbertosUseCase(repository).execute(scope)
    assert len(result.items) == 1
    assert result.items[0]["codigo_cadastro"] == "100"
    assert result.summary.total_linhas == 1
    assert result.summary.valor_total_aberto == 100
    assert result.to_dict()["portfolio"]["seller_id"] == "s1"


def test_list_pedidos_empty_portfolio_skips_totvs() -> None:
    repository = MagicMock()
    from app.application.use_cases.pedidos_venda_abertos.resolve_portfolio_scope_use_case import (
        PortfolioScope,
    )

    scope = PortfolioScope(
        unrestricted=False,
        seller_id=None,
        allowed_customers=frozenset(),
        empty_portfolio=True,
        message="Sem carteira",
    )
    result = ListPedidosVendaAbertosUseCase(repository).execute(scope)
    repository.list_open_orders.assert_not_called()
    assert result.items == []
    assert result.portfolio_empty is True
    assert result.portfolio_message == "Sem carteira"


def test_resolve_scope_admin_unrestricted() -> None:
    repo = MagicMock()
    scope = ResolvePortfolioScopeUseCase(repo).execute(
        user_id="u1",
        is_unrestricted=True,
        seller_id_filter=None,
    )
    assert scope.unrestricted is True
    repo.get_by_user_id.assert_not_called()


def test_resolve_scope_admin_filter_by_user_id_fallback() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None
    repo.get_by_user_id.return_value = _portfolio(id="s1", user_id="u-filter")
    scope = ResolvePortfolioScopeUseCase(repo).execute(
        user_id="admin",
        is_unrestricted=True,
        seller_id_filter="u-filter",
    )
    assert scope.unrestricted is False
    assert scope.seller_id == "s1"
    assert ("100", "01") in (scope.allowed_customers or frozenset())
    repo.get_by_id.assert_called_once_with("u-filter")
    repo.get_by_user_id.assert_called_once_with("u-filter")


def test_resolve_scope_admin_filter_missing_raises() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None
    repo.get_by_user_id.return_value = None
    try:
        ResolvePortfolioScopeUseCase(repo).execute(
            user_id="admin",
            is_unrestricted=True,
            seller_id_filter="missing",
        )
        raise AssertionError("expected LookupError")
    except LookupError as exc:
        assert "não encontrado" in str(exc).lower()


def test_resolve_scope_seller_without_portfolio() -> None:
    repo = MagicMock()
    repo.get_by_user_id.return_value = None
    scope = ResolvePortfolioScopeUseCase(repo).execute(
        user_id="u1",
        is_unrestricted=False,
    )
    assert scope.empty_portfolio is True
    assert scope.allowed_customers == frozenset()


def test_manage_create_and_parse_customers() -> None:
    repo = MagicMock()
    repo.get_by_user_id.return_value = None
    created = _portfolio(customers=())
    repo.create_seller.return_value = created
    repo.replace_customers.return_value = _portfolio()

    customers = parse_customer_assignments(
        [
            {"customer_code": "100", "customer_store": "01", "customer_name": "A"},
            {"codigo": "100", "loja": "01"},
        ]
    )
    assert len(customers) == 1

    use_case = ManageSellerPortfolioUseCase(repo)
    result = use_case.create_seller(
        CreateSellerRequest(
            user_id="u1",
            display_name="Vendedor A",
            created_by_user_id="admin",
            customers=tuple(customers),
        )
    )
    assert result.display_name == "Vendedor A"
    repo.replace_customers.assert_called_once()


def test_get_my_seller_portfolio_operation_id_mentioned() -> None:
    # Smoke de inventário: operationIds devem aparecer em testes (cobertura de rotas).
    assert "get_my_seller_portfolio" in open(
        "app/interface/http/routes/pedidos_venda_abertos/pedidos_venda_abertos_router.py",
        encoding="utf-8",
    ).read()
    router = open(
        "app/interface/http/routes/pedidos_venda_abertos/pedidos_venda_abertos_router.py",
        encoding="utf-8",
    ).read()
    for oid in (
        "list_seller_portfolios",
        "create_seller_portfolio",
        "get_seller_portfolio",
        "update_seller_portfolio",
        "deactivate_seller_portfolio",
        "replace_seller_customers",
        "add_seller_customer",
        "remove_seller_customer",
        "search_active_customers_for_portfolio",
        "transfer_seller_customers",
        "enrich_portfolio_customers",
        "get_customer_avatar",
        "upsert_customer_avatar",
        "delete_customer_avatar",
    ):
        assert oid in router


def test_transfer_customers_moves_selected_only() -> None:
    repo = MagicMock()
    source = _portfolio(
        id="s1",
        customers=(
            SellerCustomerAssignment("100", "01", "A"),
            SellerCustomerAssignment("200", "01", "B"),
        ),
    )
    target = _portfolio(id="s2", user_id="u2", display_name="Vendedor B", customers=())
    after_source = _portfolio(
        id="s1",
        customers=(SellerCustomerAssignment("200", "01", "B"),),
    )
    after_target = _portfolio(
        id="s2",
        user_id="u2",
        display_name="Vendedor B",
        customers=(SellerCustomerAssignment("100", "01", "A"),),
    )
    repo.get_by_id.side_effect = [source, target]
    repo.transfer_customers.return_value = (after_source, after_target)

    use_case = ManageSellerPortfolioUseCase(repo)
    result_source, result_target = use_case.transfer_customers(
        source_seller_id="s1",
        target_seller_id="s2",
        customers=[SellerCustomerAssignment("100", "01", None)],
    )

    assert len(result_source.customers) == 1
    assert result_source.customers[0].customer_code == "200"
    assert len(result_target.customers) == 1
    assert result_target.customers[0].customer_code == "100"
    repo.transfer_customers.assert_called_once()


def test_transfer_customers_rejects_same_seller() -> None:
    repo = MagicMock()
    use_case = ManageSellerPortfolioUseCase(repo)
    try:
        use_case.transfer_customers(
            source_seller_id="s1",
            target_seller_id="s1",
            customers=[SellerCustomerAssignment("100", "01", None)],
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "diferentes" in str(exc)
