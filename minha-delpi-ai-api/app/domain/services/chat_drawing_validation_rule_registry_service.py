"""Registro declarativo de regras de validação de desenho por família PA."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

_BUNDLE = "drawing_validation_rules"


class ChatDrawingValidationRuleRegistryService:
    _template_rule_index_cache: dict[str, str] | None = None

    @classmethod
    def is_enabled(
        cls,
        rule_id: str,
        product_code: str,
        *,
        group_code: str | None = None,
    ) -> bool:
        normalized_rule = str(rule_id or "").strip()

        if not normalized_rule:
            return False

        family = cls.resolve_family(product_code, group_code=group_code)
        family_node = cls._family_node(family)
        disabled = cls._rule_names(family_node.get("disabledRules"))

        if normalized_rule in disabled:
            return False

        enabled = cls._rule_names(family_node.get("enabledRules"))

        if not enabled:
            return False

        if "*" in enabled:
            return True

        return normalized_rule in enabled

    @classmethod
    def resolve_family(
        cls,
        product_code: str,
        *,
        group_code: str | None = None,
    ) -> str:
        group = str(group_code or "").strip()

        if group:
            return group[:4]

        normalized = ChatProductQueryIntentService.normalize_product_code(product_code)
        prefix_length = cls._prefix_length()

        if normalized and len(normalized) >= prefix_length:
            return normalized[:prefix_length]

        return cls._default_family()

    @classmethod
    def list_enabled_rules(
        cls,
        product_code: str,
        *,
        group_code: str | None = None,
    ) -> tuple[str, ...]:
        family = cls.resolve_family(product_code, group_code=group_code)
        family_node = cls._family_node(family)
        disabled = cls._rule_names(family_node.get("disabledRules"))
        enabled = cls._rule_names(family_node.get("enabledRules"))
        catalog = cls._rule_catalog()

        if "*" in enabled:
            candidates = tuple(str(key) for key in catalog)
        else:
            candidates = enabled

        return tuple(rule for rule in candidates if rule not in disabled)

    @classmethod
    def rule_for_template(cls, template_key: str) -> str | None:
        normalized = str(template_key or "").strip()

        if not normalized:
            return None

        return cls._template_rule_index().get(normalized)

    @classmethod
    def template_keys_for_rule(cls, rule_id: str) -> tuple[str, ...]:
        node = cls._rule_catalog().get(str(rule_id or "").strip())

        if not isinstance(node, dict):
            return ()

        raw = node.get("templateKeys")

        if not isinstance(raw, list):
            return ()

        return tuple(str(key).strip() for key in raw if str(key).strip())

    @classmethod
    def is_template_enabled(
        cls,
        template_key: str,
        product_code: str,
        *,
        group_code: str | None = None,
    ) -> bool:
        normalized = str(template_key or "").strip()

        if not normalized:
            return True

        if normalized in cls._core_template_keys():
            return True

        rule_id = cls.rule_for_template(normalized)

        if not rule_id:
            return True

        return cls.is_enabled(rule_id, product_code, group_code=group_code)

    @classmethod
    def filter_items(
        cls,
        items: list[dict[str, Any]],
        product_code: str,
        *,
        group_code: str | None = None,
    ) -> list[dict[str, Any]]:
        return [
            item
            for item in items
            if cls.is_template_enabled(
                str(item.get("templateKey") or ""),
                product_code,
                group_code=group_code,
            )
        ]

    @classmethod
    def _core_template_keys(cls) -> frozenset[str]:
        raw = ChatAssistantContentService.get_node(_BUNDLE, "coreTemplateKeys")

        if not isinstance(raw, list):
            return frozenset()

        return frozenset(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def _template_rule_index(cls) -> dict[str, str]:
        if cls._template_rule_index_cache is not None:
            return cls._template_rule_index_cache

        index: dict[str, str] = {}

        for rule_id, node in cls._rule_catalog().items():
            if not isinstance(node, dict):
                continue

            for template_key in node.get("templateKeys") or []:
                normalized = str(template_key).strip()

                if normalized:
                    index[normalized] = str(rule_id)

        cls._template_rule_index_cache = index

        return index

    @classmethod
    def _rule_catalog(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "rules")

        return node if isinstance(node, dict) else {}

    @classmethod
    def _family_node(cls, family: str) -> dict[str, Any]:
        families = ChatAssistantContentService.get_node(_BUNDLE, "families") or {}

        if not isinstance(families, dict):
            return {}

        node = families.get(family)

        if isinstance(node, dict):
            return node

        default = families.get(cls._default_family())

        return default if isinstance(default, dict) else {}

    @classmethod
    def _default_family(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "familyResolution",
                "defaultFamily",
                default="default",
            )
        )

    @classmethod
    def _prefix_length(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "familyResolution",
            "prefixLength",
            default="4",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 4

    @classmethod
    def _rule_names(cls, raw: Any) -> frozenset[str]:
        if not isinstance(raw, list):
            return frozenset()

        return frozenset(str(item).strip() for item in raw if str(item).strip())
