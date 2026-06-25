"""Registry declarativo de commentary por profileKey — Playbook 21 W1b."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)

_TEMPLATE_PROSE_SKIP = "skip"
_TEMPLATE_PROSE_FULL = "full"


class ChatOperationalCommentaryProfileService:
    @classmethod
    def registered_profile_keys(cls) -> frozenset[str]:
        node = ChatHumanizedDataResponseContentService.get_node("commentaryProfiles")

        if not isinstance(node, dict):
            return frozenset()

        return frozenset(str(key).strip() for key in node if str(key).strip())

    @classmethod
    def profile_config(cls, profile_key: str) -> dict[str, Any]:
        node = ChatHumanizedDataResponseContentService.get_node(
            "commentaryProfiles",
            str(profile_key or "").strip(),
        )

        return node if isinstance(node, dict) else {}

    @classmethod
    def content_section(cls, profile_key: str) -> str:
        section = str(cls.profile_config(profile_key).get("contentSection") or "").strip()

        if section:
            return section

        return str(profile_key or "").strip()

    @classmethod
    def builder_strategy(cls, profile_key: str) -> str:
        strategy = str(cls.profile_config(profile_key).get("builderStrategy") or "").strip()

        return strategy or "none"

    @classmethod
    def question_synthesis_strategy(cls, profile_key: str) -> str:
        return str(
            cls.profile_config(profile_key).get("questionSynthesisStrategy") or ""
        ).strip()

    @classmethod
    def build_from_highlight_rules(
        cls,
        profile_key: str,
        data: dict[str, Any],
        *,
        format_line: Callable[[str, str, dict[str, str]], str],
    ) -> dict[str, Any] | None:
        highlights = cls.build_highlight_rules(profile_key, data, format_line=format_line)
        visual_hints = cls.visual_hints(profile_key)

        if not highlights and not visual_hints:
            return None

        return {
            "profileKey": profile_key,
            "highlights": highlights,
            "summaryLines": highlights[:4],
            "visualHints": visual_hints or None,
        }

    @classmethod
    def template_prose_commentary_mode(cls, profile_key: str) -> str:
        mode = str(
            cls.profile_config(profile_key).get("templateProseCommentary") or _TEMPLATE_PROSE_FULL
        ).strip()

        return mode if mode in {_TEMPLATE_PROSE_SKIP, _TEMPLATE_PROSE_FULL} else _TEMPLATE_PROSE_FULL

    @classmethod
    def should_skip_template_prose_commentary(cls, profile_key: str) -> bool:
        return cls.template_prose_commentary_mode(profile_key) == _TEMPLATE_PROSE_SKIP

    @classmethod
    def visual_hints(cls, profile_key: str) -> list[str]:
        hints = cls.profile_config(profile_key).get("visualHints")

        if not isinstance(hints, list):
            return []

        return [str(item).strip() for item in hints if str(item or "").strip()]

    @classmethod
    def try_build_metadata_only(
        cls,
        profile_key: str,
    ) -> dict[str, Any] | None:
        if not cls.should_skip_template_prose_commentary(profile_key):
            return None

        hints = cls.visual_hints(profile_key)

        return {
            "profileKey": profile_key,
            "highlights": [],
            "summaryLines": [],
            "visualHints": hints,
            "metadataOnly": True,
        }

    @classmethod
    def build_highlight_rules(
        cls,
        profile_key: str,
        data: dict[str, Any],
        *,
        format_line: Callable[[str, str, dict[str, str]], str],
    ) -> list[str]:
        rules = cls.profile_config(profile_key).get("highlightRules")

        if not isinstance(rules, list):
            return []

        highlights: list[str] = []

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            if not cls._rule_matches(rule, data):
                continue

            presenter = rule.get("presenter")

            if not isinstance(presenter, dict):
                continue

            section = str(presenter.get("section") or "").strip()
            key = str(presenter.get("key") or "").strip()

            if not section or not key:
                continue

            values = cls._resolve_rule_values(rule.get("values"), data)

            if values is None:
                continue

            line = format_line(section, key, values)

            if line and line not in highlights:
                highlights.append(line)

        return highlights

    @classmethod
    def _rule_matches(cls, rule: dict[str, Any], data: dict[str, Any]) -> bool:
        when_all = rule.get("whenAll")

        if not isinstance(when_all, list):
            return True

        return all(cls._condition_matches(condition, data) for condition in when_all)

    @classmethod
    def _condition_matches(cls, condition: Any, data: dict[str, Any]) -> bool:
        if not isinstance(condition, dict):
            return False

        path = str(condition.get("path") or "").strip()
        op = str(condition.get("op") or "present").strip()
        expected = condition.get("value")
        actual = cls._resolve_path(data, path)

        if op == "present":
            return actual not in (None, "", [], {})

        if op == "absent":
            return actual in (None, "", [], {})

        if op == "nonempty":
            if isinstance(actual, list):
                return bool(actual)

            return bool(str(actual or "").strip())

        if op == "eq":
            return cls._coerce_number(actual) == cls._coerce_number(expected)

        if op == "gt":
            left = cls._coerce_number(actual)
            right = cls._coerce_number(expected)

            return left is not None and right is not None and left > right

        if op == "or_nonempty":
            paths = condition.get("paths")

            if not isinstance(paths, list):
                return False

            return any(cls._condition_matches({"path": item, "op": "nonempty"}, data) for item in paths)

        return False

    @classmethod
    def _resolve_rule_values(
        cls,
        values: Any,
        data: dict[str, Any],
    ) -> dict[str, str] | None:
        if not isinstance(values, dict):
            return {}

        resolved: dict[str, str] = {}

        for key, token in values.items():
            binding = str(token or "").strip()

            if binding.startswith("{") and binding.endswith("}"):
                path = binding[1:-1].strip()
                resolved_value = cls._resolve_path(data, path)
                resolved[str(key)] = str(resolved_value if resolved_value is not None else "")
            else:
                resolved[str(key)] = binding

        return resolved

    @classmethod
    def _resolve_path(cls, data: dict[str, Any], path: str) -> Any:
        if not path:
            return None

        if path == "product.product_code":
            product = data.get("product")

            if isinstance(product, dict):
                token = product.get("product_code") or product.get("code")

                return token if token not in (None, "") else None

        if path == "summary.total_raw_materials":
            summary = data.get("summary")

            if isinstance(summary, dict):
                mp_count = summary.get("total_raw_materials")

                if mp_count not in (None, ""):
                    return mp_count

                items = data.get("items")

                if isinstance(items, list) and items:
                    return len(items)

        current: Any = data

        for part in path.split("."):
            if not isinstance(current, dict):
                return None

            current = current.get(part)

        return current

    @staticmethod
    def _coerce_number(value: Any) -> float | None:
        if value in (None, ""):
            return None

        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return None
