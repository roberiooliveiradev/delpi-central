"""Adapta markdown de GPT_instructions (api-delpi-py) para rotas atuais da api-delpi."""

from __future__ import annotations

import re
from datetime import UTC, datetime

# Substituições de paths obsoletos → api-delpi atual (maio/2026).
_PATH_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("/products/search/description", "/products/search"),
    ("GET /product/", "GET /products/"),
    ("`/product/", "`/products/"),
    ("/product/{code}", "/products/{code}"),
    ("/product/*", "/products/*"),
    ("https://api.transformamaisdelpi.com.br/data/sql", "POST /data/sql (gateway: /apps/api-delpi/data/sql)"),
)

_HEADER_TEMPLATE = """\
> **Origem:** `api-delpi-py/GPT_instructions/{source_name}` · **Adaptado em:** {adapted_at} · **Alvo:** agente Minha DELPI / RAG operacional
>
> Paths normalizados para a api-delpi atual (`/products/search`, `/products/{{code}}/…`). Consulte também `api-delpi-rotas-agente.md`.

"""


class GptInstructionsAdaptationService:
    @classmethod
    def adapt(cls, content: str, *, source_name: str) -> str:
        text = str(content or "").strip()

        if not text:
            return text

        for old, new in _PATH_REPLACEMENTS:
            text = text.replace(old, new)

        text = cls._normalize_search_examples(text)

        header = _HEADER_TEMPLATE.format(
            source_name=source_name,
            adapted_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        )

        if text.startswith(">"):
            return text

        return f"{header}\n{text}"

    @classmethod
    def _normalize_search_examples(cls, text: str) -> str:
        return re.sub(
            r"(GET /products/search)\?description=",
            r"\1?description=",
            text,
            flags=re.IGNORECASE,
        )

    @classmethod
    def output_filename(cls, source_name: str) -> str:
        stem = source_name.rsplit(".", 1)[0] if "." in source_name else source_name
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", stem).strip("-").lower()
        return f"gpt-{slug}.md"
