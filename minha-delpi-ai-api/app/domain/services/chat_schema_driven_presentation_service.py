"""Apresentação genérica orientada a schema e forma dos dados — Fase 3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.services.chat_api_delpi_response_profile_service import (
    ChatApiDelpiResponseProfileService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)

_RICH_PROFILE_KEYS = frozenset(
    {
        "analyser",
        "stock",
        "tree_hierarchy",
        "table_list",
        "factory_status",
        "production_status",
        "shipping_status",
        "structure_exclusivity",
    }
)

_TABULAR_LIST_KEYS = ("items", "series", "periods", "history", "rows", "entries", "points")


class SchemaDrivenPresenterHost(Protocol):
    def _unwrap_data(self, data: Any) -> Any: ...

    def _fallback_title(self, path: str) -> str | None: ...

    def _presenter_text(self, section: str, key: str, **values: str) -> str: ...

    def _infer_items_title(self, items: list, path: str) -> str: ...

    def _build_items_table(
        self,
        items: list,
        *,
        title: str | None = None,
        path: str = "",
    ) -> dict: ...

    def _kpi_chart(self) -> Any: ...


@dataclass(frozen=True)
class SchemaPresentationBundle:
    table: dict[str, Any] | None = None
    text: dict[str, Any] | None = None
    chart: dict[str, Any] | None = None
    kpi: dict[str, Any] | None = None


class ChatSchemaDrivenPresentationService:
    @classmethod
    def should_apply(cls, *, path: str, entity: str | None = None) -> bool:
        profile_key = ChatPresentationProfileService.resolve_profile_key(path, entity)

        if profile_key in _RICH_PROFILE_KEYS:
            return False

        if ChatApiDelpiResponseProfileService.is_kpi_entity(entity):
            return True

        return profile_key in {"generic", "sql", "system"}

    @classmethod
    def build_bundle(
        cls,
        host: SchemaDrivenPresenterHost,
        data: Any,
        *,
        path: str = "",
        entity: str | None = None,
    ) -> SchemaPresentationBundle:
        if not cls.should_apply(path=path, entity=entity):
            return SchemaPresentationBundle()

        root = host._unwrap_data(data)

        if root is None:
            return SchemaPresentationBundle()

        kpi = cls.build_kpi(host, root, path=path, entity=entity)
        rows = cls.extract_tabular_rows(root)
        table = cls.build_table(host, rows, path=path) if rows else None
        chart = cls.build_chart(host, root, rows=rows, path=path, entity=entity)
        text = cls.build_text(host, root, rows=rows, path=path, entity=entity)

        return SchemaPresentationBundle(
            table=table,
            text=text,
            chart=chart,
            kpi=kpi,
        )

    @classmethod
    def build_primary(
        cls,
        host: SchemaDrivenPresenterHost,
        data: Any,
        *,
        path: str = "",
        entity: str | None = None,
    ) -> dict[str, Any] | None:
        bundle = cls.build_bundle(host, data, path=path, entity=entity)

        if isinstance(bundle.kpi, dict):
            return bundle.kpi

        return bundle.table

    @classmethod
    def build_table(
        cls,
        host: SchemaDrivenPresenterHost,
        rows: list[dict[str, Any]],
        *,
        path: str,
    ) -> dict[str, Any] | None:
        if not rows:
            return None

        title = str(host._infer_items_title(rows, path) or "").strip()

        if not title:
            title = cls._text("tableTitleFallback")

        return host._build_items_table(rows, title=title, path=path)

    @classmethod
    def build_kpi(
        cls,
        host: SchemaDrivenPresenterHost,
        root: dict[str, Any],
        *,
        path: str,
        entity: str | None,
    ) -> dict[str, Any] | None:
        kpi_chart = host._kpi_chart()

        if not kpi_chart.looks_like_kpi_response(root, path, entity=entity):
            return None

        presentation = kpi_chart.build_kpi_chart(root, path)

        if isinstance(presentation, dict) and presentation.get("type") == "kpi":
            return presentation

        return None

    @classmethod
    def build_chart(
        cls,
        host: SchemaDrivenPresenterHost,
        root: dict[str, Any],
        *,
        rows: list[dict[str, Any]] | None,
        path: str,
        entity: str | None,
    ) -> dict[str, Any] | None:
        kpi_chart = host._kpi_chart()
        safe_rows = rows or cls.extract_tabular_rows(root)

        if safe_rows:
            chart = kpi_chart.try_chart_from_rows(safe_rows, force=False, path=path)

            if isinstance(chart, dict):
                return chart

        if isinstance(root, dict) and kpi_chart.looks_like_kpi_response(root, path, entity=entity):
            chart = kpi_chart.build_kpi_chart(root, path)

            if isinstance(chart, dict) and chart.get("type") == "chart":
                return chart

        return None

    @classmethod
    def build_text(
        cls,
        host: SchemaDrivenPresenterHost,
        root: dict[str, Any],
        *,
        rows: list[dict[str, Any]] | None = None,
        path: str,
        entity: str | None,
    ) -> dict[str, Any] | None:
        title = (
            str(host._fallback_title(path) or "").strip()
            or cls._text("tableTitleFallback")
        )
        safe_rows = rows if rows is not None else cls.extract_tabular_rows(root)
        shape = ChatPresentationDataShapeAnalyzer.analyze(rows=safe_rows)
        lead = ""

        if shape.get("hasDate") and safe_rows:
            lead = cls._text(
                "timeSeriesLead",
                title=title,
                count=str(len(safe_rows)),
            )
        elif len(safe_rows) > 1:
            lead = cls._text(
                "listSummary",
                title=title,
                count=str(len(safe_rows)),
            )
        elif len(safe_rows) == 1:
            lead = cls._text(
                "singleRecordLead",
                title=title,
                columns=str(shape.get("columns") or 0),
            )
        elif cls.build_kpi(host, root, path=path, entity=entity) is not None:
            metric_count = cls._count_scalar_metrics(root)
            lead = cls._text(
                "kpiLead",
                title=title,
                metricCount=str(metric_count),
            )
        else:
            return None

        markdown = f"### {title}\n\n{lead}".strip()

        return {
            "type": "markdown",
            "title": title,
            "markdown": markdown,
        }

    @classmethod
    def extract_tabular_rows(cls, root: Any) -> list[dict[str, Any]]:
        if isinstance(root, list):
            return [row for row in root if isinstance(row, dict)]

        if not isinstance(root, dict):
            return []

        for key in _TABULAR_LIST_KEYS:
            candidate = root.get(key)

            if isinstance(candidate, list) and candidate and isinstance(candidate[0], dict):
                return [row for row in candidate if isinstance(row, dict)]

        nested_data = root.get("data")

        if isinstance(nested_data, dict):
            nested_rows = cls.extract_tabular_rows(nested_data)

            if nested_rows:
                return nested_rows

        if isinstance(nested_data, list):
            return [row for row in nested_data if isinstance(row, dict)]

        return []

    @classmethod
    def _count_scalar_metrics(cls, root: dict[str, Any]) -> int:
        ignored = {"unit", "unidade", "meta", "message", "success", "total"}

        return sum(
            1
            for key, value in root.items()
            if key not in ignored and isinstance(value, (int, float)) and not isinstance(value, bool)
        )

    @classmethod
    def _text(cls, key: str, **values: str) -> str:
        template = ChatAssistantContentService.get(
            "presenter_content",
            "schemaDriven",
            key,
            default="",
        )

        if not template:
            return ""

        try:
            return template.format(**values)
        except KeyError:
            return template
