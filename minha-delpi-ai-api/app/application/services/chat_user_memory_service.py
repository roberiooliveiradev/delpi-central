from uuid import UUID

from app.domain.services.chat_learning_safety_guard import ChatLearningSafetyGuard
from app.domain.services.chat_user_memory_durability_service import (
    ChatUserMemoryDurabilityService,
)
from app.infrastructure.config.settings import Settings

_TYPE_LABELS = {
    "preference": "Preferência",
    "profile": "Perfil",
    "correction": "Correção",
}


class ChatUserMemoryService:
    """Memória persistente do usuário/projeto (cross-sessão).

    Captura conservadora de preferências/perfil duráveis e injeção do bloco no
    contexto do turno. Tudo gated por feature flag e best-effort: nunca quebra o
    turno (playbook §31 — captura sem efeito colateral).
    """

    def __init__(self, repository=None):
        if repository is None:
            from app.infrastructure.persistence.postgres_memory_item_repository import (
                PostgresMemoryItemRepository,
            )

            repository = PostgresMemoryItemRepository()

        self.repository = repository

    def capture_from_turn(
        self,
        *,
        message: str,
        user_id: str | None = None,
        project_id: str | None = None,
        session_id: str | None = None,
    ) -> dict | None:
        if not Settings.CHAT_USER_MEMORY_ENABLED or not Settings.CHAT_USER_MEMORY_CAPTURE:
            return None

        if not user_id:
            return None

        detected = ChatUserMemoryDurabilityService.detect(message or "")

        if detected is None:
            return None

        # Guarda a mensagem inteira: evita capturar memória quando há dado
        # sensível por perto (ex.: e-mail/telefone que o regex truncaria).
        if not ChatLearningSafetyGuard.is_safe_to_learn(message or ""):
            return None

        if not ChatLearningSafetyGuard.is_safe_to_learn(detected["content"]):
            return None

        user_uuid = self._as_uuid(user_id)
        project_uuid = self._as_uuid(project_id)
        session_uuid = self._as_uuid(session_id)

        from app.extensions.db import db

        try:
            with db.session.begin_nested():
                existing = self.repository.find_active_duplicate(
                    user_id=user_uuid,
                    scope=detected["scope"],
                    type=detected["type"],
                    content_norm=detected["contentNorm"],
                    project_id=project_uuid,
                )

                if existing is not None:
                    updated = self.repository.bump_evidence(
                        existing["id"],
                        confidence=detected["confidence"],
                    )
                    self._sync_rag_index(updated)
                    return updated

                created = self.repository.create(
                    type=detected["type"],
                    content=detected["content"],
                    content_norm=detected["contentNorm"],
                    user_id=user_uuid,
                    project_id=project_uuid,
                    session_id=session_uuid,
                    scope=detected["scope"],
                    confidence=detected["confidence"],
                    source=detected["source"],
                    created_by=user_uuid,
                )
                self._sync_rag_index(created)
                from app.domain.services.chat_learning_event_service import (
                    ChatLearningEventService,
                )

                ChatLearningEventService.emit(
                    "chat.memory.created",
                    memoryItemId=created.get("id"),
                    userId=user_id,
                    type=detected["type"],
                )
                return created
        except Exception:
            return None

    @staticmethod
    def _sync_rag_index(item: dict | None) -> None:
        if not item:
            return

        try:
            from app.application.services.chat_memory_knowledge_index_service import (
                ChatMemoryKnowledgeIndexService,
            )

            ChatMemoryKnowledgeIndexService().sync_item(item)
        except Exception:
            return

    def format_prompt_block_for(
        self,
        *,
        user_id: str | None = None,
        project_id: str | None = None,
    ) -> str:
        if not Settings.CHAT_USER_MEMORY_ENABLED or not Settings.CHAT_USER_MEMORY_APPLY:
            return ""

        if not user_id and not project_id:
            return ""

        try:
            items = self.repository.list_active_for_context(
                user_id=self._as_uuid(user_id),
                project_id=self._as_uuid(project_id),
                limit=Settings.CHAT_USER_MEMORY_MAX_ITEMS,
            )
        except Exception:
            return ""

        return self.build_prompt_block(items)

    @staticmethod
    def build_prompt_block(items: list[dict]) -> str:
        if not items:
            return ""

        lines = ["Memória persistente do usuário (confirmada anteriormente):"]

        for item in items:
            label = _TYPE_LABELS.get(str(item.get("type")), "Memória")
            content = str(item.get("content") or "").strip()
            if content:
                lines.append(f"- [{label}] {content}")

        if len(lines) == 1:
            return ""

        return "\n".join(lines)

    @staticmethod
    def _as_uuid(value: str | None) -> UUID | None:
        if not value:
            return None
        try:
            return UUID(str(value))
        except (ValueError, TypeError):
            return None
