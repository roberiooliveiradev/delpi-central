"""Marcos leves de adoção (Playbook 10 — gamificação sem exagero)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _milestones_content() -> list[dict[str, Any]]:
    data = ContentService.load_json("assistant/onboarding")
    items = data.get("milestones") or []

    return [dict(item) for item in items if isinstance(item, dict)]


class ChatOnboardingMilestoneService:
    @classmethod
    def list_milestones(cls) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []

        for item in _milestones_content():
            milestone_id = str(item.get("id") or "").strip()
            message = str(item.get("message") or "").strip()

            if milestone_id and message:
                result.append(
                    {
                        "id": milestone_id,
                        "message": message,
                        "label": str(item.get("label") or milestone_id).strip(),
                    }
                )

        return result

    @classmethod
    def achieved_from_history(cls, previous_messages: list[Any] | None) -> set[str]:
        achieved: set[str] = set()

        for item in previous_messages or []:
            meta = getattr(item, "metadata", None)

            if meta is None and isinstance(item, dict):
                meta = item.get("metadata")

            if not isinstance(meta, dict):
                continue

            stored = meta.get("onboardingMilestonesAchieved")

            if isinstance(stored, list):
                for token in stored:
                    normalized = str(token or "").strip()

                    if normalized:
                        achieved.add(normalized)

            celebrations = meta.get("milestoneCelebrations")

            if isinstance(celebrations, list):
                for celebration in celebrations:
                    if isinstance(celebration, dict):
                        milestone_id = str(celebration.get("id") or "").strip()

                        if milestone_id:
                            achieved.add(milestone_id)

        return achieved

    @classmethod
    def detect_new_milestones(
        cls,
        *,
        previous_messages: list[Any] | None,
        pipeline_stages: list[str] | None,
        tool_calls: list[dict] | None,
        had_attachments: bool = False,
        canvas_open: bool = False,
    ) -> list[dict[str, str]]:
        achieved = cls.achieved_from_history(previous_messages)
        stages = [str(stage) for stage in (pipeline_stages or [])]
        new_ids: list[str] = []

        if "first_operational_query" not in achieved and cls._operational_success(
            tool_calls,
            stages,
        ):
            new_ids.append("first_operational_query")

        if "first_canvas" not in achieved and (
            canvas_open or "canvas" in stages
        ):
            new_ids.append("first_canvas")

        if "first_attachment" not in achieved and (
            had_attachments
            or "attachment_welcome" in stages
            or "attachment_compare" in stages
        ):
            new_ids.append("first_attachment")

        if "first_capabilities" not in achieved and (
            "capabilities" in stages or "onboarding_training" in stages
        ):
            new_ids.append("first_capabilities")

        celebrations: list[dict[str, str]] = []
        lookup = {item["id"]: item for item in cls.list_milestones()}

        for milestone_id in new_ids[:1]:
            item = lookup.get(milestone_id)

            if item:
                celebrations.append(item)

        return celebrations

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        previous_messages: list[Any] | None,
        pipeline_stages: list[str] | None,
        tool_calls: list[dict] | None,
        had_attachments: bool = False,
        canvas_open: bool = False,
    ) -> None:
        achieved = cls.achieved_from_history(previous_messages)
        celebrations = cls.detect_new_milestones(
            previous_messages=previous_messages,
            pipeline_stages=pipeline_stages,
            tool_calls=tool_calls,
            had_attachments=had_attachments,
            canvas_open=canvas_open,
        )

        for item in celebrations:
            achieved.add(str(item.get("id") or "").strip())

        if achieved:
            metadata["onboardingMilestonesAchieved"] = sorted(
                token for token in achieved if token
            )

        if celebrations:
            metadata["milestoneCelebrations"] = celebrations

    @staticmethod
    def _call_counts_as_operational_success(call: dict) -> bool:
        if not isinstance(call, dict) or str(call.get("name") or "") != "execute_external_action":
            return False

        call_meta = call.get("metadata")

        if not isinstance(call_meta, dict) or call_meta.get("ok") is not True:
            return False

        if call_meta.get("sqlSchemaPrefetch") or call_meta.get("suppressClientPresentation"):
            return False

        path = str(call_meta.get("path") or "").lower()

        if "/system/tables" in path and (
            "/columns" in path or "/schema" in path or "/relations" in path
        ):
            return False

        return True

    @staticmethod
    def _operational_success(
        tool_calls: list[dict] | None,
        stages: list[str],
    ) -> bool:
        if any(
            "operational" in stage
            for stage in stages
            if stage.startswith("intent:")
        ):
            return any(
                ChatOnboardingMilestoneService._call_counts_as_operational_success(call)
                for call in (tool_calls or [])
            )

        return any(
            ChatOnboardingMilestoneService._call_counts_as_operational_success(call)
            for call in (tool_calls or [])
        )
