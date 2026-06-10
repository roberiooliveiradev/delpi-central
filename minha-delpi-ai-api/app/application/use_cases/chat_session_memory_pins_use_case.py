from uuid import UUID

from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_session_memory_repository_port import ChatSessionMemoryRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.chat_conversation_memory_service import ChatConversationMemoryService
from app.domain.services.chat_manual_context_pin_service import ChatManualContextPinService
from app.domain.services.chat_memory_ux_service import ChatMemoryUxService
from app.domain.services.chat_user_context_item_service import ChatUserContextItemService


class ChatSessionMemoryPinsUseCase:
    def __init__(
        self,
        session_repository: ChatSessionRepositoryPort,
        memory_repository: ChatSessionMemoryRepositoryPort,
    ):
        self.session_repository = session_repository
        self.memory_repository = memory_repository

    def get_context(self, *, user_id: UUID, session_id: UUID) -> dict:
        self._ensure_session_access(user_id=user_id, session_id=session_id)
        return self._build_response(session_id)

    def add_pin(self, *, user_id: UUID, session_id: UUID, kind: str, value: str) -> dict:
        self._ensure_session_access(user_id=user_id, session_id=session_id)

        normalized = ChatManualContextPinService.normalize_pin(kind=kind, value=value)

        if not normalized:
            raise ValueError("Tipo ou valor de contexto inválido.")

        chip_kind, chip_value = normalized
        content = (
            chip_value
            if chip_kind == "product"
            else f"filial {chip_value}"
            if chip_kind == "branch"
            else f"armazém {chip_value}"
        )
        item = ChatUserContextItemService.ingest(content=content)
        overlay = self.memory_repository.load_active_overlay(session_id)
        existing_items = list(overlay.get("userContextItems") or [])

        for duplicate_id in ChatUserContextItemService.find_duplicate_item_ids(
            existing_items,
            [item],
        ):
            self.memory_repository.remove_context_item(session_id, duplicate_id)

        self.memory_repository.add_context_item(session_id, item)
        existing_items = [i for i in existing_items if i.get("id") != item.get("id")]
        existing_items.append(item)
        overlay["userContextItems"] = existing_items[-12:]
        overlay = ChatUserContextItemService.apply_extracted_entities_to_overlay(
            overlay,
            item,
        )

        return self._build_response(session_id)

    def add_context_item(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        content: str,
        filename: str | None = None,
        role: str | None = None,
        kind: str | None = None,
        message_id: str | None = None,
        question: str | None = None,
        answer: str | None = None,
        question_message_id: str | None = None,
        answer_message_id: str | None = None,
    ) -> dict:
        self._ensure_session_access(user_id=user_id, session_id=session_id)

        question_text = str(question or "").strip()
        answer_text = str(answer or "").strip()

        if question_text and answer_text:
            items = ChatUserContextItemService.ingest_turn(
                question=question_text,
                answer=answer_text,
                question_message_id=question_message_id,
                answer_message_id=answer_message_id,
            )
        else:
            items = [
                ChatUserContextItemService.ingest(
                    content=content,
                    filename=filename,
                    role=role,
                    kind=kind,
                    message_id=message_id,
                )
            ]

        overlay = self.memory_repository.load_active_overlay(session_id)
        existing_items = overlay.get("userContextItems") or []

        for duplicate_id in ChatUserContextItemService.find_duplicate_item_ids(
            existing_items,
            items,
        ):
            self.memory_repository.remove_context_item(session_id, duplicate_id)
            existing_items = [
                item
                for item in existing_items
                if isinstance(item, dict)
                and str(item.get("id") or "").strip() != duplicate_id
            ]

        for item in items:
            self.memory_repository.add_context_item(session_id, item)
            existing_items.append(item)
            overlay = ChatUserContextItemService.apply_extracted_entities_to_overlay(
                overlay,
                item,
            )

        overlay["userContextItems"] = existing_items[-12:]
        overlay = ChatUserContextItemService.apply_extracted_entities_to_overlay(
            overlay,
            items[-1] if items else {},
        )

        return self._build_response(session_id)

    def remove_context_item(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        item_id: str,
    ) -> dict:
        self._ensure_session_access(user_id=user_id, session_id=session_id)

        if not self.memory_repository.remove_context_item(session_id, item_id):
            raise ValueError("Item de contexto não encontrado.")

        return self._build_response(session_id)

    _RESPONSE_FORMAT_VALUES = frozenset({"table", "text", "tree", "chart", "topics", "canvas", "dashboard", "auto"})

    def set_response_format(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        response_format: str,
    ) -> dict:
        self._ensure_session_access(user_id=user_id, session_id=session_id)

        token = str(response_format or "").strip().lower()

        if token not in self._RESPONSE_FORMAT_VALUES:
            raise ValueError("Formato de resposta inválido.")

        overlay = self.memory_repository.load_active_overlay(session_id)
        behavior = dict(overlay.get("behaviorInstructions") or {})

        if token == "auto":
            behavior.pop("responseFormat", None)
        else:
            behavior["responseFormat"] = token
            behavior["scope"] = "session"

        overlay["behaviorInstructions"] = behavior
        self.memory_repository.sync_from_snapshot(session_id, overlay)

        return self._build_response(session_id)

    def remove_pin(self, *, user_id: UUID, session_id: UUID, kind: str) -> dict:
        self._ensure_session_access(user_id=user_id, session_id=session_id)

        if not ChatManualContextPinService.entity_key_for_kind(kind):
            raise ValueError("Tipo de contexto não suportado.")

        overlay = self.memory_repository.load_active_overlay(session_id)
        existing_items = list(overlay.get("userContextItems") or [])
        kept, removed_ids = ChatUserContextItemService.remove_context_items_for_operational_kind(
            existing_items,
            kind=kind,
        )

        for item_id in removed_ids:
            self.memory_repository.remove_context_item(session_id, item_id)

        entity_key = ChatManualContextPinService.entity_key_for_kind(kind)

        if entity_key:
            self.memory_repository.deactivate_entity(session_id, entity_key)

        overlay["userContextItems"] = kept[-12:]
        overlay = ChatUserContextItemService.sync_operational_focus(overlay)

        return self._build_response(session_id)

    def _ensure_session_access(self, *, user_id: UUID, session_id: UUID) -> None:
        session = self.session_repository.get_session_by_id(session_id)

        if not session:
            raise ChatSessionNotFoundError(str(session_id))

        if session.user_id != user_id:
            raise ChatSessionAccessDeniedError(str(session_id))

    def _build_response(self, session_id: UUID) -> dict:
        overlay = self.memory_repository.load_active_overlay(session_id)
        snapshot = ChatUserContextItemService.sync_operational_focus(
            {
                "operationalFocus": overlay.get("operationalFocus") or {},
                "behaviorInstructions": overlay.get("behaviorInstructions") or {},
                "userContextItems": overlay.get("userContextItems") or [],
            }
        )
        chips = ChatConversationMemoryService.build_context_chips(snapshot)

        return {
            "chips": chips,
            "summary": ChatMemoryUxService.build_context_bar_summary(snapshot, chips=chips),
            "usage": ChatMemoryUxService.build_usage_view(snapshot),
        }
