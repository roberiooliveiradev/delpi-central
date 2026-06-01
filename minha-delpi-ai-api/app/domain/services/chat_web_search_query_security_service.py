"""Sanitização de queries de pesquisa web — Playbook 08 §17–18."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.web_search_query_service import WebSearchQueryService


@dataclass(frozen=True)
class WebSearchQuerySecurityResult:
    query: str
    redacted: bool
    blocked: bool
    removed_fragments: tuple[str, ...]
    warnings: tuple[str, ...]


class ChatWebSearchQuerySecurityService:
    """Remove dados internos/sensíveis antes de enviar texto a buscadores externos."""

    _SENSITIVE_SUBSTRINGS = (
        "preco interno",
        "preço interno",
        "margem interna",
        "custo interno",
        "pedido interno",
        "historico de vendas",
        "histórico de vendas",
        "dados comerciais confidenciais",
        "informacao confidencial",
        "informação confidencial",
        "nosso preco",
        "nosso preço",
        "preco de venda interno",
        "preço de venda interno",
        "codigo interno estrategico",
        "código interno estratégico",
    )

    _REDACT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
        (re.compile(r"pre[cç]o\s+interno\s*(?:de\s*)?r?\$?\s*[\d.,]+", re.I), ""),
        (re.compile(r"r\$\s*[\d.,]+(?:\s*(?:interno|margem|custo))?", re.I), ""),
        (re.compile(r"\bmargem\s+(?:interna|de\s+lucro)\s*[\d.,%]*", re.I), ""),
        (re.compile(r"\bpedido\s+interno\s*(?:n[ºo°.]?\s*)?[\w-]+", re.I), ""),
        (re.compile(r"\bcomprou\s+nosso\s+produto\s+\d+", re.I), "produto"),
        (re.compile(r"\bpelo\s+pre[cç]o\s+interno\b", re.I), ""),
    )

    _ENTITY_PUBLIC_SUFFIX = "informacoes publicas"

    @classmethod
    def sanitize(cls, message: str, *, extracted_query: str | None = None) -> WebSearchQuerySecurityResult:
        raw = str(extracted_query if extracted_query is not None else message or "").strip()
        normalized = ChatMessageNormalizationService.normalize_for_matching(raw) or raw
        removed: list[str] = []
        warnings: list[str] = []
        redacted = False

        for substring in cls._SENSITIVE_SUBSTRINGS:
            if substring in normalized:
                redacted = True
                removed.append(substring)

        value = raw

        for pattern, replacement in cls._REDACT_PATTERNS:
            new_value, count = pattern.subn(replacement, value)

            if count:
                redacted = True
                removed.append(pattern.pattern)

            value = new_value

        value = WebSearchQueryService.sanitize_query(value)
        value = re.sub(r"\s+", " ", value).strip(" ,.;")

        if redacted:
            warnings.append(
                "Dados internos ou comerciais sensíveis foram omitidos da consulta enviada à web."
            )
            public = cls._build_public_fallback(raw)

            if public:
                value = public

        if not value or len(value) < 3:
            fallback = cls._build_public_fallback(raw)

            if fallback:
                value = fallback
                warnings.append(
                    "A consulta foi reescrita para buscar apenas informações públicas."
                )
            else:
                return WebSearchQuerySecurityResult(
                    query="",
                    redacted=redacted,
                    blocked=True,
                    removed_fragments=tuple(removed),
                    warnings=tuple(
                        warnings
                        + [
                            "Não é seguro enviar esta pergunta completa para um buscador externo."
                        ]
                    ),
                )

        return WebSearchQuerySecurityResult(
            query=value,
            redacted=redacted,
            blocked=False,
            removed_fragments=tuple(removed),
            warnings=tuple(warnings),
        )

    @classmethod
    def _build_public_fallback(cls, raw: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(raw) or raw
        client_match = re.search(
            r"cliente\s+([a-z0-9][\w-]{1,40})",
            normalized,
            flags=re.IGNORECASE,
        )

        if client_match:
            name = client_match.group(1).strip()
            return f"cliente {name} {cls._ENTITY_PUBLIC_SUFFIX}"

        company_match = re.search(
            r"(?:empresa|companhia)\s+([a-z0-9][\w-]{1,40})",
            normalized,
            flags=re.IGNORECASE,
        )

        if company_match:
            name = company_match.group(1).strip()
            return f"{name} empresa {cls._ENTITY_PUBLIC_SUFFIX}"

        return ""
