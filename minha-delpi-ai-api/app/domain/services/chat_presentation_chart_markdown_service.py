"""Gráficos operacionais embutidos em markdown (Mermaid / tabela) — Playbook 12 R14."""

from __future__ import annotations

import math
import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)

_MAX_CHART_POINTS = 40

_MERMAID_XY_CHART_TYPES = frozenset(
    {
        "bar",
        "bar_chart",
        "line",
        "line_chart",
        "multi_line",
        "area",
        "area_chart",
        "horizontal_bar",
    }
)

_MERMAID_PIE_CHART_TYPES = frozenset({"donut", "pie"})

_TABLE_FALLBACK_CHART_TYPES = frozenset(
    {
        "heatmap",
        "gauge",
        "scatter",
        "histogram",
        "combo",
        "combo_chart",
        "stacked_bar",
        "grouped_bar",
        "stacked",
        "grouped",
        # xychart-beta do Mermaid não suporta barras horizontais de forma confiável.
        "horizontal_bar",
    }
)


class ChatPresentationChartMarkdownService:
    @classmethod
    def embed_charts_in_text_presentation(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        if metadata.get("ok") is False:
            return

        if not cls._should_embed_charts(metadata):
            return

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()

        if not markdown:
            return

        sections = cls.build_chart_sections(metadata)

        if not sections:
            return

        body = markdown

        for section in sections:
            if section in body:
                continue

            body = f"{body}\n\n{section}".strip()

        text_presentation["markdown"] = body
        cls._finalize_embedded_chart_slot(metadata)

    @classmethod
    def _finalize_embedded_chart_slot(cls, metadata: dict[str, Any]) -> None:
        metadata.pop("chartPresentation", None)

        presentation = metadata.get("presentation")

        if isinstance(presentation, dict) and presentation.get("type") == "chart":
            metadata["presentation"] = None

    @classmethod
    def build_chart_sections(cls, metadata: dict[str, Any]) -> list[str]:
        sections: list[str] = []

        for chart in cls._collect_charts(metadata):
            section = cls._chart_section(chart, metadata=metadata)

            if section:
                sections.append(section)

        return sections

    @classmethod
    def _chart_section(
        cls,
        chart: dict[str, Any],
        *,
        metadata: dict[str, Any],
    ) -> str:
        title = str(chart.get("title") or "").strip()
        heading = f"**{title}**" if title else ChatAssistantContentService.get(
            "presenter_content",
            "generic",
            "chartSectionHeader",
            default="**Gráfico**",
        )

        body = cls._chart_body(chart, metadata=metadata)

        if not body:
            return ""

        return f"{heading}\n\n{body}".strip()

    @classmethod
    def _chart_body(cls, chart: dict[str, Any], *, metadata: dict[str, Any]) -> str:
        chart_type = str(chart.get("chartType") or "bar").strip().lower()
        profile = ChatPresentationProfileService.resolve_profile(
            str(metadata.get("path") or ""),
            cls._resolve_entity(str(metadata.get("path") or "")),
        )
        preferred = str(profile.get("textEmbedChartFormat") or "auto").strip().lower()

        rows = cls._chart_rows(chart)

        if not rows:
            return ""

        if preferred == "mermaid":
            mermaid = cls._mermaid_block_for_embed(chart, rows)

            if mermaid:
                return mermaid

            return cls._table_fallback(chart, rows)

        if preferred == "table" or chart_type in _TABLE_FALLBACK_CHART_TYPES:
            return cls._table_fallback(chart, rows)

        if preferred == "auto":
            mermaid = cls._mermaid_block_for_embed(chart, rows)

            if mermaid:
                return mermaid

        return cls._table_fallback(chart, rows)

    @classmethod
    def _mermaid_block_for_embed(
        cls,
        chart: dict[str, Any],
        rows: list[dict[str, Any]],
    ) -> str:
        chart_type = str(chart.get("chartType") or "bar").strip().lower()
        mermaid_chart = chart

        if chart_type == "horizontal_bar":
            mermaid_chart = {**chart, "chartType": "bar"}

        return cls._mermaid_block(mermaid_chart, rows)

    @classmethod
    def _mermaid_block(cls, chart: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        chart_type = str(chart.get("chartType") or "bar").strip().lower()
        title = str(chart.get("title") or "").strip()
        capped = rows[:_MAX_CHART_POINTS]
        truncated = len(rows) > len(capped)

        if chart_type in _MERMAID_PIE_CHART_TYPES:
            diagram = cls._mermaid_pie(title, capped)

        elif chart_type in _MERMAID_XY_CHART_TYPES:
            diagram = cls._mermaid_xy_chart(chart, capped, chart_type=chart_type)
        else:
            return ""

        if not diagram:
            return ""

        parts = ["```mermaid", diagram, "```"]

        if truncated:
            parts.append("")
            parts.append(
                ChatAssistantContentService.format(
                    "presenter_content",
                    "generic",
                    "chartPointsTruncated",
                    remaining=len(rows) - len(capped),
                )
            )

        return "\n".join(parts).strip()

    @classmethod
    def _mermaid_pie(cls, title: str, rows: list[dict[str, Any]]) -> str:
        lines = ["pie showData"]

        if title:
            lines.append(f'    title "{cls._escape_mermaid_text(title)}"')

        for row in rows:
            label = cls._row_label(row)
            value = cls._row_numeric(row)

            if value is None:
                continue

            lines.append(f'    "{cls._escape_mermaid_text(label)}" : {value}')

        return "\n".join(lines) if len(lines) > 1 else ""

    @classmethod
    def _mermaid_xy_chart(
        cls,
        chart: dict[str, Any],
        rows: list[dict[str, Any]],
        *,
        chart_type: str,
    ) -> str:
        config = chart.get("config") if isinstance(chart.get("config"), dict) else {}
        x_axis = str(config.get("xAxis") or cls._guess_label_key(rows)).strip()
        y_axes = cls._resolve_y_axes(config, rows, x_axis)

        if not y_axes:
            return ""

        primary_y = y_axes[0]
        labels = [cls._format_x_label(row.get(x_axis)) for row in rows]
        values = [cls._row_numeric_for_key(row, primary_y) for row in rows]

        if not any(value is not None for value in values):
            return ""

        numeric_values = [value if value is not None else 0 for value in values]
        y_min, y_max = cls._axis_bounds(numeric_values)
        title = str(chart.get("title") or "").strip()
        series_kind = "line" if chart_type in {"line", "line_chart", "multi_line", "area", "area_chart"} else "bar"

        lines: list[str] = ["xychart-beta"]

        if title:
            lines.append(f'    title "{cls._escape_mermaid_text(title)}"')

        lines.append(f"    x-axis [{', '.join(labels)}]")
        lines.append(f'    y-axis "{cls._escape_mermaid_text(primary_y)}" {y_min} --> {y_max}')
        lines.append(f"    {series_kind} [{', '.join(str(value) for value in numeric_values)}]")

        return "\n".join(lines)

    @classmethod
    def _table_fallback(cls, chart: dict[str, Any], rows: list[dict[str, Any]]) -> str:
        chart_type = str(chart.get("chartType") or "chart").strip()
        capped = rows[:_MAX_CHART_POINTS]
        columns = list(capped[0].keys()) if capped else []
        columns = [key for key in columns if str(key).strip() and not str(key).startswith("_")]

        if not columns:
            return ""

        from app.domain.services.external_actions.presenters.product_analyser_presenter import (
            ExternalActionProductAnalyserPresenter,
        )

        presenter = ExternalActionProductAnalyserPresenter(None)
        table_lines = presenter._markdown_table(
            [(key, str(key).replace("_", " ").strip()) for key in columns],
            [row for row in capped if isinstance(row, dict)],
        )

        if not table_lines:
            return ""

        note = ChatAssistantContentService.format(
            "presenter_content",
            "generic",
            "chartTableFallbackNote",
            chartType=chart_type,
        )
        parts = [note, "", *table_lines]

        if len(rows) > len(capped):
            parts.append("")
            parts.append(
                ChatAssistantContentService.format(
                    "presenter_content",
                    "generic",
                    "chartPointsTruncated",
                    remaining=len(rows) - len(capped),
                )
            )

        return "\n".join(parts).strip()

    @classmethod
    def _collect_charts(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        seen: set[str] = set()

        for key in ("chartPresentation", "presentation"):
            chart = metadata.get(key)

            if isinstance(chart, dict) and chart.get("type") == "chart":
                signature = cls._chart_signature(chart)

                if signature and signature not in seen:
                    collected.append(chart)
                    seen.add(signature)

        return collected

    @staticmethod
    def _chart_signature(chart: dict[str, Any]) -> str:
        title = str(chart.get("title") or "").strip()
        chart_type = str(chart.get("chartType") or "").strip()
        data = chart.get("data")

        row_count = len(data) if isinstance(data, list) else 0

        return f"{chart_type}|{title}|{row_count}"

    @classmethod
    def _chart_rows(cls, presentation: dict[str, Any]) -> list[dict[str, Any]]:
        data = presentation.get("data")

        if isinstance(data, list) and data:
            return [row for row in data if isinstance(row, dict)]

        labels = presentation.get("labels")
        datasets = presentation.get("datasets")

        if not isinstance(labels, list) or not labels:
            return []

        values: list[Any] = []

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
    def _resolve_y_axes(
        cls,
        config: dict[str, Any],
        rows: list[dict[str, Any]],
        x_axis: str,
    ) -> list[str]:
        y_axis = config.get("yAxis")

        if isinstance(y_axis, list):
            keys = [str(key).strip() for key in y_axis if str(key).strip()]

            if keys:
                return keys[:1]

        if isinstance(y_axis, str) and y_axis.strip():
            return [y_axis.strip()]

        sample = rows[0] if rows else {}

        return [
            key
            for key in sample.keys()
            if str(key).strip()
            and str(key) != x_axis
            and not str(key).startswith("_")
            and cls._row_numeric_for_key(sample, str(key)) is not None
        ][:1]

    @classmethod
    def _guess_label_key(cls, rows: list[dict[str, Any]]) -> str:
        sample = rows[0] if rows else {}

        for key in sample.keys():
            value = sample.get(key)

            if isinstance(value, str):
                return str(key)

        return "label"

    @classmethod
    def _row_label(cls, row: dict[str, Any]) -> str:
        for key in ("label", "name", "category", "x", "period"):
            value = row.get(key)

            if value not in (None, ""):
                return str(value).strip()

        for key, value in row.items():
            if str(key).startswith("_"):
                continue

            if isinstance(value, str) and value.strip():
                return value.strip()

        return "—"

    @classmethod
    def _row_numeric(cls, row: dict[str, Any]) -> float | None:
        for key in ("value", "y", "amount", "total", "count"):
            parsed = cls._parse_number(row.get(key))

            if parsed is not None:
                return parsed

        for key, value in row.items():
            if str(key).startswith("_"):
                continue

            if str(key).lower() in {"label", "name", "category", "period", "x"}:
                continue

            parsed = cls._parse_number(value)

            if parsed is not None:
                return parsed

        return None

    @classmethod
    def _row_numeric_for_key(cls, row: dict[str, Any], key: str) -> float | None:
        return cls._parse_number(row.get(key))

    @staticmethod
    def _parse_number(value: Any) -> float | None:
        if value is None or value == "":
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            numeric = float(value)

            return numeric if math.isfinite(numeric) else None

        text = str(value).strip()

        if not text:
            return None

        candidates = [text]

        if "," in text:
            candidates.append(text.replace(".", "").replace(",", "."))

        for candidate in candidates:
            try:
                numeric = float(candidate)

                if math.isfinite(numeric):
                    return numeric
            except (TypeError, ValueError):
                continue

        return None

    @staticmethod
    def _axis_bounds(values: list[float]) -> tuple[int, int]:
        if not values:
            return 0, 1

        minimum = min(values)
        maximum = max(values)

        if minimum == maximum:
            padding = abs(maximum) * 0.1 or 1

            return int(math.floor(minimum - padding)), int(math.ceil(maximum + padding))

        span = maximum - minimum
        padding = span * 0.08 or 1

        return int(math.floor(minimum - padding)), int(math.ceil(maximum + padding))

    @classmethod
    def _format_x_label(cls, value: Any) -> str:
        label = cls._sanitize_axis_label(str(value or "—"))

        return f'"{cls._escape_mermaid_text(label)}"'

    @classmethod
    def _sanitize_axis_label(cls, label: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(label or "").strip())

        return cleaned[:48] or "—"

    @staticmethod
    def _escape_mermaid_text(value: str) -> str:
        return str(value or "").replace('"', "'").replace("\n", " ").strip()

    @classmethod
    def _should_embed_charts(cls, metadata: dict[str, Any]) -> bool:
        from app.domain.services.chat_presentation_text_mode_service import (
            ChatPresentationTextModeService,
        )

        if not ChatPresentationTextModeService.should_embed_in_markdown(metadata):
            return False

        path = str(metadata.get("path") or "").strip()
        entity = cls._resolve_entity(path)
        profile = ChatPresentationProfileService.resolve_profile(path, entity)

        if profile.get("textEmbedChartsInMarkdown") is not True:
            return False

        chart_policy = str(profile.get("chartPolicy") or "auto").strip().lower()

        if chart_policy == "skip":
            return True

        return True

    @classmethod
    def _resolve_entity(cls, path: str) -> str | None:
        entity = str(
            ChatOperationalResponseProfileService.resolve({}, path=path).entity or ""
        ).strip()

        return entity or None
