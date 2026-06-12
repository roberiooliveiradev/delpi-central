import time

from app.domain.ports.vocabulary_term_repository_port import VocabularyTermRepositoryPort
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.infrastructure.config.settings import Settings


def _default_vocabulary_repository() -> VocabularyTermRepositoryPort:
    from app.composition.repository_composer import make_vocabulary_term_repository

    return make_vocabulary_term_repository()

# Cache em processo: regras aprendidas mudam raramente (apenas em promoção admin).
_CACHE_TTL_SECONDS = 300.0


class ChatLearnedNormalizationService:
    """Carrega termos de vocabulário aprovados e os aplica na normalização base.

    Mantém o `ChatMessageNormalizationService` puro: empurra as regras aprendidas
    para o registro do serviço base, que passa a aplicá-las após as regras estáticas.
    """

    _last_loaded_at: float = 0.0

    def __init__(self, vocabulary_repository: VocabularyTermRepositoryPort | None = None):
        self.vocabulary_repository = vocabulary_repository or _default_vocabulary_repository()

    def ensure_loaded(self, *, force: bool = False) -> None:
        """Carrega regras se a flag estiver ligada e o cache expirou. Best-effort."""
        from app.application.services.chat_platform_runtime_access import (
            learning_pipeline_settings,
        )

        learning = learning_pipeline_settings()

        if not (learning.get("learningEnabled") and learning.get("learningApplyVocabulary")):
            return

        now = time.monotonic()

        if not force and (now - ChatLearnedNormalizationService._last_loaded_at) < _CACHE_TTL_SECONDS:
            return

        try:
            self.refresh()
        except Exception:
            # Nunca quebrar um turno por causa de aprendizado opcional.
            ChatLearnedNormalizationService._last_loaded_at = now

    def refresh(self) -> int:
        """Recarrega as regras aprendidas a partir do banco. Retorna a contagem aplicada."""
        terms = self.vocabulary_repository.list_active_normalization_rules(
            scopes=("global",),
            max_rules=Settings.CHAT_LEARNING_VOCABULARY_MAX_RULES,
        )

        rules: list[tuple[str, str]] = []

        for term in terms:
            matchable = ChatMessageNormalizationService.strip_accents(term["term"])
            correction = ChatMessageNormalizationService.strip_accents(term["normalizedTerm"])

            if matchable and correction and matchable != correction:
                rules.append((matchable, correction))

        ChatMessageNormalizationService.set_learned_rules(rules)
        ChatLearnedNormalizationService._last_loaded_at = time.monotonic()
        return len(rules)
