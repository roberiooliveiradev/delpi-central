"""Limites e ajustes de dados para gráficos — Playbook 09 §25."""

from __future__ import annotations

from typing import Any


class ChatPresentationChartPolicyService:
    MAX_TEMPORAL_POINTS = 24
    MAX_RANKING_ITEMS = 10
    MAX_DONUT_SLICES = 6
    MAX_BAR_ITEMS = 12
    OTHERS_LABEL = "Outros"

    @classmethod
    def apply(
        cls,
        rows: list[dict[str, Any]] | None,
        chart_type: str | None,
        *,
        label_key: str | None = None,
        value_key: str | None = None,
    ) -> list[dict[str, Any]]:
        safe_rows = [dict(row) for row in (rows or []) if isinstance(row, dict)]
        token = str(chart_type or "bar").strip().lower()

        if not safe_rows:
            return []

        resolved_label, resolved_value = cls._resolve_keys(safe_rows, label_key, value_key)

        if token in {"donut", "pie"}:
            return cls._limit_participation(
                safe_rows,
                label_key=resolved_label,
                value_key=resolved_value,
            )

        if token == "horizontal_bar":
            return cls._limit_ranking(
                safe_rows,
                label_key=resolved_label,
                value_key=resolved_value,
            )

        if token in {"line", "multi_line", "area"}:
            return safe_rows[: cls.MAX_TEMPORAL_POINTS]

        return safe_rows[: cls.MAX_BAR_ITEMS]

    @classmethod
    def fallback_notice(cls, chart_type: str | None, original_count: int, capped_count: int) -> str | None:
        if original_count <= capped_count:
            return None

        token = str(chart_type or "").strip().lower()

        if token in {"donut", "pie"}:
            return (
                "Há muitas categorias para rosca/pizza; agrupei as menores em "
                f"«{cls.OTHERS_LABEL}» para melhorar a leitura."
            )

        if token == "horizontal_bar":
            return (
                f"Há muitas categorias ({original_count}); mostrei as "
                f"{capped_count} principais em barra horizontal."
            )

        if token in {"line", "multi_line", "area"}:
            return (
                f"A série tem {original_count} pontos; exibi os "
                f"{capped_count} mais recentes no gráfico."
            )

        return None

    @classmethod
    def _resolve_keys(
        cls,
        rows: list[dict[str, Any]],
        label_key: str | None,
        value_key: str | None,
    ) -> tuple[str, str]:
        first = rows[0]
        resolved_label = label_key or next(
            (key for key, value in first.items() if isinstance(value, str)),
            "name",
        )
        resolved_value = value_key or next(
            (
                key
                for key, value in first.items()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            ),
            "value",
        )

        return resolved_label, resolved_value

    @classmethod
    def _limit_ranking(
        cls,
        rows: list[dict[str, Any]],
        *,
        label_key: str,
        value_key: str,
    ) -> list[dict[str, Any]]:
        ordered = sorted(
            rows,
            key=lambda row: float(row.get(value_key) or 0)
            if isinstance(row.get(value_key), (int, float))
            else 0,
            reverse=True,
        )

        return ordered[: cls.MAX_RANKING_ITEMS]

    @classmethod
    def _limit_participation(
        cls,
        rows: list[dict[str, Any]],
        *,
        label_key: str,
        value_key: str,
    ) -> list[dict[str, Any]]:
        ordered = sorted(
            rows,
            key=lambda row: float(row.get(value_key) or 0)
            if isinstance(row.get(value_key), (int, float))
            else 0,
            reverse=True,
        )

        if len(ordered) <= cls.MAX_DONUT_SLICES:
            return ordered

        keep = ordered[: cls.MAX_DONUT_SLICES - 1]
        remainder = ordered[cls.MAX_DONUT_SLICES - 1 :]
        others_total = sum(
            float(row.get(value_key) or 0)
            for row in remainder
            if isinstance(row.get(value_key), (int, float))
        )

        if others_total > 0:
            keep.append({label_key: cls.OTHERS_LABEL, value_key: others_total})

        return keep
