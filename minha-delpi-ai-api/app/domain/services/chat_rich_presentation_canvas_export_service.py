"""Exporta apresentações ricas (tabela, árvore, gráfico) para markdown da lousa."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)

_MAX_TABLE_ROWS = 80
_MAX_TREE_ROWS = 120


class ChatRichPresentationCanvasExportService:
    @classmethod
    def build_markdown_from_assistant(
        cls,
        content: str,
        metadata: dict[str, Any] | None,
    ) -> str:
        base = cls._normalize_base_text(content, metadata)
        tool_calls = metadata.get("toolCalls") if isinstance(metadata, dict) else None
        visual_sections = cls._sections_from_tool_calls(tool_calls)

        if not visual_sections:
            return base

        return ChatRichPresentationTextService._strip_embedded_visual_markers(
            cls._merge_sections([base, *visual_sections])
        )

    @classmethod
    def sections_from_tool_metadata(cls, metadata: dict[str, Any]) -> list[str]:
        return cls._visual_sections_from_metadata(metadata)

    @classmethod
    def _sections_from_tool_calls(cls, tool_calls: list[dict] | None) -> list[str]:
        sections: list[str] = []

        if not isinstance(tool_calls, list):
            return sections

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            for section in cls._visual_sections_from_metadata(metadata):
                if section and section not in sections:
                    sections.append(section)

        return sections

    @classmethod
    def _visual_sections_from_metadata(cls, metadata: dict[str, Any]) -> list[str]:
        sections: list[str] = []

        for table in ChatRichPresentationTextService._iter_unique_table_presentations(metadata):
            section = cls._table_presentation_to_markdown(table)

            if section:
                sections.append(section)

        tree = cls._resolve_tree_presentation(metadata)

        if tree:
            section = cls._tree_presentation_to_markdown(tree)

            if section:
                sections.append(section)

        chart = cls._resolve_chart_presentation(metadata)

        if chart:
            section = cls._chart_presentation_to_markdown(chart)

            if section:
                sections.append(section)

        return sections

    @classmethod
    def _normalize_base_text(cls, content: str, metadata: dict[str, Any] | None) -> str:
        text = str(content or "").strip()

        if not text and isinstance(metadata, dict):
            for tool_call in metadata.get("toolCalls") or []:
                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_metadata = tool_call.get("metadata")

                if not isinstance(tool_metadata, dict):
                    continue

                text_presentation = tool_metadata.get("textPresentation")

                if isinstance(text_presentation, dict):
                    candidate = str(text_presentation.get("markdown") or "").strip()

                    if candidate:
                        text = candidate
                        break

        return ChatRichPresentationTextService._strip_embedded_visual_markers(text)

    @classmethod
    def _resolve_tree_presentation(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        for key in ("treePresentation", "presentation"):
            presentation = metadata.get(key)

            if ChatRichPresentationTextService._is_tree_presentation(presentation):
                return presentation

        return None

    @classmethod
    def _resolve_chart_presentation(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        for key in ("chartPresentation", "presentation"):
            presentation = metadata.get(key)

            if ChatRichPresentationTextService._is_chart_presentation(presentation):
                return presentation

        return None

    @classmethod
    def _table_presentation_to_markdown(cls, presentation: dict[str, Any]) -> str | None:
        title = str(presentation.get("title") or "Tabela").strip()
        columns = [
            column
            for column in (presentation.get("columns") or [])
            if isinstance(column, dict)
        ]
        rows = [
            row for row in (presentation.get("rows") or []) if isinstance(row, dict)
        ]

        if not columns or not rows:
            return f"### {title}" if title else None

        header = " | ".join(
            str(column.get("label") or column.get("key") or "").strip()
            for column in columns
        )
        body_lines: list[str] = []

        for row in rows[:_MAX_TABLE_ROWS]:
            body_lines.append(
                " | ".join(str(row.get(column.get("key"), "")) for column in columns)
            )

        lines = [
            f"### {title}",
            "",
            f"| {header} |",
            f"| {' | '.join(['---'] * len(columns))} |",
            *[f"| {line} |" for line in body_lines],
        ]

        if len(rows) > _MAX_TABLE_ROWS:
            lines.extend(["", f"_… e mais {len(rows) - _MAX_TABLE_ROWS} registro(s)._"])

        return "\n".join(lines).strip()

    @classmethod
    def _tree_presentation_to_markdown(cls, presentation: dict[str, Any]) -> str | None:
        root = presentation.get("root")

        if not isinstance(root, dict):
            return None

        title = str(presentation.get("title") or "Estrutura").strip()
        rows = cls._flatten_tree_rows(root)

        if not rows:
            return f"### {title}"

        header = "Nível | Código | Descrição | Tipo | Unid. | Qtde | Caminho"
        body_lines = [
            " | ".join(
                [
                    str(row["nivel"]),
                    row["codigo"],
                    row["descricao"],
                    row["tipo"],
                    row["unidade"],
                    row["quantidade"],
                    row["caminho"],
                ]
            )
            for row in rows[:_MAX_TREE_ROWS]
        ]

        lines = [
            f"### {title}",
            "",
            f"| {header} |",
            f"| {' | '.join(['---'] * 7)} |",
            *[f"| {line} |" for line in body_lines],
        ]

        if len(rows) > _MAX_TREE_ROWS:
            lines.extend(["", f"_… e mais {len(rows) - _MAX_TREE_ROWS} nó(s)._"])

        return "\n".join(lines).strip()

    @classmethod
    def _flatten_tree_rows(
        cls,
        node: dict[str, Any],
        *,
        depth: int = 0,
        path: list[str] | None = None,
    ) -> list[dict[str, str]]:
        current_path = [
            *(path or []),
            str(node.get("label") or node.get("id") or "").strip(),
        ]
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        rows = [
            {
                "nivel": str(depth),
                "codigo": str(node.get("label") or node.get("id") or "").strip(),
                "descricao": str(node.get("subtitle") or "").strip(),
                "tipo": str(node.get("badge") or "").strip(),
                "unidade": str(meta.get("unit") or "").strip(),
                "quantidade": cls._format_quantity(meta.get("quantity")),
                "caminho": " > ".join(part for part in current_path if part),
            }
        ]

        for child in node.get("children") or []:
            if isinstance(child, dict):
                rows.extend(
                    cls._flatten_tree_rows(child, depth=depth + 1, path=current_path)
                )

        return rows

    @classmethod
    def _chart_presentation_to_markdown(cls, presentation: dict[str, Any]) -> str | None:
        title = str(presentation.get("title") or "Gráfico").strip()
        chart_type = str(presentation.get("chartType") or "chart").strip()
        rows = cls._chart_rows(presentation)

        if not rows:
            return f"### {title}\n\n_Tipo: {chart_type}_\n\n_Sem dados para exibir._"

        columns = list(rows[0].keys())
        header = " | ".join(columns)
        body_lines = [
            " | ".join(str(row.get(column, "")) for column in columns) for row in rows
        ]

        return "\n".join(
            [
                f"### {title}",
                "",
                f"**Tipo:** {chart_type}",
                "",
                f"| {header} |",
                f"| {' | '.join(['---'] * len(columns))} |",
                *[f"| {line} |" for line in body_lines],
            ]
        ).strip()

    @classmethod
    def _chart_rows(cls, presentation: dict[str, Any]) -> list[dict[str, Any]]:
        data = presentation.get("data")

        if isinstance(data, list) and data:
            return [row for row in data if isinstance(row, dict)]

        labels = presentation.get("labels")
        datasets = presentation.get("datasets")

        if not isinstance(labels, list) or not labels:
            return []

        values = []

        if isinstance(datasets, list) and datasets:
            first = datasets[0]

            if isinstance(first, dict) and isinstance(first.get("data"), list):
                values = first["data"]

        if len(labels) != len(values):
            return []

        return [
            {"label": str(label), "value": value}
            for label, value in zip(labels, values)
        ]

    @classmethod
    def _format_quantity(cls, value: Any) -> str:
        if value is None or value == "":
            return ""

        try:
            numeric = float(value)

            if numeric.is_integer():
                return str(int(numeric))

            return f"{numeric:.4f}".rstrip("0").rstrip(".")
        except (TypeError, ValueError):
            return str(value)

    @classmethod
    def _merge_sections(cls, sections: list[str]) -> str:
        parts = [str(section or "").strip() for section in sections]

        return "\n\n".join(part for part in parts if part)
