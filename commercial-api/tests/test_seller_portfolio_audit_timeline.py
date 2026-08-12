from datetime import datetime, timezone
from unittest.mock import MagicMock

from commercial_app.application.use_cases.manage_seller_portfolio import (
    ManageSellerPortfolioUseCase,
)
from commercial_app.domain.entities.audit_log_entry import AuditLogEntry
from commercial_app.domain.entities.seller_portfolio import (
    SellerPortfolio,
    SellerPortfolioMember,
)
from commercial_app.domain.services.audit_messages_content_service import (
    AuditMessagesContentService,
)
from commercial_app.domain.services.seller_portfolio_audit_formatter_service import (
    SellerPortfolioAuditFormatterService,
)


def _portfolio(**kwargs) -> SellerPortfolio:
    defaults = dict(
        id="p1",
        user_id="u1",
        display_name="Sul",
        active=True,
        customers=(),
        members=(SellerPortfolioMember(user_id="u1", role="owner"),),
    )
    defaults.update(kwargs)
    return SellerPortfolio(**defaults)


def test_audit_messages_content_has_portfolio_actions() -> None:
    bundle = AuditMessagesContentService.bundle()
    assert "seller_portfolio.add_member" in bundle["titles"]
    assert "seller_portfolio.transfer_customers" in bundle["messages"]
    assert AuditMessagesContentService.role_label("owner") == "responsável"


def test_formatter_builds_pt_br_message_for_add_member() -> None:
    formatter = SellerPortfolioAuditFormatterService()
    entry = AuditLogEntry(
        id="a1",
        actor_user_id="admin",
        action="seller_portfolio.add_member",
        entity_type="seller_portfolio",
        entity_id="p1",
        payload={"user_id": "u2", "role": "member"},
        created_at=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc),
    )
    formatted = formatter.format_entry(entry)
    assert formatted["title"] == "Membro adicionado"
    assert "u2" in formatted["message"]
    assert "membro" in formatted["message"]
    assert formatted["tone"] == "success"


def test_formatter_fallback_for_unknown_action() -> None:
    formatter = SellerPortfolioAuditFormatterService()
    entry = AuditLogEntry(
        id="a2",
        actor_user_id="admin",
        action="seller_portfolio.unknown",
        entity_type="seller_portfolio",
        entity_id="p1",
        payload={},
    )
    formatted = formatter.format_entry(entry)
    assert formatted["title"] == "Evento de auditoria"
    assert "seller_portfolio.unknown" in formatted["message"]


def test_list_portfolio_audit_formats_rows() -> None:
    repository = MagicMock()
    repository.get_by_id.return_value = _portfolio()
    audit = MagicMock()
    audit.list_for_entity.return_value = (
        [
            {
                "id": "evt-1",
                "actor_user_id": "admin",
                "action": "seller_portfolio.deactivate",
                "entity_type": "seller_portfolio",
                "entity_id": "p1",
                "payload": {"active": False},
                "created_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
            }
        ],
        1,
    )
    use_case = ManageSellerPortfolioUseCase(repository, audit_repository=audit)

    result = use_case.list_portfolio_audit("p1", page=1, page_size=10)

    assert result["total"] == 1
    assert result["page"] == 1
    assert result["page_size"] == 10
    assert result["items"][0]["action"] == "seller_portfolio.deactivate"
    assert result["items"][0]["title"] == "Carteira inativada"
    audit.list_for_entity.assert_called_once_with(
        entity_type="seller_portfolio",
        entity_id="p1",
        page=1,
        page_size=10,
        related_target_key="target_portfolio_id",
    )


def test_list_portfolio_audit_raises_when_missing() -> None:
    repository = MagicMock()
    repository.get_by_id.return_value = None
    use_case = ManageSellerPortfolioUseCase(repository, audit_repository=MagicMock())
    try:
        use_case.list_portfolio_audit("missing")
        assert False, "expected LookupError"
    except LookupError:
        pass


def test_list_portfolio_audit_empty_without_audit_repo() -> None:
    repository = MagicMock()
    repository.get_by_id.return_value = _portfolio()
    use_case = ManageSellerPortfolioUseCase(repository)
    result = use_case.list_portfolio_audit("p1")
    assert result == {"items": [], "total": 0, "page": 1, "page_size": 20}
