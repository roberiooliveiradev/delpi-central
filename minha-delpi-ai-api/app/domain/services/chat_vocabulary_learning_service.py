import re

from app.domain.services.chat_learning_content_service import ChatLearningContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatVocabularyLearningService:
    """Detecta termos novos, definições explícitas e candidatos de normalização."""

    @classmethod
    def _clean(cls, value: str) -> str:
        quote_chars = ChatLearningContentService.quote_chars()

        return re.sub(r"\s+", " ", str(value or "")).strip().strip(quote_chars).strip()

    @classmethod
    def detect_explicit_definition(cls, message: str) -> dict | None:
        """Detecta 'quando eu falar X é Y' / 'X significa Y' (alta confiança)."""
        text = cls._clean(message)

        if not text:
            return None

        max_term_length = ChatLearningContentService.limit_int("maxTermLength", 80)
        max_meaning_length = ChatLearningContentService.limit_int("maxMeaningLength", 240)
        max_term_words = ChatLearningContentService.limit_int("maxTermWords", 6)
        stored_term_length = ChatLearningContentService.limit_int("storedTermLength", 160)
        evidence_length = ChatLearningContentService.limit_int("evidenceSnippetLength", 400)
        confidence = ChatLearningContentService.limit_float("explicitDefinitionConfidence", 0.9)

        for pattern in ChatLearningContentService.explicit_definition_patterns():
            match = pattern.search(text)

            if not match:
                continue

            term = cls._clean(match.group("term"))
            meaning = cls._clean(match.group("meaning"))

            if not term or not meaning:
                continue

            if len(term) > max_term_length or len(meaning) > max_meaning_length:
                continue

            if len(term.split()) > max_term_words:
                continue

            return {
                "candidateType": "term_definition",
                "term": term[:stored_term_length],
                "normalizedTerm": ChatMessageNormalizationService.strip_accents(term)[
                    :stored_term_length
                ],
                "proposedMeaning": meaning,
                "confidence": confidence,
                "source": "user_explicit_definition",
                "scope": "project",
                "evidence": {"examples": [text[:evidence_length]]},
            }

        return None

    @classmethod
    def build_normalization_candidate(
        cls,
        raw_message: str,
        *,
        source: str = "recurring_typo",
        base_confidence: float | None = None,
    ) -> dict | None:
        """Candidato de normalização a partir de uma mensagem que confundiu o chat."""
        text = cls._clean(raw_message)
        max_message_length = ChatLearningContentService.limit_int(
            "normalizationMessageMaxLength",
            240,
        )
        stored_length = ChatLearningContentService.limit_int("storedNormalizationLength", 160)
        default_confidence = ChatLearningContentService.limit_float(
            "normalizationBaseConfidence",
            0.4,
        )
        max_confidence = ChatLearningContentService.limit_float(
            "normalizationMaxConfidence",
            0.95,
        )
        resolved_confidence = (
            default_confidence if base_confidence is None else float(base_confidence)
        )

        if not text or len(text) > max_message_length:
            return None

        matchable = ChatMessageNormalizationService.strip_accents(text)

        if not matchable:
            return None

        return {
            "candidateType": "normalization_rule",
            "term": matchable[:stored_length],
            "normalizedTerm": matchable[:stored_length],
            "inputText": text,
            "proposedRule": None,
            "confidence": max(0.0, min(resolved_confidence, max_confidence)),
            "source": source,
            "scope": "global",
            "evidence": {"examples": [text]},
        }

    @classmethod
    def classify_term(cls, term: str) -> str:
        """Classificação leve do termo (playbook §13)."""
        token = str(term or "").strip()
        abbreviation_max = ChatLearningContentService.limit_int("abbreviationMaxLength", 6)
        consonant_max = ChatLearningContentService.limit_int(
            "consonantAbbreviationMaxLength",
            5,
        )
        vowel_pattern = ChatLearningContentService.compile_pattern("termHasVowel")

        if not token:
            return ChatLearningContentService.classification_kind("defaultKind", "term")

        if " " in token:
            return ChatLearningContentService.classification_kind("phraseKind", "phrase")

        if token.isupper() and len(token) <= abbreviation_max:
            return ChatLearningContentService.classification_kind(
                "abbreviationKind",
                "abbreviation",
            )

        if not vowel_pattern.search(token) and len(token) <= consonant_max:
            return ChatLearningContentService.classification_kind(
                "abbreviationKind",
                "abbreviation",
            )

        return ChatLearningContentService.classification_kind("typoKind", "typo")
