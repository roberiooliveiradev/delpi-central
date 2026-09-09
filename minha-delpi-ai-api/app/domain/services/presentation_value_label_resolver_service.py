"""Tradução de valores categóricos — identidade técnica permanece; UI usa display label."""

from __future__ import annotations

from typing import Any, Mapping


class PresentationValueLabelResolverService:
    """Resolve display labels for enum/code values without changing canonical values.

    v1: use provided vocabulary map only — never invent meaning via LLM.
    """

    @classmethod
    def resolve(
        cls,
        value: Any,
        *,
        vocabulary: Mapping[str, str] | None = None,
    ) -> str:
        token = str(value if value is not None else "").strip()
        if not token:
            return ""
        if isinstance(vocabulary, Mapping):
            mapped = vocabulary.get(token)
            if isinstance(mapped, str) and mapped.strip():
                return mapped.strip()
        return token
