"""Decisão session (local) vs refetch para transformação de dados retidos."""

from __future__ import annotations

from typing import Any, Literal

from app.domain.services.chat_tabular_data_aggregation_service import (
    ChatTabularDataAggregationService,
)

ExecutionPath = Literal["session", "refetch", "skip"]


class ChatOperationalSessionDataRefinementService:
    @classmethod
    def dimension_config(cls, route: dict[str, Any], dimension: str) -> dict[str, Any]:
        target = str(dimension or "").strip().lower()

        for entry in route.get("dimensions") or []:
            if not isinstance(entry, dict):
                continue

            if str(entry.get("value") or "").strip().lower() == target:
                return entry

        return {}

    @classmethod
    def resolve_execution_path(
        cls,
        dimension_entry: dict[str, Any],
        rows: list[dict[str, Any]],
    ) -> ExecutionPath:
        strategy = str(dimension_entry.get("strategy") or "refetch").strip().lower()
        refetch_group_by = str(
            dimension_entry.get("refetchGroupBy")
            or dimension_entry.get("value")
            or ""
        ).strip()

        if strategy == "refetch":
            return "refetch" if refetch_group_by else "skip"

        can_local = cls._can_aggregate_locally(dimension_entry, rows)

        if strategy == "local":
            return "session" if can_local else ("refetch" if refetch_group_by else "skip")

        if can_local:
            return "session"

        return "refetch" if refetch_group_by else "skip"

    @classmethod
    def refetch_group_by_value(
        cls,
        dimension_entry: dict[str, Any],
        *,
        dimension: str,
    ) -> str:
        return str(
            dimension_entry.get("refetchGroupBy")
            or dimension_entry.get("value")
            or dimension
        ).strip()

    @classmethod
    def transform_items(
        cls,
        rows: list[dict[str, Any]],
        dimension_entry: dict[str, Any],
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        category_field = str(dimension_entry.get("localCategoryField") or "").strip()
        metric_fields = cls._metric_fields(dimension_entry)
        sort_field = str(dimension_entry.get("localSortField") or metric_fields[0] or "").strip()

        return ChatTabularDataAggregationService.aggregate_ranking(
            rows,
            category_field=category_field,
            metric_fields=metric_fields,
            sort_field=sort_field or None,
            descending=bool(dimension_entry.get("localSortDescending", True)),
            limit=limit,
        )

    @classmethod
    def build_transformed_root(
        cls,
        original_root: dict[str, Any],
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = dict(original_root)
        payload["items"] = items
        payload["total"] = len(items)
        payload["page"] = 1
        payload["page_size"] = len(items)
        payload["total_pages"] = 1

        summary = payload.get("summary")

        if isinstance(summary, dict):
            payload["summary"] = {
                **summary,
                "total_records": len(items),
            }

        return payload

    @classmethod
    def session_refinement_metadata(
        cls,
        *,
        dimension: str,
        dimension_label: str,
        source_row_count: int,
        result_row_count: int,
    ) -> dict[str, Any]:
        return {
            "kind": "local_aggregate",
            "dimension": dimension,
            "dimensionLabel": dimension_label,
            "sourceRowCount": source_row_count,
            "resultRowCount": result_row_count,
            "sampleOnly": True,
        }

    @classmethod
    def _can_aggregate_locally(
        cls,
        dimension_entry: dict[str, Any],
        rows: list[dict[str, Any]],
    ) -> bool:
        category_field = str(dimension_entry.get("localCategoryField") or "").strip()
        metric_fields = cls._metric_fields(dimension_entry)

        return ChatTabularDataAggregationService.can_aggregate(
            rows,
            category_field=category_field,
            metric_fields=metric_fields,
        )

    @classmethod
    def _metric_fields(cls, dimension_entry: dict[str, Any]) -> list[str]:
        raw = dimension_entry.get("localMetricFields") or ["real_consumption_qty"]

        if not isinstance(raw, list):
            return ["real_consumption_qty"]

        fields = [str(item).strip() for item in raw if str(item).strip()]

        return fields or ["real_consumption_qty"]
