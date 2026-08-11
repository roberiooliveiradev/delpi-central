from unittest.mock import MagicMock

from commercial_app.application.use_cases.manage_seller_portfolio import (
    CreatePortfolioRequest,
    ManageSellerPortfolioUseCase,
    parse_customer_assignments,
)
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)


def _portfolio(**kwargs) -> SellerPortfolio:
    defaults = dict(
        id="p1",
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


def test_create_portfolio_rejects_duplicate_user() -> None:
    repository = MagicMock()
    repository.get_by_user_id.return_value = _portfolio()
    use_case = ManageSellerPortfolioUseCase(repository)

    try:
        use_case.create_portfolio(
            CreatePortfolioRequest(user_id="u1", display_name="Novo")
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Já existe vendedor" in str(exc)


def test_transfer_customers_requires_reason_note() -> None:
    repository = MagicMock()
    repository.get_by_id.side_effect = [
        _portfolio(id="p1"),
        _portfolio(id="p2", user_id="u2", display_name="Destino"),
    ]
    use_case = ManageSellerPortfolioUseCase(repository)

    try:
        use_case.transfer_customers(
            source_portfolio_id="p1",
            target_portfolio_id="p2",
            customers=[SellerCustomerAssignment("100", "01")],
            actor_user_id="admin",
            reason_note="",
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "reason_note" in str(exc)


def test_transfer_customers_writes_audit_when_configured() -> None:
    repository = MagicMock()
    source = _portfolio(id="p1")
    target = _portfolio(id="p2", user_id="u2", display_name="Destino")
    repository.get_by_id.side_effect = [source, target, source, target]
    repository.transfer_customers.return_value = (source, target)
    audit = MagicMock()

    use_case = ManageSellerPortfolioUseCase(repository, audit_repository=audit)
    result = use_case.transfer_customers(
        source_portfolio_id="p1",
        target_portfolio_id="p2",
        customers=[SellerCustomerAssignment("100", "01")],
        actor_user_id="admin-1",
        reason_note="Reorganização comercial",
    )

    assert result[0].id == "p1"
    audit.append.assert_called_once()
    payload = audit.append.call_args.kwargs["payload"]
    assert payload["reason_note"] == "Reorganização comercial"
    assert payload["transferred_count"] == 1


def test_purge_portfolio_writes_audit_and_returns_snapshot() -> None:
    repository = MagicMock()
    current = _portfolio(id="p1")
    repository.get_by_id.return_value = current
    repository.delete_portfolio.return_value = current
    audit = MagicMock()
    use_case = ManageSellerPortfolioUseCase(repository, audit_repository=audit)

    deleted = use_case.purge_portfolio("p1", actor_user_id="admin-1")

    assert deleted.id == "p1"
    repository.delete_portfolio.assert_called_once_with("p1")
    audit.append.assert_called_once()
    kwargs = audit.append.call_args.kwargs
    assert kwargs["action"] == "seller_portfolio.purge"
    assert kwargs["entity_id"] == "p1"
    assert kwargs["payload"]["customer_count"] == 2
    assert kwargs["payload"]["user_id"] == "u1"


def test_purge_portfolio_missing_raises() -> None:
    repository = MagicMock()
    repository.get_by_id.return_value = None
    use_case = ManageSellerPortfolioUseCase(repository)

    try:
        use_case.purge_portfolio("missing", actor_user_id="admin-1")
        assert False, "expected LookupError"
    except LookupError as exc:
        assert "não encontrado" in str(exc)
    repository.delete_portfolio.assert_not_called()


def test_parse_customer_assignments_deduplicates() -> None:
    parsed = parse_customer_assignments(
        [
            {"customer_code": "100", "customer_store": "01"},
            {"customer_code": "100", "customer_store": "01", "customer_name": "Dup"},
        ]
    )
    assert len(parsed) == 1
    assert parsed[0].customer_code == "100"
