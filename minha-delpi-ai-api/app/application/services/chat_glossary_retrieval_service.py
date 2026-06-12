import re
import time
from uuid import UUID

from app.domain.ports.vocabulary_term_repository_port import VocabularyTermRepositoryPort
from app.domain.services.chat_term_extraction_service import ChatTermExtractionService
from app.infrastructure.config.settings import Settings


def _default_vocabulary_repository() -> VocabularyTermRepositoryPort:
    from app.composition.repository_composer import make_vocabulary_term_repository

    return make_vocabulary_term_repository()

# Cache em processo: o glossário muda raramente (apenas em promoção/edição admin).
_CACHE_TTL_SECONDS = 300.0
_MAX_BLOCK_TERMS = 12


class ChatGlossaryRetrievalService:
    """Recupera definições de glossário aprovadas e injeta no contexto do turno.

    "Recuperar glossário em perguntas" (playbook Fase 4): quando um termo do
    glossário aparece na mensagem, sua definição entra no contexto enviado ao LLM.
    Mantém um cache em processo das definições ativas.
    """

    _definitions: list[dict] = []
    _last_loaded_at: float = 0.0

    def __init__(self, vocabulary_repository: VocabularyTermRepositoryPort | None = None):
        self.vocabulary_repository = vocabulary_repository or _default_vocabulary_repository()

    def _ensure_loaded(self, *, force: bool = False) -> None:
        now = time.monotonic()

        if (
            not force
            and ChatGlossaryRetrievalService._last_loaded_at > 0.0
            and (now - ChatGlossaryRetrievalService._last_loaded_at) < _CACHE_TTL_SECONDS
        ):
            return

        try:
            self.refresh()
        except Exception:
            ChatGlossaryRetrievalService._last_loaded_at = now

    def refresh(self) -> int:
        terms = self.vocabulary_repository.list_active_definitions(
            scopes=("global",),
            max_terms=Settings.CHAT_LEARNING_GLOSSARY_MAX_TERMS,
        )

        loaded: list[dict] = []

        for term in terms:
            matchable = ChatTermExtractionService.normalize(term.get("term") or "")
            if matchable and term.get("meaning"):
                loaded.append(
                    {
                        "term": term["term"],
                        "matchable": matchable,
                        "meaning": term["meaning"],
                    }
                )

        ChatGlossaryRetrievalService._definitions = loaded
        ChatGlossaryRetrievalService._last_loaded_at = time.monotonic()
        return len(loaded)

    def build_context_block_for(
        self,
        *,
        message: str,
        project_id: str | None = None,
    ) -> str:
        from app.application.services.chat_platform_runtime_access import (
            learning_pipeline_settings,
        )

        learning = learning_pipeline_settings()
        if not (
            learning.get("learningEnabled") and learning.get("learningGlossaryRetrieval")
        ):
            return ""

        if not message:
            return ""

        try:
            self._ensure_loaded()
        except Exception:
            return ""

        matches = self.match_definitions(
            message,
            ChatGlossaryRetrievalService._definitions,
        )
        return self.build_block(matches)

    @staticmethod
    def match_definitions(message: str, definitions: list[dict]) -> list[dict]:
        normalized = ChatTermExtractionService.normalize(message)

        if not normalized:
            return []

        matches: list[dict] = []

        for definition in definitions:
            matchable = definition.get("matchable")
            if not matchable:
                continue

            pattern = r"\b" + re.escape(matchable) + r"\b"
            if re.search(pattern, normalized):
                matches.append(definition)

            if len(matches) >= _MAX_BLOCK_TERMS:
                break

        return matches

    @staticmethod
    def build_block(matches: list[dict]) -> str:
        if not matches:
            return ""

        lines = ["Glossário (termos confirmados relevantes a esta pergunta):"]

        for definition in matches:
            term = str(definition.get("term") or "").strip()
            meaning = str(definition.get("meaning") or "").strip()
            if term and meaning:
                lines.append(f"- {term}: {meaning}")

        if len(lines) == 1:
            return ""

        return "\n".join(lines)

    def lookup_internal(
        self,
        term: str,
        *,
        project_id: UUID | None = None,
    ) -> dict | None:
        """Busca definição interna por forma normalizada (cascata §11, passo 1)."""
        normalized = ChatTermExtractionService.normalize(term)

        if not normalized:
            return None

        try:
            return self.vocabulary_repository.find_definition_by_term(
                normalized_term=normalized,
                scopes=("global",),
                project_id=project_id,
            )
        except Exception:
            return None
