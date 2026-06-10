"""Detectores genéricos de anomalias em dados tabulares — Playbook 13 P1."""

from __future__ import annotations

from typing import Any


class ChatDataAnomalyDetectionService:
    _NEGATIVE_HINTS = frozenset(
        {
            "available_quantity",
            "current_quantity",
            "quantity",
            "saldo",
            "balance",
            "total",
        }
    )

    @classmethod
    def detect(
        cls,
        *,
        rows: list[dict[str, Any]] | None,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        safe_rows = [row for row in (rows or []) if isinstance(row, dict)]
        meta = metadata if isinstance(metadata, dict) else {}
        anomalies: list[dict[str, Any]] = []

        if not safe_rows:
            anomalies.append(
                {
                    "type": "empty_list",
                    "field": "",
                    "scope": "resultado",
                    "impact": "indefinido",
                }
            )
            return anomalies

        for row_index, row in enumerate(safe_rows[:50]):
            for key, raw in row.items():
                field = str(key or "").strip()

                if raw is None or raw == "":
                    continue

                if not cls._is_numeric(raw):
                    continue

                value = float(raw)

                if value < 0 and cls._is_quantity_field(field):
                    anomalies.append(
                        {
                            "type": "negative_value",
                            "field": field,
                            "scope": f"linha {row_index + 1}",
                            "impact": "pode indicar empenho acima do físico ou inconsistência",
                            "value": value,
                        }
                    )

                if value == 0 and cls._is_quantity_field(field):
                    anomalies.append(
                        {
                            "type": "zero_value",
                            "field": field,
                            "scope": f"linha {row_index + 1}",
                            "impact": "valor zerado pode exigir validação operacional",
                            "value": 0,
                        }
                    )

        if meta.get("paginated") or cls._is_paginated(meta, len(safe_rows)):
            anomalies.append(
                {
                    "type": "truncated_result",
                    "field": "",
                    "scope": "paginação",
                    "impact": "pode haver mais registros fora desta página",
                }
            )

        return cls._dedupe(anomalies)

    @classmethod
    def attention_lines(cls, anomalies: list[dict[str, Any]]) -> list[str]:
        from app.domain.services.chat_humanized_data_response_content_service import (
            ChatHumanizedDataResponseContentService,
        )

        lines: list[str] = []

        for item in anomalies:
            anomaly_type = str(item.get("type") or "").strip()
            template = ChatHumanizedDataResponseContentService.get(
                "anomalies",
                anomaly_type,
                default="",
            )

            if template:
                lines.append(
                    ChatHumanizedDataResponseContentService.format(
                        "anomalies",
                        anomaly_type,
                        field=str(item.get("field") or "—"),
                        scope=str(item.get("scope") or "—"),
                    )
                )
                continue

            field = str(item.get("field") or "").strip()
            scope = str(item.get("scope") or "").strip()
            impact = str(item.get("impact") or "").strip()

            if field and scope:
                lines.append(f"{field} em {scope}: {impact}".strip(": "))

        return lines[:6]

    @classmethod
    def _is_paginated(cls, metadata: dict[str, Any], row_count: int) -> bool:
        for key in ("total", "total_records", "totalRecords"):
            raw = metadata.get(key)

            if raw is None:
                continue

            try:
                total = int(raw)
            except (TypeError, ValueError):
                continue

            if total > row_count:
                return True

        data = metadata.get("data")

        if isinstance(data, dict):
            return cls._is_paginated(data, row_count)

        return False

    @classmethod
    def _is_quantity_field(cls, field: str) -> bool:
        lowered = field.casefold()

        return any(hint in lowered for hint in cls._NEGATIVE_HINTS)

    @classmethod
    def _is_numeric(cls, value: object) -> bool:
        if isinstance(value, bool):
            return False

        if isinstance(value, (int, float)):
            return True

        try:
            float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return False

        return True

    @classmethod
    def _dedupe(cls, anomalies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []

        for item in anomalies:
            key = f"{item.get('type')}|{item.get('field')}|{item.get('scope')}"

            if key in seen:
                continue

            seen.add(key)
            unique.append(item)

        return unique
