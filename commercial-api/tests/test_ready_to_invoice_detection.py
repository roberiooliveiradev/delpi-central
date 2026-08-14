"""Unit tests for ready_to_invoice snapshot delta + recipients."""

from __future__ import annotations

from commercial_app.application.use_cases.detect_ready_to_invoice_entries import (
    DetectReadyToInvoiceEntriesUseCase,
)
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)
from commercial_app.domain.ports.integration_outbox_repository_port import (
    IntegrationCheckpoint,
)
from commercial_app.domain.services.ready_to_invoice_recipient_resolver_service import (
    ReadyToInvoiceRecipientResolverService,
)
from commercial_app.domain.services.ready_to_invoice_snapshot_delta_service import (
    ReadyToInvoiceSnapshotDeltaService,
    open_order_line_key,
)


def test_open_order_line_key() -> None:
    assert open_order_line_key({"filial": "01", "pedido": "100", "linha": "01"}) == "01|100|01"


def test_delta_detects_new_ready_keys_only() -> None:
    service = ReadyToInvoiceSnapshotDeltaService()
    items = [
        {
            "filial": "01",
            "pedido": "A",
            "linha": "01",
            "saldo": 2,
            "no_estoque": 2,
            "valor_aberto": 10,
        },
        {
            "filial": "01",
            "pedido": "B",
            "linha": "01",
            "saldo": 2,
            "no_estoque": 0,
            "valor_aberto": 20,
            "data_entrega": "2099-01-01",
        },
        {
            "filial": "01",
            "pedido": "C",
            "linha": "01",
            "saldo": 1,
            "estoque_alocado": 1,
            "valor_aberto": 5,
        },
    ]
    delta = service.compute_delta(
        items=items,
        previous_keys=["01|A|01"],
    )
    assert delta.current_keys == frozenset({"01|A|01", "01|C|01"})
    assert delta.entered_keys == frozenset({"01|C|01"})
    assert len(delta.entered_items) == 1
    assert delta.entered_items[0]["pedido"] == "C"


def test_recipient_resolver_uses_portfolio_membership() -> None:
    resolver = ReadyToInvoiceRecipientResolverService(
        billing_user_ids=["bill-1"],
        billing_permission_codes=["commercial.accounts.manage"],
    )
    portfolios = [
        SellerPortfolio(
            id="p1",
            user_id="owner-1",
            display_name="Carteira",
            active=True,
            customers=(
                SellerCustomerAssignment(customer_code="100", customer_store="01"),
            ),
            members=(
                SellerPortfolioMember(user_id="owner-1", role="owner"),
                SellerPortfolioMember(user_id="seller-2", role="member"),
            ),
        )
    ]
    index = resolver.build_customer_sellers_index(portfolios)
    recipients = resolver.resolve_for_item(
        {"codigo_cadastro": "100", "loja_cadastro": "01"},
        customer_sellers=index,
    )
    assert recipients.seller_user_ids == frozenset({"owner-1", "seller-2"})
    assert recipients.billing_user_ids == frozenset({"bill-1"})
    assert recipients.billing_permission_codes == ("commercial.accounts.manage",)
    assert "bill-1" in recipients.all_user_ids


class _FakeCheckpointRepo:
    def __init__(self) -> None:
        self.saved: dict | None = None
        self.existing: IntegrationCheckpoint | None = None

    def get_by_source_key(self, source_key: str):
        return self.existing

    def upsert_metadata(self, *, source_key: str, metadata: dict, cursor_value=None, last_success_at=None):
        self.saved = {
            "source_key": source_key,
            "metadata": metadata,
            "cursor_value": cursor_value,
        }
        return IntegrationCheckpoint(
            id="1",
            source_key=source_key,
            cursor_value=cursor_value,
            last_success_at=last_success_at,
            metadata=metadata,
            updated_at=None,
        )


class _FakeGateway:
    def list_open_orders(self, *, params=None):
        return {
            "data": {
                "items": [
                    {
                        "filial": "01",
                        "pedido": "9",
                        "linha": "01",
                        "saldo": 1,
                        "no_estoque": 1,
                        "codigo_cadastro": "100",
                        "loja_cadastro": "01",
                        "nome_cliente": "ACME",
                        "valor_aberto": 50,
                    }
                ]
            }
        }


class _FakePortfolios:
    def list_portfolios(self, *, active_only: bool = False):
        return [
            SellerPortfolio(
                id="p1",
                user_id="seller-1",
                display_name="X",
                active=True,
                customers=(
                    SellerCustomerAssignment(customer_code="100", customer_store="01"),
                ),
                members=(SellerPortfolioMember(user_id="seller-1", role="owner"),),
            )
        ]


def test_detect_use_case_persists_snapshot_and_resolves_sellers() -> None:
    checkpoints = _FakeCheckpointRepo()
    uc = DetectReadyToInvoiceEntriesUseCase(
        gateway=_FakeGateway(),
        portfolios=_FakePortfolios(),
        checkpoints=checkpoints,
        recipient_resolver=ReadyToInvoiceRecipientResolverService(
            billing_user_ids=[],
            billing_permission_codes=[],
        ),
    )
    result = uc.execute()
    assert result.previous_key_count == 0
    assert result.current_key_count == 1
    assert len(result.entered) == 1
    assert result.entered[0].line_key == "01|9|01"
    assert result.entered[0].recipients.seller_user_ids == frozenset({"seller-1"})
    assert checkpoints.saved is not None
    assert checkpoints.saved["metadata"]["keys"] == ["01|9|01"]
    assert "view=board" in result.board_deep_link_path
    assert "ready_to_invoice" in result.board_deep_link_path


def test_v014_migration_defines_outbox_and_checkpoints() -> None:
    from pathlib import Path

    sql = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "V014__integration_outbox_and_checkpoints.sql"
    ).read_text(encoding="utf-8")
    assert "integration_outbox" in sql
    assert "integration_checkpoints" in sql
    assert "WHERE published_at IS NULL" in sql
    assert "DROP TABLE" not in sql
