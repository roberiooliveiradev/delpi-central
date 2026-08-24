"""Cache request-scoped de candidatos OpenAPI por turno."""

from __future__ import annotations

import hashlib
from contextvars import ContextVar
from typing import Any

_cache: ContextVar[dict[tuple[str, frozenset[str]], list[dict]] | None] = ContextVar(
    "external_action_candidate_turn_cache",
    default=None,
)


class ExternalActionCandidateTurnCache:
    @classmethod
    def _store(cls) -> dict[tuple[str, frozenset[str]], list[dict]]:
        store = _cache.get()

        if store is None:
            store = {}
            _cache.set(store)

        return store

    @classmethod
    def cache_key(
        cls,
        message: str,
        *,
        allowed_action_ids: list[str] | None,
    ) -> tuple[str, frozenset[str]]:
        normalized = str(message or "").strip().lower()[:2000]
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
        allowed = frozenset(
            str(item).strip()
            for item in (allowed_action_ids or [])
            if str(item).strip()
        )

        return digest, allowed

    @classmethod
    def get(
        cls,
        message: str,
        *,
        allowed_action_ids: list[str] | None,
    ) -> list[dict] | None:
        key = cls.cache_key(message, allowed_action_ids=allowed_action_ids)
        cached = cls._store().get(key)

        if cached is None:
            return None

        return [dict(item) for item in cached]

    @classmethod
    def set(
        cls,
        message: str,
        *,
        allowed_action_ids: list[str] | None,
        candidates: list[dict],
    ) -> None:
        key = cls.cache_key(message, allowed_action_ids=allowed_action_ids)
        cls._store()[key] = [dict(item) for item in candidates]

    @classmethod
    def clear(cls) -> None:
        _cache.set({})
