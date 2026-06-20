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

    _SECTION_MARKER_RE = re.compile(r"<!--\s*section:(\w+)\s*-->")

    _DATA_ANSWER_DROP_SECTIONS = frozenset({"highlights", "profile", "summary"})

    _QUICK_LAYER_HEADER_RE = re.compile(
        r"(?:^|\n)\s*"
        r"\*\*(?:Resumo|Próxima ação(?: recomendada)?|Interpretação)\*\*\s*",
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
    def _is_kpi_presentation(cls, presentation: dict[str, Any] | None) -> bool:
        return isinstance(presentation, dict) and str(presentation.get("type") or "") == "kpi"

    @classmethod
    def _is_dashboard_presentation(cls, presentation: dict[str, Any] | None) -> bool:
        return isinstance(presentation, dict) and str(presentation.get("type") or "") == "dashboard"

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
        kpis = int(
            cls._is_kpi_presentation(metadata.get("kpiPresentation"))
            or cls._is_kpi_presentation(primary)
        )
        dashboards = int(
            cls._is_dashboard_presentation(metadata.get("dashboardPresentation"))
            or cls._is_dashboard_presentation(primary)
        )

        return {
            "table": tables,
            "tree": trees,
            "chart": charts,
            "kpi": kpis,
            "dashboard": dashboards,
        }

    @classmethod
    def has_complementary_visuals(cls, metadata: dict[str, Any]) -> bool:
        counts = cls.count_complementary_visuals(metadata)

        return sum(counts.values()) >= 1

    @classmethod
    def is_stack_layout(cls, metadata: dict[str, Any]) -> bool:
        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            layout = str(decision.get("layoutMode") or "").strip().lower()

            if layout == "single":
                return False

            if layout == "stack":
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
        kpi_presentation: dict[str, Any] | None = None,
        dashboard_presentation: dict[str, Any] | None = None,
    ) -> bool:
        """Stack humanizado (qualquer action): narrativa completa no texto; visuais nos slots."""

        del (
            table_presentations,
            table_presentation,
            tree_presentation,
            chart_presentation,
            primary_presentation,
            kpi_presentation,
            dashboard_presentation,
        )

        return False

    @classmethod
    def should_compact_metadata_text(cls, metadata: dict[str, Any]) -> bool:
        if cls._uses_humanized_stack_sections(metadata):
            return False

        if cls.is_stack_layout(metadata):
            return False

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return False

        if not str(text_presentation.get("markdown") or "").strip():
            return False

        if cls.has_complementary_visuals(metadata):
            return False

        return False

    @classmethod
    def compact_text_markdown(cls, markdown: str, metadata: dict[str, Any]) -> str:
        body = str(markdown or "").strip()

        if not body:
            return ""

        counts = cls.count_complementary_visuals(metadata)

        if counts["table"] >= 1:
            body = cls._strip_markdown_tables(body)
            body = cls._strip_stock_position_detail_section(body)

        if counts["tree"] >= 1:
            body = cls._strip_structure_sections(body)

        body = cls._strip_visual_footer_hints(body)
        body = cls._strip_product_profile_prose(body)
        body = cls._strip_opening_structure_inventory(body)
        body = cls._strip_embedded_visual_markers(body)

        if isinstance(metadata.get("dataAnswer"), dict):
            body = cls.strip_highlights_block(body)

        return re.sub(r"\n{3,}", "\n\n", body).strip()

    @classmethod
    def strip_data_answer_quick_layers(cls, markdown: str) -> str:
        body = str(markdown or "").strip()

        if not body:
            return ""

        while True:
            match = cls._QUICK_LAYER_HEADER_RE.search(body)

            if not match:
                break

            head = body[: match.start()].rstrip()
            tail = body[match.end() :]
            next_section = re.search(
                r"\n(?:\*\*[^*]+\*\*|<!-- section:[^>]+ -->|#{1,3} )",
                tail,
            )
            remainder = tail[next_section.start() + 1 :].strip() if next_section else ""
            body = "\n\n".join(part for part in [head, remainder] if part).strip()

        body = re.sub(
            r"(?:^|\n)Status geral:\s*\*\*[^*]+\*\*[^\n]*",
            "",
            body,
            flags=re.IGNORECASE,
        )
        body = re.sub(
            r"(?:^|\n)Referência da consulta:\s*\*\*[^*]+\*\*[^\n]*",
            "",
            body,
            flags=re.IGNORECASE,
        )

        return re.sub(r"\n{3,}", "\n\n", body).strip()

    @classmethod
    def prepare_evidence_first_chat_narrative(cls, metadata: dict[str, Any]) -> None:
        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()

        if not markdown:
            return

        decision = metadata.get("presentationDecision")
        layout_mode = ""
        explicit_format = str(metadata.get("explicitSessionFormat") or "").strip().casefold()

        if isinstance(decision, dict):
            layout_mode = str(decision.get("layoutMode") or "").strip().casefold()

        body = cls.strip_data_answer_quick_layers(markdown)
        body = cls.strip_highlights_block(body)

        if explicit_format != "text" and layout_mode in {"stack", "single"}:
            body = cls._strip_embedded_visual_sections_for_stack(body)

        if explicit_format == "dashboard":
            body = cls._compact_native_view_lead(body)

        body = cls._align_narrative_with_data_answer(body, metadata)

        text_presentation["markdown"] = re.sub(r"\n{3,}", "\n\n", body).strip()

    @classmethod
    def _resolve_data_answer_lead(cls, data_answer: dict[str, Any]) -> str:
        summary = data_answer.get("summary")

        if not isinstance(summary, dict):
            return ""

        answer = str(summary.get("answer") or "").strip()
        meaning = str(summary.get("meaning") or "").strip()

        if answer and meaning and meaning not in answer:
            return f"{answer} {meaning}".strip()

        return answer

    @classmethod
    def _strip_operational_presenter_summary_paragraphs(cls, markdown: str) -> str:
        paragraphs = re.split(r"\n{2,}", str(markdown or "").strip())
        kept: list[str] = []

        for paragraph in paragraphs:
            trimmed = paragraph.strip()

            if not trimmed:
                continue

            if trimmed.startswith("<!--") or trimmed.startswith("#"):
                kept.append(trimmed)
                continue

            if re.match(r"(?i)^Consultei o estoque\b", trimmed):
                continue

            if re.match(r"(?i)^Encontrei \*\*", trimmed):
                continue

            kept.append(trimmed)

        return "\n\n".join(kept).strip()

    @classmethod
    def _inject_data_answer_lead_in_scope(cls, markdown: str, lead: str) -> str:
        if not lead or lead in markdown:
            return markdown

        marker = "<!-- section:scope -->"

        if marker in markdown:
            head, tail = markdown.split(marker, 1)
            tail_chunks = [part.strip() for part in tail.strip().split("\n\n") if part.strip()]
            framing = tail_chunks[0] if tail_chunks else ""
            rest = "\n\n".join(tail_chunks[1:]).strip() if len(tail_chunks) > 1 else ""
            scope_parts = [marker, ""]

            if framing:
                scope_parts.extend([framing, ""])

            scope_parts.append(lead)

            if rest:
                scope_parts.extend(["", rest])

            rebuilt = "\n".join(scope_parts).strip()
            return f"{head.rstrip()}\n\n{rebuilt}".strip()

        title_match = re.match(r"(^(?:#{1,3} .+\n+))", markdown, flags=re.MULTILINE)

        if title_match:
            title_block = title_match.group(1)
            remainder = markdown[title_match.end() :].strip()
            return f"{title_block}\n{lead}\n\n{remainder}".strip()

        return f"{lead}\n\n{markdown}".strip()

    @classmethod
    def _align_narrative_with_data_answer(
        cls,
        markdown: str,
        metadata: dict[str, Any],
    ) -> str:
        data_answer = metadata.get("dataAnswer")

        if not isinstance(data_answer, dict):
            return markdown

        lead = cls._resolve_data_answer_lead(data_answer)

        if not lead:
            return markdown

        body = cls._strip_operational_presenter_summary_paragraphs(markdown)

        return cls._inject_data_answer_lead_in_scope(body, lead)

    @classmethod
    def _strip_embedded_visual_sections_for_stack(cls, markdown: str) -> str:
        body = cls._strip_markdown_tables(markdown)
        body = cls._strip_titled_section(body, "Panorama fabril")
        body = cls._strip_titled_section(body, "Composição")
        body = cls._strip_code_fence_blocks(body)
        body = cls._strip_chart_fallback_sections(body)

        for title in (
            "Saldo consolidado por matéria-prima",
            "Estoque de matérias-primas",
            "Produção (PA / PI / OP / apontamentos)",
            "Saldo de MP",
        ):
            body = cls._strip_titled_section(body, title)

        return body.strip()

    @classmethod
    def _strip_code_fence_blocks(cls, markdown: str) -> str:
        return re.sub(r"(?:^|\n)\s*```[\w-]*\s*\n[\s\S]*?\n```", "", markdown).strip()

    @classmethod
    def _strip_chart_fallback_sections(cls, markdown: str) -> str:
        pattern = (
            r"(?:^|\n)\s*\*\*[^*]+\*\*\s*\n+"
            r"_Dados do gráfico[\s\S]*?(?=\n\*\*[^*]+\*\*|\n#{1,3} |\Z)"
        )

        return re.sub(pattern, "", markdown, flags=re.IGNORECASE).strip()

    @classmethod
    def _compact_native_view_lead(cls, markdown: str) -> str:
        body = cls._strip_embedded_visual_sections_for_stack(markdown)
        lines = body.splitlines()
        title_line = ""

        if lines and lines[0].startswith("###"):
            title_line = lines[0]
            body = "\n".join(lines[1:]).strip()

        paragraphs = [part.strip() for part in re.split(r"\n{2,}", body) if part.strip()]
        kept: list[str] = []

        for paragraph in paragraphs[:3]:
            if paragraph.startswith("<!-- section:"):
                continue

            if paragraph.startswith("**") and paragraph.endswith("**") and len(paragraph) < 120:
                kept.append(paragraph)
                continue

            if len(paragraph) <= 320:
                kept.append(paragraph)

            if len(kept) >= 2:
                break

        rebuilt = [title_line, ""] if title_line else []

        if kept:
            rebuilt.append("\n\n".join(kept))

        return "\n".join(part for part in rebuilt if part).strip()

    @classmethod
    def _strip_titled_section(cls, markdown: str, title: str) -> str:
        escaped = re.escape(str(title or "").strip())
        pattern = rf"(?:^|\n)\s*\*\*{escaped}\*\*\s*\n[\s\S]*?(?=\n\*\*[^*]+\*\*|\n#{1,3} |\Z)"

        return re.sub(pattern, "", markdown, flags=re.IGNORECASE).strip()

    @classmethod
    def build_scope_only_narrative(cls, markdown: str, *, framing: str = "") -> str:
        body = str(markdown or "").strip()

        if not body:
            return ""

        lines = body.splitlines()
        title_line = ""

        if lines and lines[0].startswith("###"):
            title_line = lines[0]
            body = "\n".join(lines[1:]).strip()

        rebuilt: list[str] = []

        if title_line:
            rebuilt.extend([title_line, ""])

        if cls._SECTION_MARKER_RE.search(body):
            parts = cls._SECTION_MARKER_RE.split(body)
            preamble = str(parts[0] or "").strip()
            index = 1

            rebuilt.extend(["<!-- section:scope -->", ""])
            scope_body = framing.strip() or cls.strip_data_answer_quick_layers(preamble).strip()

            if scope_body:
                rebuilt.append(scope_body)

            while index < len(parts):
                section_id = str(parts[index] or "").strip()
                content = str(parts[index + 1] if index + 1 < len(parts) else "").strip()
                index += 2

                if section_id in cls._DATA_ANSWER_DROP_SECTIONS:
                    continue

                if section_id == "scope":
                    continue

                rebuilt.extend([f"<!-- section:{section_id} -->", ""])

                cleaned = cls.strip_data_answer_quick_layers(content).strip()

                if cleaned:
                    rebuilt.append(cleaned)

            return "\n".join(rebuilt).strip()

        rebuilt.extend(["<!-- section:scope -->", ""])
        scope_body = framing.strip() or cls.strip_data_answer_quick_layers(body).strip()

        if scope_body:
            rebuilt.append(scope_body)

        return "\n".join(rebuilt).strip()

    @classmethod
    def strip_highlights_block(cls, markdown: str) -> str:
        header_match = re.search(
            r"(?:^|\n)\s*\*\*(?:Destaques|Indicadores principais)\*\*\s*$",
            markdown,
            re.IGNORECASE | re.MULTILINE,
        )

        if not header_match:
            return markdown

        head = markdown[: header_match.start()].rstrip()
        tail_lines = markdown[header_match.end() :].splitlines()
        remainder: list[str] = []
        skipping_bullets = True

        for line in tail_lines:
            trimmed = line.strip()

            if skipping_bullets and (not trimmed or trimmed.startswith("- ")):
                continue

            skipping_bullets = False
            remainder.append(line)

        return "\n\n".join(part for part in [head, "\n".join(remainder).strip()] if part).strip()

    @classmethod
    def _strip_stock_position_detail_section(cls, markdown: str) -> str:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        header = ChatAssistantContentService.get(
            "presenter_content",
            "generic",
            "stockTextDetailHeader",
            default="Detalhamento por filial e armazém",
        )
        escaped = re.escape(str(header or "").strip())
        pattern = rf"\n\*\*{escaped}\*\*\s*\n(?:[ \t]*- .+(?:\n|$))+"

        return re.sub(pattern, "", markdown, flags=re.IGNORECASE).strip()

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
    def _is_playbook_operational_tool_metadata(cls, metadata: dict[str, Any]) -> bool:
        from app.domain.services.chat_operational_response_profile_service import (
            ChatOperationalResponseProfileService,
        )

        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            entity = api_meta.get("entity")

            if ChatOperationalResponseProfileService.is_playbook_operational_entity(
                str(entity or "").strip() or None
            ):
                return True

        path = str(metadata.get("path") or "")

        return ChatOperationalResponseProfileService.is_playbook_operational_path(path)

    @classmethod
    def _should_prefer_playbook_operational_text_answer(cls, metadata: dict[str, Any]) -> bool:
        if not cls._is_playbook_operational_tool_metadata(metadata):
            return False

        humanized = metadata.get("humanizedSummary")

        if isinstance(humanized, dict):
            linhas = [
                str(line).strip()
                for line in (humanized.get("linhas") or [])
                if str(line or "").strip()
            ]

            if linhas:
                return True

        text_presentation = metadata.get("textPresentation")

        if isinstance(text_presentation, dict):
            markdown = str(text_presentation.get("markdown") or "").strip()

            if markdown:
                return True

        return False

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

            if metadata.get("llmProseDecoupled"):
                return False

            if cls._should_prefer_playbook_operational_text_answer(metadata):
                return True

            text_presentation = metadata.get("textPresentation")

            if not isinstance(text_presentation, dict):
                continue

            if not str(text_presentation.get("markdown") or "").strip():
                continue

            decision = metadata.get("presentationDecision") or {}
            selected = str(decision.get("selected") or metadata.get("preferredFormat") or "").strip().lower()

            if selected in {"table", "tree", "chart", "kpi", "dashboard"} and not cls.is_stack_layout(
                metadata
            ):
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
