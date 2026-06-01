from uuid import UUID

from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_session_memory_repository_port import ChatSessionMemoryRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.chat_conversation_memory_service import ChatConversationMemoryService
from app.domain.services.chat_manual_context_pin_service import ChatManualContextPinService


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
        entity_key = ChatManualContextPinService.entity_key_for_kind(chip_kind)

        if not entity_key:
            raise ValueError("Tipo de contexto não suportado.")

        self.memory_repository.upsert_entity(
            session_id,
            entity_key,
            chip_value,
        )

        return self._build_response(session_id)

    def remove_pin(self, *, user_id: UUID, session_id: UUID, kind: str) -> dict:
        self._ensure_session_access(user_id=user_id, session_id=session_id)

        entity_key = ChatManualContextPinService.entity_key_for_kind(kind)

        if not entity_key:
            raise ValueError("Tipo de contexto não suportado.")

        self.memory_repository.deactivate_entity(session_id, entity_key)
        return self._build_response(session_id)

    def _ensure_session_access(self, *, user_id: UUID, session_id: UUID) -> None:
        session = self.session_repository.get_session_by_id(session_id)

        if not session:
            raise ChatSessionNotFoundError(str(session_id))

        if session.user_id != user_id:
            raise ChatSessionAccessDeniedError(str(session_id))

    def _build_response(self, session_id: UUID) -> dict:
        overlay = self.memory_repository.load_active_overlay(session_id)
        snapshot = {
            "lastEntities": overlay.get("lastEntities") or {},
            "behaviorInstructions": overlay.get("behaviorInstructions") or {},
        }
        chips = ChatConversationMemoryService.build_context_chips(snapshot)
        pinnable = [
            chip
            for chip in chips
            if ChatManualContextPinService.is_pinnable_kind(chip.get("kind"))
        ]

        return {"chips": pinnable}
