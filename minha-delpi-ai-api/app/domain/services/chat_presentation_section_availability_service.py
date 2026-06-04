"""Disponibilidade de seções humanizadas — inteligência de apresentação (chat base)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_presentation_route_policy_service import (
    ChatPresentationRoutePolicyService,
)

_ABSENCE_INSIGHT_RE = re.compile(
    r"(ainda não cadastrad|não (?:há|ha|foi) retornad|sem operações|sem historico|sem histórico|"
    r"não retornou|não há histórico|sem histórico recente|sem compras recentes)",
    re.IGNORECASE,
)


class ChatPresentationSectionAvailabilityService:
    """Define quais blocos do mockup analyser têm dado — o MFE só renderiza o que vier True."""

    _PROFILE = "profile"
    _GUIDE = "guide"
    _INSPECTION = "inspection"
    _STRUCTURE = "structure"
    _SCOPE = "scope"
    _HIGHLIGHTS = "highlights"
    _ATTENTION = "attention"

    @classmethod
    def enrich_stack_plan(cls, metadata: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        path = str(metadata.get("path") or "")
        lowered = ChatPresentationRoutePolicyService.path_lowered(path)

        if not ChatPresentationRoutePolicyService.is_analyser_route(lowered):
            plan["presentationProfile"] = "generic_stack"
            plan["humanizedSections"] = False
            plan["sectionVisibility"] = {}
            plan["sectionFraming"] = {}
            return plan

        visibility = cls._resolve_analyser_visibility(metadata)
        plan["presentationProfile"] = "product_analyser"
        plan["humanizedSections"] = True
        plan["sectionVisibility"] = visibility
        plan["sectionFraming"] = cls._build_section_framing(metadata, visibility)
        plan["narrativeOrder"] = cls._narrative_order_for_visibility(
            visibility,
            attention_last=bool(visibility.get(cls._ATTENTION)),
            highlights_after_profile=bool(visibility.get(cls._HIGHLIGHTS)),
            profile_first=bool(visibility.get(cls._PROFILE)),
        )
        return plan

    @classmethod
    def filter_analyser_highlights(cls, insights: list[str]) -> list[str]:
        """Remove bullets que só comunicam ausência de dado (seção vazia não deve narrar falta)."""
        filtered: list[str] = []

        for line in insights:
            token = str(line or "").strip()

            if not token or _ABSENCE_INSIGHT_RE.search(token):
                continue

            filtered.append(token)

        return filtered

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

        if profile_first and visibility.get(cls._PROFILE):
            order.append("profileTables")

        if highlights_after_profile and visibility.get(cls._HIGHLIGHTS):
            order.append("highlights")

        if visibility.get(cls._GUIDE) or visibility.get(cls._INSPECTION):
            order.append("operationalTables")

        if visibility.get(cls._STRUCTURE):
            order.append("tailVisuals")

        if attention_last and visibility.get(cls._ATTENTION):
            order.append("attention")

        return order

    @classmethod
    def _resolve_analyser_visibility(cls, metadata: dict[str, Any]) -> dict[str, bool]:
        markdown = cls._text_markdown(metadata)

        return {
            cls._SCOPE: cls._has_scope(markdown),
            cls._PROFILE: cls._has_profile_table(metadata),
            cls._HIGHLIGHTS: cls._has_highlights(markdown),
            cls._GUIDE: cls._has_table_role(metadata, ("roteiro", "guide")),
            cls._INSPECTION: cls._has_table_role(metadata, ("inspeção", "inspecao", "inspection")),
            cls._STRUCTURE: cls._has_tree(metadata),
            cls._ATTENTION: cls._has_attention(markdown),
        }

    @classmethod
    def _build_section_framing(
        cls,
        metadata: dict[str, Any],
        visibility: dict[str, bool],
    ) -> dict[str, str]:
        """Uma frase interpretiva por seção — sem repetir tabela, bullets ou ficha."""
        code = cls._product_code_from_path(metadata)
        framing: dict[str, str] = {}

        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        section_texts = ChatProductOperationalContentService.get_mapping(
            "presentation",
            "sectionFraming",
        )

        if visibility.get(cls._SCOPE):
            if code:
                template = section_texts.get("scopeWithCode", "")
                framing[cls._SCOPE] = template.format(code=code) if template else ""
            else:
                framing[cls._SCOPE] = section_texts.get("scopeGeneric", "")

        if visibility.get(cls._PROFILE):
            framing[cls._PROFILE] = section_texts.get("profile", "")

        if visibility.get(cls._HIGHLIGHTS):
            framing[cls._HIGHLIGHTS] = section_texts.get("highlights", "")

        if visibility.get(cls._GUIDE):
            framing[cls._GUIDE] = section_texts.get("guide", "")

        if visibility.get(cls._INSPECTION):
            framing[cls._INSPECTION] = section_texts.get("inspection", "")

        if visibility.get(cls._STRUCTURE):
            framing[cls._STRUCTURE] = section_texts.get("structure", "")

        if visibility.get(cls._ATTENTION):
            framing[cls._ATTENTION] = section_texts.get("attention", "")

        return framing

    @classmethod
    def _strip_md(cls, value: str) -> str:
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", str(value or ""))
        text = re.sub(r"`([^`]+)`", r"\1", text)

        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def _product_code_from_path(cls, metadata: dict[str, Any]) -> str:
        match = re.search(r"/products/([^/]+)/analyser", str(metadata.get("path") or ""), re.I)

        return match.group(1).strip() if match else ""

    @classmethod
    def _has_scope(cls, markdown: str) -> bool:
        return bool(markdown.strip())

    @classmethod
    def _has_highlights(cls, markdown: str) -> bool:
        if "**Destaques**" not in markdown:
            return False

        block = markdown.split("**Destaques**", 1)[-1]
        stop_tokens = ("**Pontos de atenção", "###", "**Plano", "**Roteiro")

        for token in stop_tokens:
            if token in block:
                block = block.split(token, 1)[0]

        bullets = [
            line.strip()
            for line in block.splitlines()
            if line.strip().startswith("-") or line.strip().startswith("*")
        ]

        substantive = [
            line
            for line in bullets
            if len(line) > 2 and not _ABSENCE_INSIGHT_RE.search(line)
        ]

        return bool(substantive)

    @classmethod
    def _has_attention(cls, markdown: str) -> bool:
        if "**Pontos de atenção" not in markdown:
            return False

        block = markdown.split("**Pontos de atenção", 1)[-1]
        numbered = re.findall(r"^\s*\d+\.\s+\S", block, flags=re.MULTILINE)

        return bool(numbered)

    @classmethod
    def _has_profile_table(cls, metadata: dict[str, Any]) -> bool:
        for presentation in cls._table_presentations(metadata):
            title = str(presentation.get("title") or "").strip().lower()

            if title.startswith("produto ") or "ficha" in title or "cadastro" in title:
                return cls._table_has_rows(presentation)

        profile = metadata.get("profileTablePresentation")

        if isinstance(profile, dict):
            return cls._table_has_rows(profile)

        return False

    @classmethod
    def _has_table_role(cls, metadata: dict[str, Any], title_tokens: tuple[str, ...]) -> bool:
        for presentation in cls._table_presentations(metadata):
            title = str(presentation.get("title") or "").strip().lower()

            if any(token in title for token in title_tokens):
                return cls._table_has_rows(presentation)

        return False

    @classmethod
    def _has_tree(cls, metadata: dict[str, Any]) -> bool:
        for key in ("treePresentation", "presentation"):
            presentation = metadata.get(key)

            if not isinstance(presentation, dict) or presentation.get("type") != "tree":
                continue

            nodes = presentation.get("nodes") or presentation.get("root")

            if isinstance(nodes, list) and nodes:
                return True

            if isinstance(nodes, dict) and nodes:
                return True

        return False

    @classmethod
    def _table_presentations(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        tables: list[dict[str, Any]] = []
        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            tables.extend(item for item in bulk if isinstance(item, dict))

        for key in ("tablePresentation", "profileTablePresentation", "inspectionTablePresentation"):
            item = metadata.get(key)

            if isinstance(item, dict) and item.get("type") == "table":
                tables.append(item)

        return tables

    @classmethod
    def _table_has_rows(cls, presentation: dict[str, Any]) -> bool:
        rows = presentation.get("rows")

        if isinstance(rows, list) and rows:
            return True

        return False

    @classmethod
    def _text_markdown(cls, metadata: dict[str, Any]) -> str:
        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return ""

        return str(text_presentation.get("markdown") or "").strip()
