from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _identity_content() -> dict:
    return ContentService.load_json("assistant/identity")


# Sinais de documentação sobre o chat/plataforma (RAG de identidade).
_IDENTITY_DOC_SIGNALS: tuple[str, ...] = (
    "minha delpi",
    "minha-delpi",
    "delpi chat",
    "chat corporativo",
    "assistente",
    "arquiteto do codigo",
    "arquiteto do código",
    "inteligencia artificial",
    "inteligência artificial",
    "ia generativa",
    "modelo de linguagem",
    "orquestr",
    "rag",
    "plataforma delpi",
    "backend da",
    "sso",
    "rbac",
    "chat-intelligence",
)

# Normas de produto / engenharia — não respondem meta-perguntas sobre o assistente.
_TECHNICAL_NORM_SIGNALS: tuple[str, ...] = (
    "normas_tecnicas",
    "normas tecnicas",
    "norma tecnica",
    "isolador",
    "termistor",
    "grupo 1009",
    "grupo 1025",
    "term. luva",
    "designacao tecnica",
    "designação técnica",
    "estrutura da descricao",
    "estrutura da descrição",
    "rohs",
    "term. emenda",
)

_IDENTITY_DOC_TITLE_HINTS: tuple[str, ...] = (
    "arquiteto",
    "minha delpi",
    "chat-intelligence",
    "chat intelligence",
    "minha delpi.txt",
)


class ChatAssistantIdentityService:
    """Classificação e respostas canônicas sobre o assistente (evita LLM pesado em CPU)."""

    @classmethod
    def is_assistant_identity_question(cls, message: str) -> bool:
        return cls.classify(message) is not None

    @classmethod
    def classify(cls, message: str) -> str | None:
        content = _identity_content()
        max_length = int(content.get("maxMessageLength") or 220)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if len(normalized) > max_length:
            return None

        category = cls._match_category(message, content)

        if category:
            return category

        exclusions = tuple(
            str(item) for item in (content.get("userIdentityExclusions") or ())
        )
        if ChatMessageNormalizationService.contains_any(message, exclusions):
            return None

        return None

    @classmethod
    def _match_category(cls, message: str, content: dict) -> str | None:
        patterns = content.get("patterns") or {}
        priority = tuple(
            str(item)
            for item in (
                content.get("categoryPriority")
                or ("who", "limits", "origin", "usage", "role", "what")
            )
        )

        for category in priority:
            terms = tuple(str(item) for item in (patterns.get(category) or ()))
            if terms and ChatMessageNormalizationService.contains_any(message, terms):
                return category

        return None

    @classmethod
    def build_rag_query(cls, message: str) -> str:
        """Consulta RAG focada no assistente/plataforma (evita match em normas de produto)."""
        base = str(message or "").strip()
        return (
            f"{base} Minha DELPI Chat assistente plataforma "
            "inteligência artificial arquitetura origem desenvolvimento"
        )

    @classmethod
    def identity_chunk_filter(cls) -> Callable[[dict], bool]:
        return cls.is_identity_relevant_chunk

    @classmethod
    def is_identity_relevant_chunk(cls, chunk: dict) -> bool:
        """Descarta chunks de normas técnicas e docs sem relação com o chat."""
        metadata = chunk.get("metadata") or {}
        title = str(chunk.get("title") or "").lower()
        filename = str(metadata.get("originalFilename") or chunk.get("title") or "").lower()
        content = str(chunk.get("content") or "").lower()
        combined = f"{title} {filename} {content[:800]}"

        if "normas_tecnicas" in filename or "normas tecnicas" in title:
            if not any(hint in title or hint in filename for hint in _IDENTITY_DOC_TITLE_HINTS):
                return False

        if any(hint in title or hint in filename for hint in _IDENTITY_DOC_TITLE_HINTS):
            return True

        has_identity_signal = any(signal in combined for signal in _IDENTITY_DOC_SIGNALS)
        has_technical_norm_signal = any(
            signal in combined for signal in _TECHNICAL_NORM_SIGNALS
        )

        if has_technical_norm_signal and not has_identity_signal:
            return False

        if has_identity_signal:
            return True

        return False

    @classmethod
    def build_direct_answer(cls, *, message: str, workspace_context: dict) -> str | None:
        category = cls.classify(message)
        if not category:
            return None

        content = _identity_content()
        responses = content.get("responses") or {}
        agent = workspace_context.get("agent") or {}
        agent_name = str(agent.get("name") or workspace_context.get("agentKey") or "").strip()
        has_agent = bool(agent_name)

        scope = "agent" if has_agent else "platform"
        template = str((responses.get(scope) or {}).get(category) or "").strip()
        if not template:
            template = str((responses.get("platform") or {}).get(category) or "").strip()
        if not template:
            return None

        placeholders = content.get("placeholders") or {}
        agent_description = str(agent.get("description") or "").strip()
        if not agent_description:
            agent_description = str(
                placeholders.get("agentDescriptionFallback")
                or "assistente especializado configurado para este tema."
            )

        platform_name = str(content.get("platformName") or "Minha DELPI")

        return template.format(
            platform_name=platform_name,
            agent_name=agent_name,
            agent_description=agent_description,
        )
