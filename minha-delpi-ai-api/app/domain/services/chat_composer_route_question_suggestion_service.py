"""Sugestões de perguntas no composer — rotas operacionais conhecidas (Playbook 14+)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import ChatMessageNormalizationService

_BUNDLE = "composer_route_questions"
_PRODUCT_CODE_PATTERN = re.compile(r"\b\d{5,}\b")
_PRODUCT_PLACEHOLDER = "{productCode}"


class ChatComposerRouteQuestionSuggestionService:
    @classmethod
    def suggest(cls, text: str) -> list[dict[str, str]]:
        config = ChatAssistantContentService.get_node(_BUNDLE) or {}

        if not isinstance(config, dict) or not config.get("enabled", True):
            return []

        raw = str(text or "").strip()
        normalized = ChatMessageNormalizationService.normalize_for_matching(raw)

        min_len = int(config.get("minDraftLength") or 3)

        if len(normalized) < min_len:
            return []

        product_code = cls._extract_product_code(raw)
        candidates: list[dict[str, str]] = []

        for group in config.get("groups") or []:
            if not isinstance(group, dict):
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
                        "groupId": str(group.get("id") or "").strip(),
                    }
                )

        if config.get("includePathRulesFromCapabilities", True):
            candidates.extend(cls._suggestions_from_capabilities(normalized, product_code))

        return cls._finalize_candidates(raw, candidates, config)

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
        path_rules = ChatAssistantContentService.get_node("capabilities", "pathRules") or []

        if not isinstance(path_rules, list):
            return []

        candidates: list[dict[str, str]] = []

        for item in path_rules:
            if not isinstance(item, dict):
                continue

            token = str(item.get("token") or "").strip()
            category = str(item.get("category") or "").strip()
            examples_raw = item.get("examples") or []
            examples = tuple(str(example).strip() for example in examples_raw if str(example).strip())

            if not token or not category:
                continue

            category_norm = ChatMessageNormalizationService.normalize_for_matching(category)

            if not cls._path_rule_matches(normalized, category_norm, examples):
                continue

            for example in examples[:2]:
                query = cls._resolve_query(example, product_code)

                if not query:
                    continue

                candidates.append(
                    {
                        "label": category,
                        "query": query,
                        "category": category,
                        "source": "path_rule",
                        "routeToken": token,
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
        match = _PRODUCT_CODE_PATTERN.search(text)

        return match.group(0) if match else None

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
