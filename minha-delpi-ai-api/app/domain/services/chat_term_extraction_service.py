import re
import unicodedata

from app.domain.services.chat_term_extraction_vocabulary_service import (
    ChatTermExtractionVocabularyService,
)


class ChatTermExtractionService:
    """Extrai e classifica termos desconhecidos de uma mensagem (playbook §9, §13).

    Puro/sem DB. Detecta perguntas de definição ("o que é X?") e classifica o
    termo para decidir a ação (glossário interno, docs, web pública, etc.).
    """

    @classmethod
    def _definition_question_patterns(cls):
        return ChatTermExtractionVocabularyService.definition_patterns()

    _STOPWORDS = frozenset(ChatTermExtractionVocabularyService.terms("stopwords"))

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        stripped = unicodedata.normalize("NFKD", text)
        stripped = "".join(ch for ch in stripped if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", stripped).strip().lower()

    @classmethod
    def detect_definition_question(cls, message: str) -> str | None:
        text = (message or "").strip()

        if len(text) < 4 or len(text) > 160:
            return None

        for pattern in cls._definition_question_patterns():
            match = pattern.search(text)
            if match:
                term = (match.group("term") or "").strip(" ?.!,;")
                normalized = cls.normalize(term)
                if term and normalized not in cls._STOPWORDS and len(normalized) >= 2:
                    return term

        return None

    @classmethod
    def classify_unknown_term(cls, term: str) -> str:
        """Classifica o termo (playbook §13) para decidir a ação adequada."""
        raw = (term or "").strip()

        if not raw:
            return "unknown"

        compact = raw.replace(" ", "")

        if compact.isdigit():
            return "internal_code"

        has_alpha = any(ch.isalpha() for ch in compact)
        has_digit = any(ch.isdigit() for ch in compact)

        if has_alpha and has_digit:
            return "product_code"

        # Sigla: 2–6 letras, tudo maiúsculo, sem espaço.
        if raw.isupper() and 2 <= len(compact) <= 6 and " " not in raw:
            return "acronym"

        if " " in raw:
            return "phrase"

        return "technical"

    @classmethod
    def is_web_researchable(cls, term: str) -> bool:
        """Termos genéricos/técnicos podem ir à web; códigos/operacionais não."""
        category = cls.classify_unknown_term(term)
        return category in {"acronym", "technical", "product_code"}
