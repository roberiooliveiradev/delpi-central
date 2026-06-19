"""Tabelas estruturadas a partir de anotações PDF com bbox — chat base."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)


class ChatPdfAnnotationTableService:
    @classmethod
    def build_tables(
        cls,
        annotations: list[dict[str, Any]] | None,
        *,
        max_tables: int | None = None,
        max_rows: int | None = None,
    ) -> list[dict[str, Any]]:
        if not annotations:
            return []

        limit_tables = max_tables or ChatDocumentVisionContentService.tables_max_tables()
        limit_rows = max_rows or ChatDocumentVisionContentService.tables_max_rows()
        tolerance = ChatDocumentVisionContentService.pdf_annotation_row_cluster_tolerance_pt()

        by_page: dict[int, list[dict[str, Any]]] = {}

        for item in annotations:
            if not isinstance(item, dict):
                continue

            content = str(item.get("content") or "").strip()

            if not content:
                continue

            page = int(item.get("page") or 1)
            bbox = item.get("bbox")

            if not isinstance(bbox, list) or len(bbox) < 4:
                continue

            by_page.setdefault(page, []).append(
                {
                    "content": content,
                    "bbox": bbox,
                    "x": float(bbox[0]),
                    "y": float(bbox[1]),
                    "y_center": (float(bbox[1]) + float(bbox[3])) / 2.0,
                }
            )

        tables: list[dict[str, Any]] = []

        for page in sorted(by_page):
            rows = cls._cluster_rows(by_page[page], tolerance=tolerance)

            if len(rows) < 2:
                continue

            table_rows: list[dict[str, Any]] = []

            for row in rows[:limit_rows]:
                cells = sorted(row, key=lambda cell: cell["x"])
                table_rows.append(
                    {
                        "cells": [cell["content"] for cell in cells],
                        "bbox": cls._row_bbox(cells),
                        "y": round(cells[0]["y_center"], 2),
                    }
                )

            if len(table_rows) < 2:
                continue

            tables.append(
                {
                    "page": page,
                    "source": "pdf_annotations",
                    "rowCount": len(table_rows),
                    "rows": table_rows,
                }
            )

            if len(tables) >= limit_tables:
                break

        return tables

    @classmethod
    def table_text(cls, tables: list[dict[str, Any]]) -> str:
        lines: list[str] = []

        for table in tables:
            if not isinstance(table, dict):
                continue

            for row in table.get("rows") or []:
                if not isinstance(row, dict):
                    continue

                cells = row.get("cells")

                if isinstance(cells, list) and cells:
                    lines.append(" | ".join(str(cell) for cell in cells))

        return "\n".join(lines).strip()

    @classmethod
    def _cluster_rows(
        cls,
        cells: list[dict[str, Any]],
        *,
        tolerance: float,
    ) -> list[list[dict[str, Any]]]:
        sorted_cells = sorted(cells, key=lambda item: item["y_center"])
        clusters: list[list[dict[str, Any]]] = []

        for cell in sorted_cells:
            placed = False

            for cluster in clusters:
                anchor = cluster[0]["y_center"]

                if abs(cell["y_center"] - anchor) <= tolerance:
                    cluster.append(cell)
                    placed = True
                    break

            if not placed:
                clusters.append([cell])

        clusters.sort(key=lambda cluster: cluster[0]["y_center"])

        return [cluster for cluster in clusters if len(cluster) >= 1]

    @classmethod
    def _row_bbox(cls, cells: list[dict[str, Any]]) -> list[float]:
        x0 = min(float(cell["bbox"][0]) for cell in cells)
        y0 = min(float(cell["bbox"][1]) for cell in cells)
        x1 = max(float(cell["bbox"][2]) for cell in cells)
        y1 = max(float(cell["bbox"][3]) for cell in cells)

        return [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)]
