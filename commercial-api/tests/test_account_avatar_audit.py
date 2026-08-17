from __future__ import annotations

from unittest.mock import MagicMock

from commercial_app.application.services.customer_avatar_storage import CustomerAvatarStorage
from commercial_app.application.use_cases.manage_account_contacts import account_entity_id
from commercial_app.application.use_cases.manage_customer_avatar import (
    ManageCustomerAvatarUseCase,
)
from commercial_app.domain.entities.audit_log_entry import AuditLogEntry
from commercial_app.domain.entities.customer_avatar import CustomerAvatarRecord
from commercial_app.domain.services.account_audit_formatter_service import (
    AccountAuditFormatterService,
)
from commercial_app.domain.services.audit_messages_content_service import (
    AuditMessagesContentService,
)


class InMemoryCustomerAvatarRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], CustomerAvatarRecord] = {}

    def get(
        self,
        *,
        customer_code: str,
        customer_store: str,
    ) -> CustomerAvatarRecord | None:
        return self._items.get((customer_code, customer_store))

    def list_for_customers(
        self,
        *,
        customers: list[tuple[str, str]],
    ) -> list[CustomerAvatarRecord]:
        return [
            self._items[key]
            for key in customers
            if key in self._items
        ]

    def upsert(
        self,
        *,
        customer_code: str,
        customer_store: str,
        file_name: str,
        storage_key: str,
        content_type: str,
        byte_size: int | None,
        uploaded_by_user_id: str | None,
    ) -> CustomerAvatarRecord:
        record = CustomerAvatarRecord(
            customer_code=customer_code,
            customer_store=customer_store,
            file_name=file_name,
            content_type=content_type,
            storage_key=storage_key,
            byte_size=byte_size,
        )
        self._items[(customer_code, customer_store)] = record
        return record

    def delete(
        self,
        *,
        customer_code: str,
        customer_store: str,
    ) -> bool:
        return self._items.pop((customer_code, customer_store), None) is not None


def _png_bytes() -> bytes:
    # Minimal 1x1 PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_audit_messages_content_has_account_avatar_actions() -> None:
    AuditMessagesContentService.clear_cache()
    bundle = AuditMessagesContentService.bundle()
    assert "account.avatar.uploaded" in bundle["titles"]
    assert "account.avatar.deleted" in bundle["messages"]
    assert "account.avatar.uploaded" in bundle["tones"]


def test_formatter_builds_pt_br_for_avatar_uploaded() -> None:
    AuditMessagesContentService.clear_cache()
    formatted = AccountAuditFormatterService().format_entry(
        AuditLogEntry(
            id="a1",
            actor_user_id="user-1",
            action="account.avatar.uploaded",
            entity_type="account",
            entity_id="000001/01",
            payload={"file_name": "avatar.png"},
        )
    )
    assert formatted["title"] == "Logo atualizado"
    assert "avatar.png" in formatted["message"]
    assert formatted["tone"] == "success"


def test_formatter_builds_pt_br_for_avatar_deleted() -> None:
    formatted = AccountAuditFormatterService().format_entry(
        AuditLogEntry(
            id="a2",
            actor_user_id="user-1",
            action="account.avatar.deleted",
            entity_type="account",
            entity_id="000001/01",
            payload={"file_name": "avatar.png"},
        )
    )
    assert formatted["title"] == "Logo removido"
    assert "removido" in formatted["message"]
    assert formatted["tone"] == "warning"


def test_upsert_and_delete_append_account_avatar_audit(tmp_path) -> None:
    repository = InMemoryCustomerAvatarRepository()
    audit = MagicMock()
    use_case = ManageCustomerAvatarUseCase(
        repository=repository,
        storage=CustomerAvatarStorage(base_dir=str(tmp_path)),
        audit_repository=audit,
    )

    record = use_case.upsert(
        customer_code="000001",
        customer_store="01",
        original_name="logo.png",
        content=_png_bytes(),
        mime_type="image/png",
        uploaded_by_user_id="user-1",
    )
    use_case.delete(
        customer_code="000001",
        customer_store="01",
        actor_user_id="user-1",
    )

    assert audit.append.call_count == 2
    actions = [call.kwargs["action"] for call in audit.append.call_args_list]
    assert actions == ["account.avatar.uploaded", "account.avatar.deleted"]
    for call in audit.append.call_args_list:
        assert call.kwargs["entity_type"] == "account"
        assert call.kwargs["entity_id"] == account_entity_id("000001", "01")
        assert call.kwargs["actor_user_id"] == "user-1"
    assert audit.append.call_args_list[0].kwargs["payload"]["file_name"] == record.file_name


def test_upsert_without_actor_skips_audit(tmp_path) -> None:
    audit = MagicMock()
    use_case = ManageCustomerAvatarUseCase(
        repository=InMemoryCustomerAvatarRepository(),
        storage=CustomerAvatarStorage(base_dir=str(tmp_path)),
        audit_repository=audit,
    )
    use_case.upsert(
        customer_code="000001",
        customer_store="01",
        original_name="logo.png",
        content=_png_bytes(),
        mime_type="image/png",
        uploaded_by_user_id=None,
    )
    audit.append.assert_not_called()


def test_upsert_delete_without_audit_repo_still_works(tmp_path) -> None:
    use_case = ManageCustomerAvatarUseCase(
        repository=InMemoryCustomerAvatarRepository(),
        storage=CustomerAvatarStorage(base_dir=str(tmp_path)),
    )
    use_case.upsert(
        customer_code="000001",
        customer_store="01",
        original_name="logo.png",
        content=_png_bytes(),
        mime_type="image/png",
        uploaded_by_user_id="user-1",
    )
    use_case.delete(
        customer_code="000001",
        customer_store="01",
        actor_user_id="user-1",
    )
