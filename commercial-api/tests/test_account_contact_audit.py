from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from commercial_app.application.use_cases.manage_account_contacts import (
    CreateAccountContactInput,
    ManageAccountContactsUseCase,
    account_entity_id,
)
from commercial_app.domain.entities.audit_log_entry import AuditLogEntry
from commercial_app.domain.services.account_audit_formatter_service import (
    AccountAuditFormatterService,
)
from commercial_app.domain.services.audit_messages_content_service import (
    AuditMessagesContentService,
)
from tests.test_account_contacts_use_case import (
    InMemoryAccountContactRepository,
    allow_scope,
)


def test_audit_messages_content_has_account_contact_actions() -> None:
    AuditMessagesContentService.clear_cache()
    bundle = AuditMessagesContentService.bundle()
    assert "account.contact.created" in bundle["titles"]
    assert "account.contact.updated" in bundle["messages"]
    assert "account.contact.deleted" in bundle["tones"]


def test_formatter_builds_pt_br_for_contact_created() -> None:
    AuditMessagesContentService.clear_cache()
    formatted = AccountAuditFormatterService().format_entry(
        AuditLogEntry(
            id="a1",
            actor_user_id="user-1",
            action="account.contact.created",
            entity_type="account",
            entity_id="000001/01",
            payload={"full_name": "Ana Souza", "channel": "whatsapp"},
        )
    )
    assert formatted["title"] == "Contato criado"
    assert "Ana Souza" in formatted["message"]
    assert "whatsapp" in formatted["message"]
    assert formatted["tone"] == "success"


def test_formatter_builds_pt_br_for_contact_updated() -> None:
    formatted = AccountAuditFormatterService().format_entry(
        AuditLogEntry(
            id="a2",
            actor_user_id="user-1",
            action="account.contact.updated",
            entity_type="account",
            entity_id="000001/01",
            payload={
                "full_name": "Ana Souza",
                "changed_fields": ["role_title", "is_primary"],
                "fields_label": "cargo, principal",
            },
        )
    )
    assert formatted["title"] == "Contato atualizado"
    assert "cargo" in formatted["message"]
    assert formatted["tone"] == "info"


def test_create_update_delete_append_account_audit() -> None:
    repository = InMemoryAccountContactRepository()
    audit = MagicMock()
    use_case = ManageAccountContactsUseCase(
        repository=repository,
        audit_repository=audit,
    )

    contact = use_case.create(
        customer_code="000001",
        customer_store="01",
        actor_user_id="user-1",
        data=CreateAccountContactInput(
            full_name="Ana Souza",
            channel="email",
            email="ana@example.com",
        ),
        scope_check=allow_scope,
    )
    use_case.update(
        customer_code="000001",
        customer_store="01",
        contact_id=contact.id,
        changes={"role_title": "Compras"},
        scope_check=allow_scope,
        actor_user_id="user-1",
    )
    use_case.soft_delete(
        customer_code="000001",
        customer_store="01",
        contact_id=contact.id,
        scope_check=allow_scope,
        actor_user_id="user-1",
    )

    assert audit.append.call_count == 3
    actions = [call.kwargs["action"] for call in audit.append.call_args_list]
    assert actions == [
        "account.contact.created",
        "account.contact.updated",
        "account.contact.deleted",
    ]


def test_create_contact_notifies_account_changed(monkeypatch) -> None:
    repository = InMemoryAccountContactRepository()
    audit = MagicMock()
    notified: list[dict] = []

    def fake_notify(**kwargs):
        notified.append(kwargs)

    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.notify_account_changed",
        fake_notify,
    )
    use_case = ManageAccountContactsUseCase(
        repository=repository,
        audit_repository=audit,
    )
    use_case.create(
        customer_code="000001",
        customer_store="01",
        actor_user_id="user-1",
        data=CreateAccountContactInput(
            full_name="Ana Souza",
            channel="email",
            email="ana@example.com",
        ),
        scope_check=allow_scope,
    )
    assert len(notified) == 1
    assert notified[0]["reason"] == "account.contact.created"
    assert notified[0]["customer_code"] == "000001"
    assert notified[0]["customer_store"] == "01"
    assert notified[0]["actor_user_id"] == "user-1"
    assert audit.append.call_count == 1
    assert audit.append.call_args.kwargs["entity_type"] == "account"
    assert audit.append.call_args.kwargs["entity_id"] == account_entity_id("000001", "01")


def test_update_without_changes_skips_audit() -> None:
    repository = InMemoryAccountContactRepository()
    audit = MagicMock()
    use_case = ManageAccountContactsUseCase(
        repository=repository,
        audit_repository=audit,
    )
    contact = use_case.create(
        customer_code="000001",
        customer_store="01",
        actor_user_id="user-1",
        data=CreateAccountContactInput(full_name="Ana", channel="email"),
        scope_check=allow_scope,
    )
    audit.reset_mock()

    use_case.update(
        customer_code="000001",
        customer_store="01",
        contact_id=contact.id,
        changes={},
        scope_check=allow_scope,
        actor_user_id="user-1",
    )
    audit.append.assert_not_called()


def test_list_account_audit_formats_rows() -> None:
    repository = InMemoryAccountContactRepository()
    audit = MagicMock()
    audit.list_for_entity.return_value = (
        [
            {
                "id": "evt-1",
                "actor_user_id": "user-1",
                "action": "account.contact.deleted",
                "entity_type": "account",
                "entity_id": "000001/01",
                "payload": {"full_name": "Ana Souza", "channel": "email"},
                "created_at": datetime(2026, 8, 13, tzinfo=timezone.utc),
            }
        ],
        1,
    )
    use_case = ManageAccountContactsUseCase(
        repository=repository,
        audit_repository=audit,
    )

    result = use_case.list_account_audit(
        customer_code="000001",
        customer_store="01",
        scope_check=allow_scope,
        page=1,
        page_size=10,
    )

    assert result["total"] == 1
    assert result["page"] == 1
    assert result["page_size"] == 10
    assert result["items"][0]["action"] == "account.contact.deleted"
    assert result["items"][0]["title"] == "Contato removido"
    assert "Ana Souza" in result["items"][0]["message"]
    audit.list_for_entity.assert_called_once_with(
        entity_type="account",
        entity_id="000001/01",
        page=1,
        page_size=10,
    )


def test_list_account_audit_empty_without_audit_repo() -> None:
    use_case = ManageAccountContactsUseCase(
        repository=InMemoryAccountContactRepository(),
    )
    result = use_case.list_account_audit(
        customer_code="000001",
        customer_store="01",
        scope_check=allow_scope,
    )
    assert result == {"items": [], "total": 0, "page": 1, "page_size": 20}


def test_list_account_audit_respects_scope() -> None:
    use_case = ManageAccountContactsUseCase(
        repository=InMemoryAccountContactRepository(),
        audit_repository=MagicMock(),
    )

    def deny_scope(_customer_code: str, _customer_store: str) -> None:
        raise LookupError("Cliente fora do escopo.")

    with pytest.raises(LookupError, match="fora do escopo"):
        use_case.list_account_audit(
            customer_code="000001",
            customer_store="01",
            scope_check=deny_scope,
        )


def test_cud_without_audit_repo_still_works() -> None:
    use_case = ManageAccountContactsUseCase(
        repository=InMemoryAccountContactRepository(),
    )
    contact = use_case.create(
        customer_code="000001",
        customer_store="01",
        actor_user_id="user-1",
        data=CreateAccountContactInput(full_name="Ana", channel="other"),
        scope_check=allow_scope,
    )
    assert isinstance(contact.id, UUID)
