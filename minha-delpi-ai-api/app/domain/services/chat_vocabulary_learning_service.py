import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

# Playbook §10, §17: detecção de vocabulário/typos/definições explícitas.

# "quando eu falar X, é/quero dizer/significa Y"
_EXPLICIT_WHEN_RE = re.compile(
    r"(?i)\bquando\s+eu\s+(?:falar|disser|dizer|digo|mencionar|menciono|usar|uso)\s+"
    r"(?P<term>.+?)\s*[,:]?\s*"
    r"(?:e|eh|é|estou\s+falando\s+d[eoa]s?|quero\s+dizer|significa|me\s+refiro\s+a|"
    r"\bsao\b|\bsão\b)\s+"
    r"(?P<meaning>.+?)[\.\!]?$"
)

# "X significa Y" / "X quer dizer Y" / "X = Y"
_EXPLICIT_MEANS_RE = re.compile(
    r"(?i)^\s*[\"'“]?(?P<term>[^=,\.\"']{1,60}?)[\"'”]?\s+"
    r"(?:significa|quer\s+dizer|é\s+o\s+mesmo\s+que|e\s+o\s+mesmo\s+que)\s+"
    r"(?P<meaning>.+?)[\.\!]?$"
)

_EXPLICIT_EQUALS_RE = re.compile(
    r"(?i)^\s*[\"'“]?(?P<term>[^=\"']{1,60}?)[\"'”]?\s*=\s*(?P<meaning>.+?)[\.\!]?$"
)

_QUOTE_CHARS = "\"'“”‘’`"


class ChatVocabularyLearningService:
    """Detecta termos novos, definições explícitas e candidatos de normalização."""

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip().strip(_QUOTE_CHARS).strip()

    @classmethod
    def detect_explicit_definition(cls, message: str) -> dict | None:
        """Detecta 'quando eu falar X é Y' / 'X significa Y' (alta confiança)."""
        text = cls._clean(message)

        if not text:
            return None

        for pattern in (_EXPLICIT_WHEN_RE, _EXPLICIT_MEANS_RE, _EXPLICIT_EQUALS_RE):
            match = pattern.search(text)

            if not match:
                continue

            term = cls._clean(match.group("term"))
            meaning = cls._clean(match.group("meaning"))

            if not term or not meaning:
                continue

            if len(term) > 80 or len(meaning) > 240:
                continue

            # Termo não pode ser uma frase inteira; deve ser curto e específico.
            if len(term.split()) > 6:
                continue

            return {
                "candidateType": "term_definition",
                "term": term[:160],
                "normalizedTerm": ChatMessageNormalizationService.strip_accents(term)[:160],
                "proposedMeaning": meaning,
                "confidence": 0.9,
                "source": "user_explicit_definition",
                "scope": "project",
                "evidence": {"examples": [text[:400]]},
            }

        return None

    @classmethod
    def build_normalization_candidate(
        cls,
        raw_message: str,
        *,
        source: str = "recurring_typo",
        base_confidence: float = 0.4,
    ) -> dict | None:
        """Candidato de normalização a partir de uma mensagem que confundiu o chat."""
        text = cls._clean(raw_message)

        if not text or len(text) > 240:
            return None

        # Forma crua (sem acento, minúscula) que confundiu o chat. A correção
        # fica em aberto: o admin define o `normalizedTerm` ao revisar/promover.
        matchable = ChatMessageNormalizationService.strip_accents(text)

        if not matchable:
            return None

        return {
            "candidateType": "normalization_rule",
            "term": matchable[:160],
            "normalizedTerm": matchable[:160],
            "inputText": text,
            "proposedRule": None,
            "confidence": max(0.0, min(base_confidence, 0.95)),
            "source": source,
            "scope": "global",
            "evidence": {"examples": [text]},
        }

    @staticmethod
    def classify_term(term: str) -> str:
        """Classificação leve do termo (playbook §13)."""
        token = str(term or "").strip()

        if not token:
            return "term"

        if " " in token:
            return "phrase"

        if token.isupper() and len(token) <= 6:
            return "abbreviation"

        if not re.search(r"[aeiouáéíóúâêô]", token, re.IGNORECASE) and len(token) <= 5:
            return "abbreviation"

        return "typo"
