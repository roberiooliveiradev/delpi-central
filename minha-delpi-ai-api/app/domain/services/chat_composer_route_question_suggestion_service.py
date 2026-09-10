"""Sugestões de perguntas no composer — contextual (draft + entities + allowlist + cache)."""

from __future__ import annotations

import hashlib
import threading
import time
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import ChatMessageNormalizationService
from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntentService

_BUNDLE = "composer_route_questions"
_PRODUCT_PLACEHOLDER = "{productCode}"

_cache_lock = threading.Lock()
_suggest_cache: dict[str, tuple[float, tuple[dict[str, str], ...]]] = {}


class ChatComposerRouteQuestionSuggestionService:
    @classmethod
    def clear_cache(cls) -> None:
        with _cache_lock:
            _suggest_cache.clear()

    @classmethod
    def suggest(
        cls,
        text: str,
        *,
        allowed_action_ids: list[str] | set[str] | tuple[str, ...] | None = None,
        use_cache: bool = True,
    ) -> list[dict[str, str]]:
        config = ChatAssistantContentService.get_node(_BUNDLE) or {}

        if not isinstance(config, dict) or not config.get("enabled", True):
            return []

        raw = str(text or "").strip()
        normalized = ChatMessageNormalizationService.normalize_for_matching(raw)
        min_len = int(config.get("minDraftLength") or 3)

        if len(normalized) < min_len:
            return []

        allowed = cls._normalize_allowed(allowed_action_ids)
        cache_key = cls._cache_key(normalized, allowed)
        cache_cfg = cls._cache_config(config)

        if use_cache and cache_cfg["enabled"]:
            hit = cls._cache_get(cache_key, cache_cfg["ttlSeconds"])
            if hit is not None:
                return [dict(item) for item in hit]

        product_code = cls._extract_product_code(raw)
        candidates: list[dict[str, str]] = []

        for group in config.get("groups") or []:
            if not isinstance(group, dict):
                continue

            group_id = str(group.get("id") or "").strip()
            if not cls._group_allowed(group_id, group, allowed, config):
                continue

            if not cls._group_matches(normalized, group):
                continue

            label = str(group.get("label") or group.get("id") or "").strip()

            for item in group.get("questions") or []:
                if not isinstance(item, dict):
                    continue

                query = cls._resolve_query(str(item.get("query") or "").strip(), product_code)

                if not query:
                    continue

                candidates.append(
                    {
                        "label": str(item.get("label") or label or query).strip(),
                        "query": query,
                        "category": label,
                        "source": "composer_route_questions",
                        "groupId": group_id,
                    }
                )

        if config.get("includePathRulesFromCapabilities", True):
            for item in cls._suggestions_from_capabilities(normalized, product_code):
                if not cls._capability_candidate_allowed(item, allowed):
                    continue
                candidates.append(item)

        resolved = cls._finalize_candidates(raw, candidates, config)

        if use_cache and cache_cfg["enabled"]:
            cls._cache_store(
                cache_key,
                resolved,
                ttl_seconds=int(cache_cfg["ttlSeconds"]),
                max_entries=int(cache_cfg["maxEntries"]),
            )

        return resolved

    @classmethod
    def _normalize_allowed(
        cls,
        allowed_action_ids: list[str] | set[str] | tuple[str, ...] | None,
    ) -> tuple[str, ...]:
        if not allowed_action_ids:
            return ()
        seen: set[str] = set()
        ordered: list[str] = []
        for raw in allowed_action_ids:
            token = str(raw or "").strip()
            if not token or token in seen:
                continue
            seen.add(token)
            ordered.append(token)
        return tuple(ordered)

    @classmethod
    def _cache_config(cls, config: dict[str, Any]) -> dict[str, Any]:
        node = config.get("cache") if isinstance(config.get("cache"), dict) else {}
        enabled = bool(node.get("enabled", True))
        try:
            ttl = max(1, int(node.get("ttlSeconds") or 45))
        except (TypeError, ValueError):
            ttl = 45
        try:
            max_entries = max(8, int(node.get("maxEntries") or 256))
        except (TypeError, ValueError):
            max_entries = 256
        return {"enabled": enabled, "ttlSeconds": ttl, "maxEntries": max_entries}

    @classmethod
    def _cache_key(cls, normalized: str, allowed: tuple[str, ...]) -> str:
        allow_blob = ",".join(sorted(token.casefold() for token in allowed))
        digest = hashlib.sha256(f"{normalized}|{allow_blob}".encode("utf-8")).hexdigest()
        return digest

    @classmethod
    def _cache_get(
        cls, key: str, ttl_seconds: int
    ) -> tuple[dict[str, str], ...] | None:
        now = time.monotonic()
        with _cache_lock:
            entry = _suggest_cache.get(key)
            if entry is None:
                return None
            expires_at, payload = entry
            if expires_at < now:
                _suggest_cache.pop(key, None)
                return None
            return payload

    @classmethod
    def _cache_store(
        cls,
        key: str,
        items: list[dict[str, str]],
        *,
        ttl_seconds: int,
        max_entries: int,
    ) -> None:
        expires_at = time.monotonic() + float(ttl_seconds)
        payload = tuple(dict(item) for item in items)
        with _cache_lock:
            _suggest_cache[key] = (expires_at, payload)
            if len(_suggest_cache) > max_entries:
                ordered = sorted(_suggest_cache.items(), key=lambda kv: kv[1][0])
                overflow = len(_suggest_cache) - max_entries
                for stale_key, _ in ordered[:overflow]:
                    _suggest_cache.pop(stale_key, None)

    @classmethod
    def _group_allowed(
        cls,
        group_id: str,
        group: dict[str, Any],
        allowed: tuple[str, ...],
        config: dict[str, Any],
    ) -> bool:
        if not allowed:
            return True
        hints = cls._hints_for_group(group_id, group, config)
        if not hints:
            return True
        blob = " ".join(token.casefold() for token in allowed)
        return any(hint in blob for hint in hints)

    @classmethod
    def _capability_candidate_allowed(
        cls,
        item: dict[str, str],
        allowed: tuple[str, ...],
    ) -> bool:
        if not allowed:
            return True
        category = str(item.get("category") or item.get("label") or "").casefold()
        if not category:
            return True
        tokens = [tok for tok in category.replace("/", " ").split() if len(tok) >= 4]
        if not tokens:
            return True
        blob = " ".join(token.casefold() for token in allowed)
        return any(tok in blob for tok in tokens)

    @classmethod
    def _hints_for_group(
        cls,
        group_id: str,
        group: dict[str, Any],
        config: dict[str, Any],
    ) -> tuple[str, ...]:
        mapping = config.get("groupActionHints")
        hints: list[str] = []
        if isinstance(mapping, dict) and group_id in mapping:
            raw = mapping.get(group_id) or []
            if isinstance(raw, list):
                hints.extend(str(x).strip().casefold() for x in raw if str(x).strip())
        for key in ("actionHints", "capabilityHints"):
            raw = group.get(key) or []
            if isinstance(raw, list):
                hints.extend(str(x).strip().casefold() for x in raw if str(x).strip())
        # dedupe
        seen: set[str] = set()
        out: list[str] = []
        for hint in hints:
            if hint in seen:
                continue
            seen.add(hint)
            out.append(hint)
        return tuple(out)

    @classmethod
    def _group_matches(cls, normalized: str, group: dict[str, Any]) -> bool:
        prefixes = [
            ChatMessageNormalizationService.normalize_for_matching(str(item))
            for item in (group.get("prefixes") or [])
            if str(item).strip()
        ]
        markers = [
            ChatMessageNormalizationService.normalize_for_matching(str(item))
            for item in (group.get("markers") or [])
            if str(item).strip()
        ]

        if prefixes and any(
            normalized == prefix or normalized.startswith(f"{prefix} ")
            for prefix in prefixes
        ):
            return True

        if markers and any(marker in normalized for marker in markers):
            return True

        return False

    @classmethod
    def _suggestions_from_capabilities(
        cls,
        normalized: str,
        product_code: str | None,
    ) -> list[dict[str, str]]:
        classification = ChatAssistantContentService.load_bundle(
            "capability_ux_classification"
        )
        keyword_rules = classification.get("keywordRules") or []

        if not isinstance(keyword_rules, list):
            return []

        candidates: list[dict[str, str]] = []
        seen_categories: set[str] = set()

        for item in keyword_rules:
            if not isinstance(item, dict):
                continue

            category = str(item.get("category") or "").strip()
            examples_raw = item.get("examples") or []
            examples = tuple(
                str(example).strip() for example in examples_raw if str(example).strip()
            )

            if not category or category in seen_categories:
                continue

            category_norm = ChatMessageNormalizationService.normalize_for_matching(category)

            if not cls._path_rule_matches(normalized, category_norm, examples):
                continue

            seen_categories.add(category)

            for example in examples[:2]:
                query = cls._resolve_query(example, product_code)

                if not query:
                    continue

                candidates.append(
                    {
                        "label": category,
                        "query": query,
                        "category": category,
                        "source": "ux_capability",
                    }
                )

        return candidates

    @classmethod
    def _path_rule_matches(
        cls,
        normalized: str,
        category_norm: str,
        examples: tuple[str, ...],
    ) -> bool:
        if any(word in category_norm for word in normalized.split() if len(word) >= 4):
            return True

        for example in examples:
            example_norm = ChatMessageNormalizationService.normalize_for_matching(example)

            if normalized and example_norm.startswith(normalized):
                return True

            if any(
                token in example_norm
                for token in normalized.split()
                if len(token) >= 4 and token not in {"produto", "qual", "quais"}
            ):
                return True

        return False

    @classmethod
    def _resolve_query(cls, query: str, product_code: str | None) -> str:
        if not query:
            return ""

        if _PRODUCT_PLACEHOLDER in query:
            if not product_code:
                return ""

            return query.replace(_PRODUCT_PLACEHOLDER, product_code)

        return query

    @classmethod
    def _extract_product_code(cls, text: str) -> str | None:
        return ChatProductQueryIntentService.extract_product_code(text)

    @classmethod
    def _finalize_candidates(
        cls,
        raw: str,
        candidates: list[dict[str, str]],
        config: dict[str, Any],
    ) -> list[dict[str, str]]:
        max_suggestions = max(1, int(config.get("maxSuggestions") or 4))
        raw_norm = ChatMessageNormalizationService.normalize_for_matching(raw)
        seen_queries: set[str] = set()
        resolved: list[dict[str, str]] = []

        for item in candidates:
            query = str(item.get("query") or "").strip()
            query_norm = ChatMessageNormalizationService.normalize_for_matching(query)

            if not query or query_norm in seen_queries:
                continue

            if query_norm == raw_norm:
                continue

            seen_queries.add(query_norm)
            resolved.append(item)

            if len(resolved) >= max_suggestions:
                break

        return resolved
