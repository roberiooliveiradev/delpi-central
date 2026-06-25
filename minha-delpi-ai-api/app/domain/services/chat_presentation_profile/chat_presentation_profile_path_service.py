"""Delegate — perfis declarativos de apresentação."""

from __future__ import annotations

from typing import Any

from app.domain.services.openapi_presentation_profile_deriver_service import (
    OpenApiPresentationProfileDeriverService,
)
from app.domain.services.openapi_operation_contract_service import (
    OpenApiOperationContractService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_facade_access import (
    presentation_profile_service,
)



class ChatPresentationProfilePathService:
    @classmethod
    def entity_path_hints(cls) -> dict[str, str]:
        raw = presentation_profile_service().mapping("entityPathHints")

        return {
            str(entity): str(path)
            for entity, path in raw.items()
            if str(entity).strip() and str(path).strip()
        }

    @classmethod
    def entity_path_hint_pairs(cls) -> list[tuple[str, str]]:
        pairs = list(presentation_profile_service().entity_path_hints().items())
        aliases = presentation_profile_service().node("entityPathHintAliases") or {}

        if isinstance(aliases, dict):
            for entity, paths in aliases.items():
                entity_token = str(entity or "").strip()

                if not entity_token or not isinstance(paths, list):
                    continue

                for path in paths:
                    path_token = str(path or "").strip()

                    if path_token:
                        pairs.append((entity_token, path_token))

        pairs.sort(key=lambda item: len(item[1]), reverse=True)
        return pairs

    @classmethod
    def entity_path_hint(cls, entity: str | None) -> str:
        token = str(entity or "").strip()

        if not token:
            return ""

        return str(presentation_profile_service().entity_path_hints().get(token) or "")

    @classmethod
    def path_entity_fallbacks(cls) -> tuple[tuple[str, str], ...]:
        rules = presentation_profile_service().node("pathEntityFallbacks") or []
        pairs: list[tuple[str, str]] = []

        if isinstance(rules, list):
            for rule in rules:
                if not isinstance(rule, dict):
                    continue

                fragment = str(rule.get("contains") or "").strip()
                entity = str(rule.get("entity") or "").strip()

                if fragment and entity:
                    pairs.append((fragment, entity))

        return tuple(
            sorted(pairs, key=lambda item: len(item[0]), reverse=True),
        )

    @classmethod
    def _matches_product_path_hint(cls, path_lower: str, hint_lower: str) -> bool:
        marker = "/products/"

        if marker not in hint_lower or marker not in path_lower:
            return False

        path_tail = path_lower.split(marker, 1)[1]
        hint_tail = hint_lower.split(marker, 1)[1]
        path_parts = [part for part in path_tail.split("/") if part]
        hint_parts = [part for part in hint_tail.split("/") if part]

        if not path_parts or not hint_parts:
            return False

        if hint_parts[0] not in {"0", "{code}"}:
            return False

        if not (path_parts[0].isdigit() or path_parts[0] in {"{code}", "0"}):
            return False

        return path_parts[1:] == hint_parts[1:]

    @classmethod
    def _matches_quality_action_plan_path_hint(cls, path_lower: str, hint_lower: str) -> bool:
        marker = "/quality/action-plans/"

        if marker not in hint_lower or marker not in path_lower:
            return False

        path_tail = path_lower.split(marker, 1)[1]
        hint_tail = hint_lower.split(marker, 1)[1]
        path_parts = [part for part in path_tail.split("/") if part]
        hint_parts = [part for part in hint_tail.split("/") if part]

        if not path_parts or not hint_parts:
            return False

        if hint_parts[0] not in {"0", "{plan_id}"}:
            return False

        if len(hint_parts) == 1:
            if path_parts[0] in {"dashboard", "overdue", "recurrence"}:
                return False

            return bool(path_parts[0])

        plan_segment = path_parts[0]

        if plan_segment in {"dashboard", "overdue"}:
            return False

        if plan_segment in {"0", "{plan_id}"}:
            return path_parts[1:] == hint_parts[1:]

        return bool(plan_segment) and path_parts[1:] == hint_parts[1:]

    @classmethod
    def _matches_entity_path_hint(cls, path_lower: str, hint_lower: str) -> bool:
        if not hint_lower:
            return False

        if path_lower == hint_lower or path_lower.startswith(f"{hint_lower}/"):
            return True

        if path_lower.endswith(hint_lower):
            return True

        if cls._matches_product_path_hint(path_lower, hint_lower):
            return True

        return cls._matches_quality_action_plan_path_hint(path_lower, hint_lower)

    @classmethod
    def _resolve_quality_action_plan_entity_from_path(cls, lowered: str) -> str | None:
        if lowered == "/quality/action-plans":
            return "quality_action_plan"

        if lowered == "/quality/action-plans/overdue":
            return "quality_action_plan"

        if lowered == "/quality/action-plans/dashboard":
            return "quality_action_plan_dashboard"

        if lowered == "/quality/action-plans/recurrence":
            return "quality_action_plan_recurrence"

        return None

    @classmethod
    def resolve_entity_from_path(cls, path: str | None) -> str | None:
        lowered = presentation_profile_service().path_lowered(path).rstrip("/")

        if not lowered:
            return None

        quality_entity = cls._resolve_quality_action_plan_entity_from_path(lowered)

        if quality_entity:
            return quality_entity

        for entity, hint in presentation_profile_service().entity_path_hint_pairs():
            hint_lower = str(hint or "").lower().rstrip("/")

            if cls._matches_entity_path_hint(lowered, hint_lower):
                return entity

        for fragment, entity in presentation_profile_service().path_entity_fallbacks():
            if fragment in lowered:
                return entity

        parts = lowered.rstrip("/").split("/")

        if (
            len(parts) == 3
            and parts[1] == "products"
            and (parts[2].isdigit() or parts[2] in {"{code}", "0"})
        ):
            return "product"

        return None

    @classmethod
    def path_lowered(cls, path: str | None) -> str:
        lowered = str(path or "").strip().lower()

        return lowered.replace("/finacial/", "/financial/")

