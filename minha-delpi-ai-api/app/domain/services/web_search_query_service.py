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

    _ENTITY_FILLER_WORDS = frozenset(
        {
            "empresa",
            "companhia",
            "company",
            "corporation",
            "negocio",
            "negócio",
            "business",
            "marca",
            "brand",
        }
    )

    _LEADING_FILLER_PATTERNS = (
        r"^(?:a\s+)?(?:empresa|companhia)\s+",
        r"^empresa\s+",
        r"^companhia\s+",
        r"^the\s+company\s+",
        r"^a\s+company\s+",
        r"^sobre\s+a\s+empresa\s+",
        r"^about\s+the\s+company\s+",
    )

    @classmethod
    def normalize_query(cls, query: str) -> str:
        return re.sub(r"\s+", " ", str(query or "").strip())

    @classmethod
    def sanitize_query(cls, query: str) -> str:
        value = cls._normalize_for_retry(query)

        for pattern in cls._LEADING_FILLER_PATTERNS:
            value = re.sub(pattern, " ", value, flags=re.IGNORECASE).strip()

        value = re.sub(r"\s+", " ", value).strip()
        return cls.normalize_query(value)

    @classmethod
    def extract_entity_tokens(cls, query: str) -> list[str]:
        sanitized = cls.sanitize_query(query)
        normalized = cls._normalize_for_retry(sanitized or query)

        return [
            token
            for token in normalized.split()
            if token not in cls._PT_STOPWORDS
            and token not in cls._ENTITY_FILLER_WORDS
            and len(token) > 1
        ]

    @classmethod
    def extract_primary_entity(cls, query: str) -> str:
        tokens = cls.extract_entity_tokens(query)

        if not tokens:
            return ""

        token = tokens[-1]
        return token[:1].upper() + token[1:]

    @classmethod
    def build_search_candidates(cls, query: str) -> list[str]:
        normalized = cls.normalize_query(query)
        sanitized = cls.sanitize_query(normalized) or normalized

        candidates: list[str] = []

        for candidate in (sanitized, normalized):
            cleaned = cls.normalize_query(candidate)

            if cleaned and cleaned not in candidates:
                candidates.append(cleaned)

        if cls._english_retry_enabled():
            retry = cls.build_english_retry_query(sanitized or normalized)

            if retry and retry not in candidates:
                candidates.append(retry)

        tokens = cls.extract_entity_tokens(sanitized or normalized)

        if len(tokens) == 1:
            entity = cls.extract_primary_entity(sanitized or normalized)
            boosts = [
                entity,
                f"{entity} International",
                f"{entity} company",
            ]

            if entity.isupper() and len(entity) <= 8:
                title_case = entity.title()
                boosts.extend(
                    [
                        title_case,
                        f"{title_case} International",
                        f"{title_case} company",
                    ]
                )

            for boost in boosts:
                cleaned = cls.normalize_query(boost)

                if cleaned and cleaned not in candidates:
                    candidates.append(cleaned)

        return candidates

    @classmethod
    def _english_retry_enabled(cls) -> bool:
        try:
            from app.domain.services.chat_domain_config_service import (
                ChatDomainConfigService,
            )

            return ChatDomainConfigService.chat_web_search_retry_en_enabled()
        except RuntimeError:
            # Testes unitários sem wiring de AppConfigPort — mantém retry ligado.
            return True

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

    _ENTITY_BOOST_MARKERS = (
        "industries",
        "indústrias",
        "empresa",
        "company",
        "corporation",
        "brazil",
        "brasileir",
        "manufacturer",
        "multinacional",
    )

    @classmethod
    def rank_results_for_query(cls, payload: dict, query: str) -> dict:
        """Prioriza resultados alinhados à entidade (ex.: WEG → WEG Industries, não homônimos)."""
        if not isinstance(payload, dict):
            return payload

        results = payload.get("results")

        if not isinstance(results, list) or len(results) <= 1:
            return payload

        tokens = cls.extract_entity_tokens(query)

        if not tokens:
            return payload

        entity = tokens[-1].casefold()

        def score(item: dict) -> float:
            text = " ".join(
                [
                    str(item.get("title") or ""),
                    str(item.get("snippet") or ""),
                    str(item.get("url") or ""),
                ]
            ).casefold()
            value = 0.0

            if entity in text:
                value += 12.0

            if re.search(rf"\b{re.escape(entity)}\b", text):
                value += 4.0

            for marker in cls._ENTITY_BOOST_MARKERS:
                if marker in text:
                    value += 2.0

            if "weg industries" in text or "weg.net" in text:
                value += 8.0

            if str(item.get("source") or "") == "instant_answer":
                value -= 2.0

            return value

        ranked = sorted(
            (item for item in results if isinstance(item, dict)),
            key=score,
            reverse=True,
        )

        return {**payload, "results": ranked}

    @classmethod
    def build_english_retry_query(cls, query: str) -> str | None:
        normalized = cls._normalize_for_retry(cls.sanitize_query(query) or query)

        if not normalized:
            return None

        translated = normalized

        for pt_phrase, en_phrase in cls._PT_TO_EN_PHRASES:
            if pt_phrase in {"empresa", "companhia"}:
                continue

            translated = translated.replace(pt_phrase, en_phrase)

        translated = cls._strip_leading_filler(translated)
        translated = re.sub(r"\s+", " ", translated).strip()

        if not translated or translated == normalized:
            if cls._looks_portuguese(normalized):
                tokens = cls.extract_entity_tokens(normalized)

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

    @classmethod
    def _strip_leading_filler(cls, query: str) -> str:
        value = cls._normalize_for_retry(query)

        for pattern in cls._LEADING_FILLER_PATTERNS:
            value = re.sub(pattern, " ", value, flags=re.IGNORECASE).strip()

        tokens = [
            token
            for token in value.split()
            if token not in cls._PT_STOPWORDS
            and token not in cls._ENTITY_FILLER_WORDS
        ]

        return re.sub(r"\s+", " ", " ".join(tokens)).strip()
