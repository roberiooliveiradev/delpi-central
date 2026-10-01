"""Elegibilidade SA1 em writes de carteira: cliente inexistente ou bloqueado
(A1_MSBLQL='1') não pode receber vínculo — backend é a autoridade final."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from commercial_app.application.use_cases.manage_seller_portfolio import (
    CreatePortfolioRequest,
    ManageSellerPortfolioUseCase,
)
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)
from commercial_app.domain.ports.customer_eligibility_port import (
    CustomerEligibility,
    CustomerEligibilityPort,
)


class FakeEligibility(CustomerEligibilityPort):
    def __init__(self, mapping: dict[tuple[str, str], CustomerEligibility]):
        self._mapping = mapping
        self.calls: list[list[tuple[str, str]]] = []

    def lookup(self, customers):
        keys = list(customers)
        self.calls.append(keys)
        return {k: v for k, v in self._mapping.items() if k in keys}


def _portfolio(**kwargs) -> SellerPortfolio:
    defaults = dict(
        id="p1",
        user_id="u1",
        display_name="Vendedor A",
        active=True,
        customers=(
            SellerCustomerAssignment("000006", "01", "AGC"),
            SellerCustomerAssignment("000001", "01", "Cliente 1"),
        ),
        members=(SellerPortfolioMember(user_id="u1", role="owner"),),
    )
    defaults.update(kwargs)
    return SellerPortfolio(**defaults)


def _use_case(
    eligibility: CustomerEligibilityPort | None,
    repository: MagicMock | None = None,
) -> tuple[ManageSellerPortfolioUseCase, MagicMock]:
    repo = repository or MagicMock()
    repo.list_portfolios.return_value = []
    return ManageSellerPortfolioUseCase(repo, customer_eligibility=eligibility), repo


# -- CASO 9: vínculo rejeitado no backend -----------------------------------


def test_add_customer_rejects_blocked_customer() -> None:
    eligibility = FakeEligibility(
        {("000006", "01"): CustomerEligibility(exists=True, active=False)}
    )
    use_case, repo = _use_case(eligibility)

    with pytest.raises(ValueError, match="bloqueado"):
        use_case.add_customer(
            portfolio_id="p1",
            customer=SellerCustomerAssignment("000006", "01", "AGC"),
        )
    repo.add_customer.assert_not_called()


def test_add_customer_rejects_unknown_customer() -> None:
    eligibility = FakeEligibility({})
    use_case, repo = _use_case(eligibility)

    with pytest.raises(ValueError, match="não encontrado"):
        use_case.add_customer(
            portfolio_id="p1",
            customer=SellerCustomerAssignment("999999", "01", "???"),
        )
    repo.add_customer.assert_not_called()


def test_add_customer_allows_active_customer() -> None:
    eligibility = FakeEligibility(
        {("000001", "01"): CustomerEligibility(exists=True, active=True)}
    )
    repo = MagicMock()
    repo.list_portfolios.return_value = []
    updated = _portfolio()
    repo.add_customer.return_value = updated
    use_case, _ = _use_case(eligibility, repository=repo)

    result = use_case.add_customer(
        portfolio_id="p1",
        customer=SellerCustomerAssignment("000001", "01", "Cliente 1"),
    )

    assert result.portfolio is updated
    repo.add_customer.assert_called_once()


def test_add_customer_without_port_skips_validation() -> None:
    """Porta ausente = modo legado/testes; produção sempre injeta o adapter."""
    repo = MagicMock()
    repo.list_portfolios.return_value = []
    repo.add_customer.return_value = _portfolio()
    use_case, _ = _use_case(None, repository=repo)

    use_case.add_customer(
        portfolio_id="p1",
        customer=SellerCustomerAssignment("000006", "01", "AGC"),
    )
    repo.add_customer.assert_called_once()


def test_create_portfolio_rejects_blocked_customer() -> None:
    eligibility = FakeEligibility(
        {("000006", "01"): CustomerEligibility(exists=True, active=False)}
    )
    use_case, repo = _use_case(eligibility)

    with pytest.raises(ValueError, match="bloqueado"):
        use_case.create_portfolio(
            CreatePortfolioRequest(
                display_name="Nova",
                customers=(SellerCustomerAssignment("000006", "01", "AGC"),),
            )
        )
    repo.create_portfolio.assert_not_called()


def test_replace_customers_rejects_blocked_customer() -> None:
    eligibility = FakeEligibility(
        {("000006", "01"): CustomerEligibility(exists=True, active=False)}
    )
    use_case, repo = _use_case(eligibility)

    with pytest.raises(ValueError, match="bloqueado"):
        use_case.replace_customers(
            portfolio_id="p1",
            customers=[SellerCustomerAssignment("000006", "01", "AGC")],
        )
    repo.replace_customers.assert_not_called()


def test_transfer_customers_rejects_blocked_customer() -> None:
    eligibility = FakeEligibility(
        {("000006", "01"): CustomerEligibility(exists=True, active=False)}
    )
    repo = MagicMock()
    repo.get_by_id.side_effect = lambda pid: _portfolio(id=pid)
    use_case, _ = _use_case(eligibility, repository=repo)

    with pytest.raises(ValueError, match="bloqueado"):
        use_case.transfer_customers(
            source_portfolio_id="p1",
            target_portfolio_id="p2",
            customers=[SellerCustomerAssignment("000006", "01", "AGC")],
            reason_note="reorganização",
        )
    repo.transfer_customers.assert_not_called()


def test_transfer_customers_bulk_marks_blocked_item_failed() -> None:
    eligibility = FakeEligibility(
        {
            ("000006", "01"): CustomerEligibility(exists=True, active=False),
            ("000001", "01"): CustomerEligibility(exists=True, active=True),
        }
    )
    repo = MagicMock()
    repo.get_by_id.side_effect = lambda pid: _portfolio(id=pid)
    repo.transfer_customers.return_value = (_portfolio(id="p1"), _portfolio(id="p2"))
    use_case, _ = _use_case(eligibility, repository=repo)

    result = use_case.transfer_customers_bulk(
        source_portfolio_id="p1",
        target_portfolio_id="p2",
        customers=[
            SellerCustomerAssignment("000006", "01", "AGC"),
            SellerCustomerAssignment("000001", "01", "Cliente 1"),
        ],
        reason_note="reorganização",
    )

    by_code = {item.customer_code: item for item in result.results}
    assert by_code["000006"].ok is False
    assert by_code["000001"].ok is True
    moved = repo.transfer_customers.call_args.kwargs["customers"]
    assert [c.customer_code for c in moved] == ["000001"]


# -- READ path: vínculo histórico preservado, status sinalizado -------------


def test_serialize_portfolio_flags_inactive_linked_customer() -> None:
    """Cliente que inativou após o vínculo: permanece na resposta (histórico
    gerenciável) mas marcado customer_active=false — não aparece como ativo."""
    eligibility = FakeEligibility(
        {
            ("000006", "01"): CustomerEligibility(exists=True, active=False),
            ("000001", "01"): CustomerEligibility(exists=True, active=True),
        }
    )
    use_case, _ = _use_case(eligibility)

    payload = use_case.serialize_portfolio(_portfolio())

    by_code = {c["customer_code"]: c for c in payload["customers"]}
    assert by_code["000006"]["customer_active"] is False
    assert by_code["000001"]["customer_active"] is True
    # Vínculo histórico continua na lista — nada é apagado nem escondido.
    assert len(payload["customers"]) == 2


def test_serialize_portfolio_without_port_keeps_legacy_payload() -> None:
    use_case, _ = _use_case(None)
    payload = use_case.serialize_portfolio(_portfolio())
    assert "customer_active" not in payload["customers"][0]


def test_inactive_link_is_not_deleted_and_still_stored() -> None:
    """CASO 10: inativar o cliente não apaga o vínculo persistido."""
    eligibility = FakeEligibility(
        {("000006", "01"): CustomerEligibility(exists=True, active=False)}
    )
    repo = MagicMock()
    linked = _portfolio()
    repo.get_by_id.return_value = linked
    use_case, _ = _use_case(eligibility, repository=repo)

    portfolio = use_case.get_portfolio("p1")

    # Entidade continua carregando o vínculo (dado histórico intacto).
    assert any(c.customer_code == "000006" for c in portfolio.customers)
    # Nenhuma operação de remoção foi disparada como efeito colateral.
    repo.remove_customer.assert_not_called()
    repo.replace_customers.assert_not_called()
