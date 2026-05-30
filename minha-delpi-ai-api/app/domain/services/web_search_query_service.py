"""Normalização de consultas e heurísticas para retry de busca web."""

from __future__ import annotations

import re
import unicodedata

USELESS_RESULT_SOURCES = frozenset({"fallback_link", "no_results"})


class WebSearchQueryService:
    _PT_TO_EN_PHRASES: tuple[tuple[str, str], ...] = (
        ("linguagem de programacao", "programming language"),
        ("linguagem de programação", "programming language"),
        ("o que e", "what is"),
        ("o que é", "what is"),
        ("como funciona", "how does it work"),
        ("historia de", "history of"),
        ("história de", "history of"),
        ("definicao de", "definition of"),
        ("definição de", "definition of"),
        ("noticias sobre", "news about"),
        ("notícias sobre", "news about"),
        ("ultimas noticias", "latest news"),
        ("últimas notícias", "latest news"),
        ("preco de", "price of"),
        ("preço de", "price of"),
        ("empresa", "company"),
        ("tecnologia", "technology"),
    )

    _PT_STOPWORDS = frozenset(
        {
            "a",
            "as",
            "de",
            "da",
            "do",
            "das",
            "dos",
            "e",
            "em",
            "na",
            "no",
            "nas",
            "nos",
            "o",
            "os",
            "para",
            "por",
            "sobre",
            "um",
            "uma",
            "uns",
            "umas",
        }
    )

    @classmethod
    def normalize_query(cls, query: str) -> str:
        return re.sub(r"\s+", " ", str(query or "").strip())

    @classmethod
    def is_useful_payload(cls, payload: dict | None) -> bool:
        if not isinstance(payload, dict):
            return False

        results = payload.get("results")

        if not isinstance(results, list) or not results:
            return False

        useful = [
            item
            for item in results
            if isinstance(item, dict)
            and str(item.get("source") or "") not in USELESS_RESULT_SOURCES
            and str(item.get("snippet") or "").strip()
        ]

        return bool(useful)

    @classmethod
    def build_english_retry_query(cls, query: str) -> str | None:
        normalized = cls._normalize_for_retry(query)

        if not normalized:
            return None

        translated = normalized

        for pt_phrase, en_phrase in cls._PT_TO_EN_PHRASES:
            translated = translated.replace(pt_phrase, en_phrase)

        translated = re.sub(r"\s+", " ", translated).strip()

        if not translated or translated == normalized:
            if cls._looks_portuguese(normalized):
                tokens = [
                    token
                    for token in normalized.split()
                    if token not in cls._PT_STOPWORDS and len(token) > 1
                ]
                if tokens:
                    translated = " ".join(tokens)
                else:
                    return None

        retry = cls.normalize_query(translated)

        if not retry or retry.casefold() == cls.normalize_query(query).casefold():
            return None

        return retry

    @classmethod
    def build_no_results_payload(cls, query: str, *, provider: str) -> dict:
        cleaned_query = cls.normalize_query(query)

        return {
            "query": cleaned_query,
            "results": [
                {
                    "title": cleaned_query or "Consulta web",
                    "snippet": (
                        "A busca na internet não retornou resultados úteis para esta consulta. "
                        "Você pode reformular a pergunta ou complementar com conhecimento geral "
                        "de forma explícita (sem citar como fonte da web)."
                    ),
                    "url": None,
                    "source": "no_results",
                }
            ],
            "provider": provider,
            "searchStatus": "no_results",
        }

    @classmethod
    def _normalize_for_retry(cls, query: str) -> str:
        value = cls.normalize_query(query).casefold()
        value = unicodedata.normalize("NFKD", value)
        value = "".join(char for char in value if not unicodedata.combining(char))
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _looks_portuguese(cls, query: str) -> bool:
        if re.search(r"[áàâãéêíóôõúç]", query):
            return True

        tokens = set(query.split())
        return bool(tokens.intersection(cls._PT_STOPWORDS))
