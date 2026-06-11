import re
import unicodedata
from typing import Any


class ChatMessageNormalizationService:
    """Normaliza mensagens do usuário para matching de intenção (acentos, typos).

    Regras estáticas vêm de `assistant/typing_correction_rules.json` (P14-0),
    carregadas no composition root via `configure_static_rules`.

    Regras *aprendidas* via `set_learned_rules` (playbook §10/§15) aplicam-se
    após as estáticas.
    """

    _STATIC_PATTERNS: list[tuple[re.Pattern[str], str]] = []
    _LEARNED_PATTERNS: list[tuple[re.Pattern[str], str]] = []

    @staticmethod
    def strip_accents(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(value or "").strip().lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))

    @classmethod
    def configure_static_rules(cls, rules: list[dict[str, Any]] | None) -> None:
        """Carrega regras estáticas do catálogo JSON (ordem preservada)."""
        compiled: list[tuple[re.Pattern[str], str]] = []

        for raw in rules or []:
            if not isinstance(raw, dict):
                continue

            pattern = str(raw.get("pattern") or "").strip()
            replacement = str(raw.get("replacement") or "").strip()

            if not pattern or not replacement:
                continue

            try:
                compiled.append((re.compile(pattern, re.IGNORECASE), replacement))
            except re.error:
                continue

        cls._STATIC_PATTERNS = compiled

    @classmethod
    def static_rule_count(cls) -> int:
        return len(cls._STATIC_PATTERNS)

    @classmethod
    def set_learned_rules(cls, rules: list[tuple[str, str]] | None) -> None:
        """Registra regras aprendidas (term -> normalized) aplicadas após as estáticas."""
        compiled: list[tuple[re.Pattern[str], str]] = []

        for raw_term, replacement in rules or []:
            term = str(raw_term or "").strip()
            target = str(replacement or "").strip()

            if not term or not target or term == target:
                continue

            try:
                compiled.append(
                    (re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE), target)
                )
            except re.error:
                continue

        cls._LEARNED_PATTERNS = compiled

    @classmethod
    def clear_learned_rules(cls) -> None:
        cls._LEARNED_PATTERNS = []

    @classmethod
    def iter_typo_patterns(cls) -> list[tuple[re.Pattern[str], str]]:
        """Padrões estáticos + aprendidos — fonte única para matching e sugestões (P14)."""
        return list(cls._STATIC_PATTERNS) + list(cls._LEARNED_PATTERNS)

    @classmethod
    def normalize_for_matching(cls, message: str) -> str:
        text = cls.strip_accents(message)
        text = re.sub(r"\s+", " ", text).strip()

        for pattern, replacement in cls._STATIC_PATTERNS:
            text = pattern.sub(replacement, text)

        for pattern, replacement in cls._LEARNED_PATTERNS:
            text = pattern.sub(replacement, text)

        return text

    @classmethod
    def contains_any(cls, message: str, terms: tuple[str, ...] | list[str]) -> bool:
        normalized = cls.normalize_for_matching(message)
        return any(cls.strip_accents(term) in normalized for term in terms)

    @classmethod
    def expand_query_terms(cls, message: str) -> list[str]:
        """Retorna a mensagem normalizada e variantes úteis para busca semântica."""
        base = cls.normalize_for_matching(message)
        variants = {base}
        if base:
            variants.add(base.replace("?", "").strip())
        return [item for item in variants if item]
