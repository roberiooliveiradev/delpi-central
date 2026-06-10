"""Marcadores de seção no markdown e framing genérico do stack (Fase 4)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)

_SECTION_MARKER_RE = re.compile(r"<!--\s*section:([a-z_]+)\s*-->")
_NARRATIVE_SLOT_SECTIONS: tuple[tuple[str, str], ...] = (
    ("lead", "scope"),
    ("profileTables", "profile"),
    ("highlights", "highlights"),
    ("operationalTables", "guide"),
    ("tailVisuals", "structure"),
    ("attention", "attention"),
)

_DESTAQUES_HEADER_RE = re.compile(r"(?m)^\s*\*\*Destaques\*\*\s*$")
_ATTENTION_HEADER_RE = re.compile(r"(?m)^\*\*Pontos de atenção")


class ChatPresentationStackMarkdownService:
    @classmethod
    def enrich_stack_plan(cls, metadata: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        profile_key = str(
            plan.get("presentationProfileKey")
            or plan.get("presentationProfile")
            or cls.resolve_profile_key(metadata)
            or ""
        ).strip()

        if not plan.get("humanizedSections"):
            plan = cls._enrich_profile_stack_plan(metadata, plan, profile_key=profile_key)

        cls.apply_section_markers(metadata, plan)
        return plan

    @classmethod
    def apply_section_markers(cls, metadata: dict[str, Any], plan: dict[str, Any]) -> None:
        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()

        if not markdown:
            return

        enriched = cls._inject_section_markers(markdown, plan)

        if enriched != markdown:
            text_presentation["markdown"] = enriched

    @classmethod
    def _enrich_profile_stack_plan(
        cls,
        metadata: dict[str, Any],
        plan: dict[str, Any],
        *,
        profile_key: str,
    ) -> dict[str, Any]:
        markdown = cls._text_markdown(metadata)
        visibility = cls._resolve_stack_visibility(metadata, markdown)
        has_humanized = any(visibility.values())

        if not has_humanized:
            return plan

        plan["humanizedSections"] = True
        plan["presentationProfile"] = profile_key or plan.get("presentationProfile")
        plan["sectionVisibility"] = visibility
        plan["sectionFraming"] = cls._build_generic_section_framing(visibility, profile_key)
        plan["narrativeOrder"] = cls._narrative_order_for_visibility(
            visibility,
            profile_first=bool(plan.get("profileFirst", True)),
            highlights_after_profile=bool(plan.get("highlightsAfterProfile", True)),
            attention_last=bool(plan.get("attentionLast")),
        )
        return plan

    @classmethod
    def _resolve_stack_visibility(
        cls,
        metadata: dict[str, Any],
        markdown: str,
    ) -> dict[str, bool]:
        has_visual_tail = (
            cls._has_tree(metadata)
            or cls._has_chart(metadata)
            or cls._has_kpi(metadata)
            or cls._has_dashboard(metadata)
        )

        return {
            "scope": bool(markdown.strip()),
            "profile": cls._has_profile_table(metadata),
            "highlights": cls._has_highlights(markdown),
            "guide": cls._has_operational_tables(metadata),
            "inspection": False,
            "structure": has_visual_tail,
            "attention": cls._has_attention(markdown),
        }

    @classmethod
    def _build_generic_section_framing(
        cls,
        visibility: dict[str, bool],
        profile_key: str,
    ) -> dict[str, str]:
        profile_texts = ChatAssistantContentService.get_node(
            "presenter_content",
            "stackSectionFraming",
            "byProfile",
            profile_key,
        )
        default_texts = ChatAssistantContentService.get_node(
            "presenter_content",
            "stackSectionFraming",
            "default",
        )

        profile_map = profile_texts if isinstance(profile_texts, dict) else {}
        default_map = default_texts if isinstance(default_texts, dict) else {}
        framing: dict[str, str] = {}

        for section_id, visible in visibility.items():
            if not visible:
                continue

            template = str(
                profile_map.get(section_id)
                or default_map.get(section_id)
                or ""
            ).strip()

            if template:
                framing[section_id] = template

        return framing

    @classmethod
    def _narrative_order_for_visibility(
        cls,
        visibility: dict[str, bool],
        *,
        profile_first: bool,
        highlights_after_profile: bool,
        attention_last: bool,
    ) -> list[str]:
        order = ["lead"]

        if profile_first and visibility.get("profile"):
            order.append("profileTables")

        if highlights_after_profile and visibility.get("highlights"):
            order.append("highlights")

        if visibility.get("guide"):
            order.append("operationalTables")

        if visibility.get("structure"):
            order.append("tailVisuals")

        if attention_last and visibility.get("attention"):
            order.append("attention")

        return order

    @classmethod
    def _inject_section_markers(cls, markdown: str, plan: dict[str, Any]) -> str:
        visibility = plan.get("sectionVisibility") if isinstance(plan.get("sectionVisibility"), dict) else {}
        updated = markdown

        if visibility.get("highlights") and "**Destaques**" in updated:
            if "<!-- section:highlights -->" not in updated:
                updated = _DESTAQUES_HEADER_RE.sub(
                    "<!-- section:highlights -->\n\n**Destaques**",
                    updated,
                    count=1,
                )

        if visibility.get("attention") and "**Pontos de atenção" in updated:
            if "<!-- section:attention -->" not in updated:
                updated = _ATTENTION_HEADER_RE.sub(
                    lambda match: f"<!-- section:attention -->\n\n{match.group(0)}",
                    updated,
                    count=1,
                )

        if (
            visibility.get("scope")
            and "<!-- section:scope -->" not in updated
            and not updated.lstrip().startswith("<!-- section:scope -->")
        ):
            lines = updated.splitlines()

            if lines and lines[0].startswith("###"):
                header = lines[0]
                body = "\n".join(lines[1:]).lstrip()
                updated = f"{header}\n\n<!-- section:scope -->\n\n{body}".strip()

        for slot, section_id in _NARRATIVE_SLOT_SECTIONS:
            marker = f"<!-- section:{section_id} -->"

            if marker in updated:
                continue

            if section_id == "profile" and visibility.get("profile"):
                continue

            if section_id == "guide" and visibility.get("guide"):
                continue

            if section_id == "structure" and visibility.get("structure"):
                continue

            _ = slot

        return updated

    @classmethod
    def _has_highlights(cls, markdown: str) -> bool:
        if "**Destaques**" not in markdown:
            return False

        block = markdown.split("**Destaques**", 1)[-1]
        bullets = [
            line.strip()
            for line in block.splitlines()
            if line.strip().startswith(("-", "*"))
        ]

        return bool(bullets)

    @classmethod
    def _has_attention(cls, markdown: str) -> bool:
        if "**Pontos de atenção" not in markdown:
            return False

        block = markdown.split("**Pontos de atenção", 1)[-1]
        return bool(re.search(r"^\s*\d+\.\s+\S", block, flags=re.MULTILINE))

    @classmethod
    def _has_profile_table(cls, metadata: dict[str, Any]) -> bool:
        for key in ("profileTablePresentation", "tablePresentation", "presentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type") == "table":
                rows = presentation.get("rows") or []

                if rows:
                    return True

        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            for presentation in bulk:
                if not isinstance(presentation, dict):
                    continue

                title = str(presentation.get("title") or "").lower()

                if title.startswith("produto ") and presentation.get("rows"):
                    return True

        return False

    @classmethod
    def _has_operational_tables(cls, metadata: dict[str, Any]) -> bool:
        count = 0

        for key in ("tablePresentation", "presentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type") == "table":
                rows = presentation.get("rows") or []

                if rows:
                    count += 1

        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            for presentation in bulk:
                if isinstance(presentation, dict) and presentation.get("type") == "table":
                    rows = presentation.get("rows") or []

                    if rows:
                        count += 1

        return count >= 1

    @classmethod
    def _has_tree(cls, metadata: dict[str, Any]) -> bool:
        for key in ("treePresentation", "presentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type") == "tree":
                return True

        return False

    @classmethod
    def _has_chart(cls, metadata: dict[str, Any]) -> bool:
        for key in ("chartPresentation", "presentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type") == "chart":
                return True

        return False

    @classmethod
    def _has_kpi(cls, metadata: dict[str, Any]) -> bool:
        for key in ("kpiPresentation", "presentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type") == "kpi":
                return True

        return False

    @classmethod
    def _has_dashboard(cls, metadata: dict[str, Any]) -> bool:
        for key in ("dashboardPresentation", "presentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type") == "dashboard":
                return True

        return False

    @classmethod
    def _text_markdown(cls, metadata: dict[str, Any]) -> str:
        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return ""

        return str(text_presentation.get("markdown") or "").strip()

    @classmethod
    def resolve_profile_key(cls, metadata: dict[str, Any]) -> str:
        path = str(metadata.get("path") or "")
        entity = None
        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            raw_entity = api_meta.get("entity")

            if isinstance(raw_entity, str) and raw_entity.strip():
                entity = raw_entity.strip()

        return ChatPresentationProfileService.resolve_profile_key(path, entity)
