"""Sugestões de rival de família após empty_result REST — sem SQL cego."""

from __future__ import annotations

from typing import Any

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionEmptyRivalRecommendationService:
    @classmethod
    def suggestions_for_tool_calls(
        cls,
        tool_calls: list | None,
        *,
        error_type: str,
    ) -> list[dict[str, str]]:
        if error_type not in {"empty_result", "empty_product_parents"}:
            return []

        operation_id, path, profile_key = cls._extract_identity(tool_calls)
        families = ExternalActionResponseContentService.object_list(
            "actionSelection",
            "emptyRivalRecommendations",
        )

        matched: list[dict[str, str]] = []
        for family in families:
            if not cls._family_matches(
                family,
                operation_id=operation_id,
                path=path,
                profile_key=profile_key,
            ):
                continue
            for item in family.get("suggestions") or []:
                if not isinstance(item, dict):
                    continue
                label = str(item.get("label") or "").strip()
                query = str(item.get("query") or label).strip()
                if label and query:
                    matched.append({"label": label, "query": query})

        return matched

    @classmethod
    def should_skip_auto_retry(cls, tool_calls: list | None, *, error_type: str) -> bool:
        return bool(
            cls.suggestions_for_tool_calls(tool_calls, error_type=error_type)
        )

    @classmethod
    def _family_matches(
        cls,
        family: dict,
        *,
        operation_id: str,
        path: str,
        profile_key: str,
    ) -> bool:
        op_ids = {
            str(item).strip().lower()
            for item in (family.get("operationIds") or [])
            if str(item).strip()
        }
        if operation_id and operation_id.lower() in op_ids:
            return True

        profiles = {
            str(item).strip().lower()
            for item in (family.get("profileKeys") or [])
            if str(item).strip()
        }
        if profile_key and profile_key.lower() in profiles:
            return True

        markers = [
            str(item).lower()
            for item in (family.get("pathMarkers") or [])
            if str(item).strip()
        ]
        if path and any(marker in path.lower() for marker in markers):
            return True

        return False

    @classmethod
    def _extract_identity(
        cls,
        tool_calls: list | None,
    ) -> tuple[str, str, str]:
        if not tool_calls:
            return "", "", ""

        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
            arguments = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
            operation_id = str(
                meta.get("operationId")
                or arguments.get("operationId")
                or ""
            ).strip()
            path = str(meta.get("path") or arguments.get("path") or "").strip()
            profile_key = str(
                meta.get("profileKey")
                or meta.get("presentationProfileKey")
                or ""
            ).strip()
            if operation_id or path or profile_key:
                return operation_id, path, profile_key

        return "", "", ""
