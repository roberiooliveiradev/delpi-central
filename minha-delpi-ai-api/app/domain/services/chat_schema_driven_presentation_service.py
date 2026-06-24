"""Apresentação genérica orientada a schema e forma dos dados — Playbook 22 Fase B."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)

_CHART_VIEW_TOKENS = frozenset(
    {
        "chart",
        "line_chart",
        "bar_chart",
        "horizontal_bar",
        "donut",
    }
)

_TABULAR_LIST_KEYS = ("items", "series", "periods", "history", "rows", "entries", "points")
_TREE_CHILD_KEYS = ("children", "components", "items", "nodes")


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
    tree: dict[str, Any] | None = None


class ChatSchemaDrivenPresentationService:
    @classmethod
    def should_apply(cls, *, path: str, entity: str | None = None) -> bool:
        return ChatPresentationProfileService.uses_schema_first_presentation(path, entity)

    @classmethod
    def build_from_openapi_schema(
        cls,
        host: SchemaDrivenPresenterHost,
        data: Any,
        *,
        path: str = "",
        entity: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> SchemaPresentationBundle:
        del response_schema  # labels aplicados no host antes da chamada

        return cls.build_bundle(host, data, path=path, entity=entity)

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

        rows = cls.extract_tabular_rows(root)
        kpi = cls.build_kpi(host, root, path=path, entity=entity)
        table = cls.build_table(host, rows, path=path) if rows else None
        force_chart = cls._profile_allows_chart(path=path, entity=entity)
        chart = cls.build_chart(
            host,
            root,
            rows=rows,
            path=path,
            entity=entity,
            force=force_chart,
        )
        tree = cls.build_tree(host, root, path=path)
        text = cls.build_text(host, root, rows=rows, path=path, entity=entity)

        return SchemaPresentationBundle(
            table=table,
            text=text,
            chart=chart,
            kpi=kpi,
            tree=tree,
        )

    @classmethod
    def build_primary(
        cls,
        host: SchemaDrivenPresenterHost,
        data: Any,
        *,
        path: str = "",
        entity: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        bundle = cls.build_from_openapi_schema(
            host,
            data,
            path=path,
            entity=entity,
            response_schema=response_schema,
        )

        return cls.resolve_primary_from_bundle(bundle, path=path, entity=entity)

    @classmethod
    def resolve_primary_from_bundle(
        cls,
        bundle: SchemaPresentationBundle,
        *,
        path: str,
        entity: str | None,
    ) -> dict[str, Any] | None:
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        view_order = [
            str(view).strip().lower()
            for view in (profile.get("viewOrder") or [])
            if str(view).strip()
        ]

        for view in view_order:
            if view == "text" and isinstance(bundle.text, dict):
                return bundle.text

            if view == "kpi" and isinstance(bundle.kpi, dict):
                return bundle.kpi

            if view in _CHART_VIEW_TOKENS and isinstance(bundle.chart, dict):
                return bundle.chart

            if view == "table" and isinstance(bundle.table, dict):
                return bundle.table

            if view == "tree" and isinstance(bundle.tree, dict):
                return bundle.tree

        if isinstance(bundle.kpi, dict):
            return bundle.kpi

        if isinstance(bundle.chart, dict):
            return bundle.chart

        if isinstance(bundle.table, dict):
            return bundle.table

        if isinstance(bundle.tree, dict):
            return bundle.tree

        if isinstance(bundle.text, dict):
            return bundle.text

        return None

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
        force: bool = False,
    ) -> dict[str, Any] | None:
        kpi_chart = host._kpi_chart()
        safe_rows = rows or cls.extract_tabular_rows(root)

        if safe_rows:
            chart = kpi_chart.try_chart_from_rows(safe_rows, force=force, path=path)

            if isinstance(chart, dict):
                return chart

        if isinstance(root, dict) and kpi_chart.looks_like_kpi_response(root, path, entity=entity):
            chart = kpi_chart.build_kpi_chart(root, path)

            if isinstance(chart, dict) and chart.get("type") == "chart":
                return chart

        return None

    @classmethod
    def build_tree(
        cls,
        host: SchemaDrivenPresenterHost,
        root: Any,
        *,
        path: str,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_product_structure_presentation_service import (
            ChatProductStructurePresentationService,
        )

        if not isinstance(root, dict):
            return None

        structure_tree = ChatProductStructurePresentationService.build_tree_presentation(
            root,
            path=path,
        )

        if isinstance(structure_tree, dict) and structure_tree.get("type") == "tree":
            return structure_tree

        if isinstance(root.get("root"), dict):
            generic = cls._build_tree_from_node(
                root["root"],
                title=str(host._fallback_title(path) or cls._text("tableTitleFallback")),
                child_key=cls._detect_child_key(root["root"]),
            )

            if generic:
                return generic

        child_key = cls._detect_child_key(root)

        if child_key:
            return cls._build_tree_from_node(
                root,
                title=str(host._fallback_title(path) or cls._text("tableTitleFallback")),
                child_key=child_key,
            )

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
            return cls.build_raw_payload_markdown(host, root, path=path)

        has_panels = bool(safe_rows) or cls.build_kpi(host, root, path=path, entity=entity) is not None

        if not has_panels:
            chart = cls.build_chart(
                host,
                root,
                rows=safe_rows,
                path=path,
                entity=entity,
            )
            has_panels = chart is not None

        if has_panels:
            hint = cls._text("panelsBelowHint")
            lead = f"{lead}\n\n{hint}".strip()

        markdown = f"### {title}\n\n<!-- section:scope -->\n\n{lead}".strip()

        return {
            "type": "markdown",
            "title": title,
            "markdown": markdown,
        }

    @classmethod
    def build_raw_payload_markdown(
        cls,
        host: SchemaDrivenPresenterHost,
        root: Any,
        *,
        path: str,
    ) -> dict[str, Any] | None:
        if root is None:
            return None

        title = (
            str(host._fallback_title(path) or "").strip()
            or cls._text("tableTitleFallback")
        )

        if isinstance(root, dict) and not root:
            lead = cls._text("rawPayloadEmpty", title=title)
            markdown = f"### {title}\n\n{lead}".strip()

            return {
                "type": "markdown",
                "title": title,
                "markdown": markdown,
            }

        payload = json.dumps(root, ensure_ascii=False, indent=2, default=str)
        lead = cls._text("rawPayloadLead", title=title)
        markdown = f"### {title}\n\n{lead}\n\n```json\n{payload}\n```".strip()

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
    def _profile_allows_chart(cls, *, path: str, entity: str | None) -> bool:
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        flags = {str(flag).strip().lower() for flag in (profile.get("flags") or []) if str(flag).strip()}
        view_order = {
            str(view).strip().lower()
            for view in (profile.get("viewOrder") or [])
            if str(view).strip()
        }

        return bool(flags & {"chart", "kpi"}) or bool(view_order & _CHART_VIEW_TOKENS)

    @classmethod
    def _detect_child_key(cls, node: dict[str, Any]) -> str | None:
        for key in _TREE_CHILD_KEYS:
            candidate = node.get(key)

            if isinstance(candidate, list) and candidate:
                return key

        return None

    @classmethod
    def _build_tree_from_node(
        cls,
        node: dict[str, Any],
        *,
        title: str,
        child_key: str | None,
    ) -> dict[str, Any] | None:
        if not isinstance(node, dict):
            return None

        key = child_key or cls._detect_child_key(node)

        if not key:
            return None

        children_raw = node.get(key)

        if not isinstance(children_raw, list) or not children_raw:
            return None

        children = [
            cls._serialize_tree_child(item, child_key=cls._detect_child_key(item) if isinstance(item, dict) else None)
            for item in children_raw
            if isinstance(item, dict)
        ]

        if not children:
            return None

        return {
            "type": "tree",
            "title": title,
            "root": cls._serialize_tree_child(node, child_key=key, children=children),
        }

    @classmethod
    def _serialize_tree_child(
        cls,
        node: dict[str, Any],
        *,
        child_key: str | None,
        children: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        label = (
            str(node.get("description") or node.get("label") or node.get("name") or "").strip()
            or str(node.get("code") or node.get("id") or node.get("key") or "—")
        )
        serialized: dict[str, Any] = {
            "id": str(node.get("id") or node.get("code") or node.get("key") or label),
            "label": label,
        }

        if children:
            serialized["children"] = children
            return serialized

        nested_key = child_key or cls._detect_child_key(node)

        if nested_key:
            nested = node.get(nested_key)

            if isinstance(nested, list) and nested:
                serialized["children"] = [
                    cls._serialize_tree_child(item, child_key=cls._detect_child_key(item))
                    for item in nested
                    if isinstance(item, dict)
                ]

        return serialized

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
