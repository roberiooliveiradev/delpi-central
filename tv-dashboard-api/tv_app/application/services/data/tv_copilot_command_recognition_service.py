"""Reconhecimento de comando do editor TV — vocabulário e tolerância no catálogo.

Ponto único de «essa frase fala com o editor?» e «esse marcador casou?». O
casamento é tolerante a acento e a erro de digitação («crie um sldie»), porque
exigir string exata jogava o pedido para o LLM, que respondia markdown em vez
de mexer na programação.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)

_TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9]+")


class TvCopilotCommandRecognitionService:
    @classmethod
    def normalize(cls, message: str | None) -> str:
        return " ".join(str(message or "").strip().lower().split())

    @classmethod
    def fold(cls, text: str | None) -> str:
        decomposed = unicodedata.normalize("NFKD", str(text or "").lower())
        return "".join(ch for ch in decomposed if not unicodedata.combining(ch))

    @classmethod
    def tokens(cls, text: str | None) -> tuple[str, ...]:
        return tuple(tok for tok in _TOKEN_SPLIT_RE.split(cls.fold(text)) if tok)

    @classmethod
    def _threshold(cls) -> float:
        return TvCopilotContentService.recognition_float("fuzzyThreshold", 0.8)

    @classmethod
    def _min_fuzzy_length(cls) -> int:
        return TvCopilotContentService.recognition_int("minFuzzyTokenLength", 4)

    @classmethod
    def _token_matches(cls, needle: str, candidate: str) -> bool:
        if needle == candidate:
            return True
        # Token curto («um», «de») só casa exato: fuzzy aqui gera falso positivo.
        if len(needle) < cls._min_fuzzy_length() or len(candidate) < cls._min_fuzzy_length():
            return False
        if abs(len(needle) - len(candidate)) > 2:
            return False
        return SequenceMatcher(None, needle, candidate).ratio() >= cls._threshold()

    @classmethod
    def marker_hit(cls, needle: str | None, haystack: str | None) -> bool:
        marker = cls.normalize(needle)
        text = cls.normalize(haystack)
        if not marker or not text:
            return False

        if marker in text:
            return True

        folded_marker = cls.fold(marker)
        folded_text = cls.fold(text)
        if folded_marker and folded_marker in folded_text:
            return True

        marker_tokens = cls.tokens(marker)
        text_tokens = cls.tokens(text)
        if not marker_tokens or len(text_tokens) < len(marker_tokens):
            return False

        width = len(marker_tokens)
        for start in range(len(text_tokens) - width + 1):
            window = text_tokens[start : start + width]
            if all(
                cls._token_matches(expected, actual)
                for expected, actual in zip(marker_tokens, window)
            ):
                return True
        return False

    @classmethod
    def is_editor_command(cls, message: str | None) -> bool:
        """Verdadeiro quando a frase pede ação sobre um objeto do editor TV."""
        text = cls.normalize(message)
        if not text:
            return False

        nouns = TvCopilotContentService.editor_nouns()
        if not any(cls.marker_hit(noun, text) for noun in nouns):
            return False

        for term_set in TvCopilotContentService.recognition_action_term_sets():
            for term in TvCopilotContentService.action_terms_for_set(term_set):
                if cls.marker_hit(term, text):
                    return True

        # Verbos de editor que o catálogo ainda não cobre: reconhecer como
        # comando permite responder «não sei fazer isso» em vez de improvisar.
        for term in TvCopilotContentService.recognition_extra_action_terms():
            if cls.marker_hit(term, text):
                return True
        return False
