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
            plan["sectionIntros"] = {}
            return plan

        visibility = cls._resolve_analyser_visibility(metadata)
        plan["presentationProfile"] = "product_analyser"
        plan["humanizedSections"] = True
        plan["sectionVisibility"] = visibility
        plan["sectionIntros"] = cls._build_section_intros(metadata, visibility)
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
    def _build_section_intros(
        cls,
        metadata: dict[str, Any],
        visibility: dict[str, bool],
    ) -> dict[str, str]:
        markdown = cls._text_markdown(metadata)
        intros: dict[str, str] = {}

        if visibility.get(cls._SCOPE):
            intro = cls._intro_scope(markdown, metadata)

            if intro:
                intros[cls._SCOPE] = intro

        if visibility.get(cls._PROFILE):
            intro = cls._intro_profile(metadata)

            if intro:
                intros[cls._PROFILE] = intro

        if visibility.get(cls._HIGHLIGHTS):
            intro = cls._intro_highlights(markdown)

            if intro:
                intros[cls._HIGHLIGHTS] = intro

        if visibility.get(cls._GUIDE):
            intro = cls._intro_table_role(
                metadata,
                ("roteiro", "guide"),
                label="roteiro de produção",
            )

            if intro:
                intros[cls._GUIDE] = intro

        if visibility.get(cls._INSPECTION):
            intro = cls._intro_table_role(
                metadata,
                ("inspeção", "inspecao", "inspection"),
                label="plano de inspeção",
            )

            if intro:
                intros[cls._INSPECTION] = intro

        if visibility.get(cls._STRUCTURE):
            intro = cls._intro_structure(metadata)

            if intro:
                intros[cls._STRUCTURE] = intro

        if visibility.get(cls._ATTENTION):
            intro = cls._intro_attention(markdown)

            if intro:
                intros[cls._ATTENTION] = intro

        return intros

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
    def _intro_scope(cls, markdown: str, metadata: dict[str, Any]) -> str:
        code = cls._product_code_from_path(metadata)
        title_match = re.search(r"^###\s+(.+)$", markdown, flags=re.MULTILINE)
        title = cls._strip_md(title_match.group(1)) if title_match else ""

        for line in markdown.splitlines():
            stripped = line.strip()

            if not stripped or stripped.startswith("#") or stripped.startswith("**"):
                continue

            if "análise integrada" in stripped.lower():
                if code and code not in stripped:
                    return f"{stripped} Produto {code} em foco."

                return stripped

        if title and code:
            return f"{title} — visão integrada de cadastro, roteiro, inspeção e BOM."

        if code:
            return f"Análise completa do produto {code} nesta consulta."

        return title

    @classmethod
    def _profile_table(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        for presentation in cls._table_presentations(metadata):
            title = str(presentation.get("title") or "").strip().lower()

            if title.startswith("produto ") or "ficha" in title or "cadastro" in title:
                return presentation

        profile = metadata.get("profileTablePresentation")

        return profile if isinstance(profile, dict) else None

    @classmethod
    def _field_map_from_profile_rows(cls, rows: list) -> dict[str, str]:
        mapped: dict[str, str] = {}

        for row in rows:
            if not isinstance(row, dict):
                continue

            label = str(row.get("campo") or row.get("field") or "").strip().lower()
            value = row.get("valor", row.get("value"))

            if label and value not in (None, ""):
                mapped[label] = str(value).strip()

        return mapped

    @classmethod
    def _intro_profile(cls, metadata: dict[str, Any]) -> str:
        table = cls._profile_table(metadata)

        if not table:
            return ""

        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        fields = cls._field_map_from_profile_rows(rows)
        code = fields.get("código")
        description = fields.get("descrição")
        product_type = fields.get("tipo")
        blocked = fields.get("bloqueio")
        bits: list[str] = []

        if code:
            bits.append(str(code))

        if description:
            bits.append(str(description))

        if product_type:
            bits.append(f"tipo {product_type}")

        if blocked:
            bits.append(f"bloqueio {blocked}")

        if not bits:
            return f"Ficha com {len(rows)} campo(s) retornado(s) pela API."

        summary = " · ".join(bits[:4])

        if len(rows) > 4:
            return f"{summary} — {len(rows)} campos no cadastro."

        return summary

    @classmethod
    def _intro_highlights(cls, markdown: str) -> str:
        if "**Destaques**" not in markdown:
            return ""

        block = markdown.split("**Destaques**", 1)[-1]

        for token in ("**Pontos de atenção", "###"):
            if token in block:
                block = block.split(token, 1)[0]

        bullets = []

        for line in block.splitlines():
            stripped = line.strip()

            if stripped.startswith("-") or stripped.startswith("*"):
                token = cls._strip_md(stripped.lstrip("-* ").strip())

                if token and not _ABSENCE_INSIGHT_RE.search(token):
                    bullets.append(token)

        if not bullets:
            return ""

        if len(bullets) == 1:
            return bullets[0]

        preview = "; ".join(cls._strip_md(item) for item in bullets[:3])

        if len(bullets) > 3:
            return f"{preview} (+{len(bullets) - 3} destaque(s))."

        return preview

    @classmethod
    def _intro_table_role(
        cls,
        metadata: dict[str, Any],
        title_tokens: tuple[str, ...],
        *,
        label: str,
    ) -> str:
        for presentation in cls._table_presentations(metadata):
            title = str(presentation.get("title") or "").strip().lower()

            if not any(token in title for token in title_tokens):
                continue

            rows = presentation.get("rows") if isinstance(presentation.get("rows"), list) else []
            count = len(rows)

            if not count:
                return ""

            products = {
                str(row.get("product_code") or row.get("product") or "").strip()
                for row in rows
                if isinstance(row, dict)
            }
            products.discard("")

            if len(products) > 1:
                return (
                    f"{count} registro(s) de {label} "
                    f"em {len(products)} produto(s) da hierarquia."
                )

            return f"{count} registro(s) no {label} retornado pela API."

        return ""

    @classmethod
    def _tree_node_count(cls, metadata: dict[str, Any]) -> int:
        for key in ("treePresentation", "presentation"):
            presentation = metadata.get(key)

            if not isinstance(presentation, dict) or presentation.get("type") != "tree":
                continue

            nodes = presentation.get("nodes")

            if isinstance(nodes, list):
                return len(nodes)

            root = presentation.get("root")

            if isinstance(root, dict):
                children = root.get("children")

                if isinstance(children, list) and children:
                    return len(children) + 1

                return 1

        return 0

    @classmethod
    def _intro_structure(cls, metadata: dict[str, Any]) -> str:
        count = cls._tree_node_count(metadata)
        tree = metadata.get("treePresentation") or metadata.get("presentation")
        title = ""

        if isinstance(tree, dict):
            title = cls._strip_md(str(tree.get("title") or ""))

        if count and title:
            return f"{title} — {count} nó(s) na hierarquia PA → PI → MP."

        if count:
            return f"Composição com {count} nó(s) na árvore de estrutura."

        return title

    @classmethod
    def _intro_attention(cls, markdown: str) -> str:
        if "**Pontos de atenção" not in markdown:
            return ""

        block = markdown.split("**Pontos de atenção", 1)[-1]
        points = [
            cls._strip_md(match.group(1))
            for match in re.finditer(r"^\s*\d+\.\s+(.+)$", block, flags=re.MULTILINE)
            if match.group(1).strip()
        ]

        if not points:
            return ""

        if len(points) == 1:
            return points[0]

        preview = "; ".join(points[:2])

        if len(points) > 2:
            return f"{preview} (+{len(points) - 2} ponto(s))."

        return preview

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
