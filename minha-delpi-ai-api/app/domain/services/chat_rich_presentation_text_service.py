"""Texto narrativo vs. componentes nativos — regras globais do chat (qualquer rota/agente)."""

from __future__ import annotations

import re
from typing import Any


class ChatRichPresentationTextService:
    _VISUAL_VIEW_TOKENS = frozenset(
        {"table", "tree", "chart", "kpi", "dashboard", "line_chart", "bar_chart", "donut"}
    )

    _PRESENTATION_MARKER_RE = re.compile(
        r"\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard)",
        re.IGNORECASE,
    )

    _FOOTER_HINT_RE = re.compile(
        r"A \*\*(?:estrutura|composição|hierarquia|dados)\*\*[^\n]*"
        r"(?:árvore|tabela|gráfico|visualizações)[^\n]*\n?",
        re.IGNORECASE,
    )

    @classmethod
    def _is_tree_presentation(cls, presentation: dict[str, Any] | None) -> bool:
        return isinstance(presentation, dict) and str(presentation.get("type") or "") == "tree"

    @classmethod
    def _is_table_presentation(cls, presentation: dict[str, Any] | None) -> bool:
        return isinstance(presentation, dict) and str(presentation.get("type") or "") == "table"

    @classmethod
    def _is_chart_presentation(cls, presentation: dict[str, Any] | None) -> bool:
        return isinstance(presentation, dict) and str(presentation.get("type") or "") == "chart"

    @classmethod
    def _table_signature(cls, presentation: dict[str, Any]) -> str:
        title = str(presentation.get("title") or "").strip().lower()
        columns = presentation.get("columns") or []
        keys = "|".join(
            str(column.get("key") or "").strip().lower()
            for column in columns
            if isinstance(column, dict)
        )
        rows = presentation.get("rows") or []
        row_count = len(rows) if isinstance(rows, list) else 0

        return f"{title}::{keys}::{row_count}"

    @classmethod
    def _iter_unique_table_presentations(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        tables: list[dict[str, Any]] = []
        bundled = metadata.get("tablePresentations")

        if isinstance(bundled, list):
            for item in bundled:
                if not cls._is_table_presentation(item):
                    continue

                signature = cls._table_signature(item)

                if signature in seen:
                    continue

                seen.add(signature)
                tables.append(item)

        if tables:
            return tables

        for key in (
            "tablePresentation",
            "profileTablePresentation",
            "inspectionTablePresentation",
            "presentation",
        ):
            presentation = metadata.get(key)

            if not cls._is_table_presentation(presentation):
                continue

            signature = cls._table_signature(presentation)

            if signature in seen:
                continue

            seen.add(signature)
            tables.append(presentation)

        return tables

    @classmethod
    def _count_table_presentations(cls, metadata: dict[str, Any]) -> int:
        return len(cls._iter_unique_table_presentations(metadata))

    @classmethod
    def count_complementary_visuals(cls, metadata: dict[str, Any]) -> dict[str, int]:
        primary = metadata.get("presentation") if isinstance(metadata.get("presentation"), dict) else {}

        tables = cls._count_table_presentations(metadata)
        trees = int(
            cls._is_tree_presentation(metadata.get("treePresentation"))
            or cls._is_tree_presentation(primary)
        )
        charts = int(
            cls._is_chart_presentation(metadata.get("chartPresentation"))
            or cls._is_chart_presentation(primary)
        )

        return {"table": tables, "tree": trees, "chart": charts}

    @classmethod
    def has_complementary_visuals(cls, metadata: dict[str, Any]) -> bool:
        counts = cls.count_complementary_visuals(metadata)

        return (counts["table"] + counts["tree"] + counts["chart"]) >= 1

    @classmethod
    def is_stack_layout(cls, metadata: dict[str, Any]) -> bool:
        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict) and str(decision.get("layoutMode") or "") == "stack":
            return True

        views = decision.get("availableViews") if isinstance(decision, dict) else None

        if isinstance(views, list):
            visual_views = [
                str(view).strip().lower()
                for view in views
                if str(view).strip().lower() in cls._VISUAL_VIEW_TOKENS
            ]

            if len(set(visual_views)) >= 2:
                return True

        counts = cls.count_complementary_visuals(metadata)
        kinds = sum(1 for value in counts.values() if value > 0)

        return kinds >= 2 or (counts["table"] >= 2)

    @classmethod
    def should_compact_narrative(
        cls,
        *,
        table_presentations: list[dict[str, Any]] | None = None,
        table_presentation: dict[str, Any] | None = None,
        tree_presentation: dict[str, Any] | None = None,
        chart_presentation: dict[str, Any] | None = None,
        primary_presentation: dict[str, Any] | None = None,
    ) -> bool:
        metadata: dict[str, Any] = {
            "tablePresentations": table_presentations,
            "tablePresentation": table_presentation,
            "treePresentation": tree_presentation,
            "chartPresentation": chart_presentation,
            "presentation": primary_presentation,
        }

        return cls.has_complementary_visuals(metadata)

    @classmethod
    def should_compact_metadata_text(cls, metadata: dict[str, Any]) -> bool:
        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return False

        if not str(text_presentation.get("markdown") or "").strip():
            return False

        return cls.has_complementary_visuals(metadata)

    @classmethod
    def compact_text_markdown(cls, markdown: str, metadata: dict[str, Any]) -> str:
        body = str(markdown or "").strip()

        if not body:
            return ""

        counts = cls.count_complementary_visuals(metadata)

        if counts["table"] >= 1:
            body = cls._strip_markdown_tables(body)

        if counts["tree"] >= 1:
            body = cls._strip_structure_sections(body)

        body = cls._strip_visual_footer_hints(body)
        body = cls._strip_product_profile_prose(body)
        body = cls._strip_opening_structure_inventory(body)
        body = cls._strip_embedded_visual_markers(body)

        return re.sub(r"\n{3,}", "\n\n", body).strip()

    @classmethod
    def _strip_embedded_visual_markers(cls, markdown: str) -> str:
        body = cls._PRESENTATION_MARKER_RE.sub("", markdown)
        body = re.sub(
            r"\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard):\d+]]",
            "",
            body,
            flags=re.IGNORECASE,
        )

        return re.sub(r"\n{3,}", "\n\n", body).strip()

    @classmethod
    def _uses_humanized_stack_sections(cls, metadata: dict[str, Any]) -> bool:
        plan = metadata.get("stackPresentationPlan")

        if isinstance(plan, dict) and plan.get("humanizedSections") is True:
            return True

        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            nested = decision.get("stackPresentationPlan")

            if isinstance(nested, dict) and nested.get("humanizedSections") is True:
                return True

        return False

    @classmethod
    def compact_metadata_text(cls, metadata: dict[str, Any]) -> None:
        if not cls.should_compact_metadata_text(metadata):
            return

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()

        if not markdown:
            return

        compact = cls.compact_text_markdown(markdown, metadata)

        if not compact:
            return

        if cls._uses_humanized_stack_sections(metadata) or cls.is_stack_layout(metadata):
            text_presentation["markdown"] = compact
            return

        text_presentation["markdown"] = cls.embed_visual_markers_in_markdown(
            compact,
            metadata,
        )

    @classmethod
    def should_prefer_authorized_answer_over_llm(cls, tool_calls: list[dict] | None) -> bool:
        if not isinstance(tool_calls, list):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            text_presentation = metadata.get("textPresentation")

            if not isinstance(text_presentation, dict):
                continue

            if not str(text_presentation.get("markdown") or "").strip():
                continue

            if cls.is_stack_layout(metadata) or cls.has_complementary_visuals(metadata):
                return True

        return False

    @classmethod
    def embed_visual_markers_in_markdown(cls, markdown: str, metadata: dict[str, Any]) -> str:
        """Insere [[tabela:n]] / [[arvore]] no texto para o MFE intercalar visuais por seção."""

        body = str(markdown or "").strip()

        if not body or cls._PRESENTATION_MARKER_RE.search(body):
            return body

        table_count = cls._count_table_presentations(metadata)
        counts = cls.count_complementary_visuals(metadata)
        has_tree = counts["tree"] >= 1
        has_chart = counts["chart"] >= 1
        has_destaques = bool(re.search(r"\*\*Destaques\*\*", body, re.IGNORECASE))

        if table_count and not has_destaques:
            pontos_match = re.search(
                r"(?:^|\n)\s*\*\*Pontos de atenção",
                body,
                re.IGNORECASE,
            )
            insert_at = pontos_match.start() if pontos_match else len(body)
            markers = "\n\n".join(f"[[table:{index}]]" for index in range(1, table_count + 1))
            body = f"{body[:insert_at].rstrip()}\n\n{markers}\n\n{body[insert_at:].lstrip()}".strip()

        if not has_destaques:
            tail_markers: list[str] = []

            if has_tree:
                tail_markers.append("[[arvore]]")

            if has_chart:
                tail_markers.append("[[chart]]")

            if tail_markers:
                body = f"{body.rstrip()}\n\n" + "\n\n".join(tail_markers)

        return re.sub(r"\n{3,}", "\n\n", body).strip()

    @classmethod
    def _strip_markdown_tables(cls, markdown: str) -> str:
        lines = markdown.split("\n")
        result: list[str] = []
        skipping = False

        for line in lines:
            trimmed = line.strip()

            if not skipping and trimmed.startswith("|") and "|" in trimmed[1:]:
                skipping = True
                continue

            if skipping:
                if trimmed.startswith("|") or trimmed == "":
                    continue

                skipping = False

            result.append(line)

        return re.sub(r"\n{3,}", "\n\n", "\n".join(result)).strip()

    @classmethod
    def _strip_structure_sections(cls, markdown: str) -> str:
        lines = markdown.split("\n")
        result: list[str] = []
        skipping = False

        for line in lines:
            trimmed = line.strip()

            if (
                not skipping
                and (
                    trimmed.startswith("**Estrutura")
                    or trimmed.startswith("**Componentes")
                    or trimmed.startswith("**Produto pai")
                    or trimmed == "**Estrutura detalhada**"
                )
            ):
                skipping = True
                continue

            if skipping:
                if trimmed.startswith("**Destaques**") or trimmed.startswith("**Pontos de atenção"):
                    skipping = False
                    result.append(line)
                continue

            result.append(line)

        return re.sub(r"\n{3,}", "\n\n", "\n".join(result)).strip()

    @classmethod
    def _strip_visual_footer_hints(cls, markdown: str) -> str:
        body = cls._FOOTER_HINT_RE.sub("", markdown)
        body = re.sub(
            r"Use a \*\*árvore\*\*[^\n]+\n?",
            "",
            body,
            flags=re.IGNORECASE,
        )
        body = re.sub(
            r"Use a \*\*tabela\*\*[^\n]+\n?",
            "",
            body,
            flags=re.IGNORECASE,
        )

        return re.sub(r"\n{3,}", "\n\n", body).strip()

    @classmethod
    def _strip_product_profile_prose(cls, markdown: str) -> str:
        lines = markdown.split("\n")
        filtered: list[str] = []
        kept_product_synopsis = False

        for line in lines:
            trimmed = line.strip()

            if re.match(r"^Produto \*\*[^*]+\*\*:", trimmed, re.IGNORECASE):
                if not kept_product_synopsis:
                    filtered.append(line)
                    kept_product_synopsis = True

                continue

            if re.match(
                r"^(Tipo |Status ativo:|Indicador de bloqueio:|Referência de cliente:|"
                r"Último preço|Última revisão:|Inspeção:|Armazém padrão:)",
                trimmed,
                re.IGNORECASE,
            ):
                continue

            filtered.append(line)

        return re.sub(r"\n{3,}", "\n\n", "\n".join(filtered)).strip()

    @classmethod
    def _strip_opening_structure_inventory(cls, markdown: str) -> str:
        body = re.sub(
            r"O produto \*\*[^*]+\*\*[^.\n]*\.\s*A estrutura de nível \d+ inclui:[\s\S]*?"
            r"(?:Fontes cruzadas nesta consulta:[^\n]+\n?)?",
            "",
            markdown,
            flags=re.IGNORECASE,
        )
        body = re.sub(r"Fontes cruzadas nesta consulta:[^\n]+\n?", "", body, flags=re.IGNORECASE)

        return re.sub(r"\n{3,}", "\n\n", body).strip()
