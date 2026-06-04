"""Insight curto para visualizações — Playbook 09 §16."""

from __future__ import annotations

from typing import Any


class ChatPresentationInsightService:
    @classmethod
    def build(
        cls,
        *,
        selected: str | None,
        rows: list[dict[str, Any]] | None,
        data_shape: dict[str, Any] | None = None,
        reason: str | None = None,
    ) -> str:
        token = str(selected or "").strip().lower()
        safe_rows = [row for row in (rows or []) if isinstance(row, dict)]
        shape = data_shape or {}

        tree_nodes = shape.get("treeNodes")

        if token == "tree":
            if tree_nodes is False or tree_nodes == 0:
                return ""

            return (
                "A árvore mostra a hierarquia de composição ou relacionamento entre itens."
            )

        if not safe_rows:
            if shape.get("hasNarrative"):
                return ""

            return "Não há dados suficientes para gerar esta visualização."

        if token in {"line_chart", "area_chart"}:
            return cls._temporal_insight(safe_rows, shape)

        if token in {"horizontal_bar", "bar_chart"}:
            return cls._ranking_insight(safe_rows, shape)

        if token in {"donut", "pie"}:
            return cls._participation_insight(safe_rows, shape)

        if token == "kpi":
            return "O indicador resume o valor principal encontrado para o filtro informado."

        if token == "table":
            count = int(shape.get("rows") or len(safe_rows))

            return (
                f"A tabela lista os principais registros encontrados "
                f"({count} linha{'s' if count != 1 else ''})."
            )

        if token in {"grouped_bar", "combo_chart", "stacked_bar"}:
            return "O gráfico compara séries lado a lado para facilitar a leitura de metas e valores."

        fallback = str(reason or "").strip()

        if fallback:
            return fallback[0].upper() + fallback[1:] + "."

        return "Use os controles para alternar entre tabela, gráfico ou exportar os dados."

    @classmethod
    def _temporal_insight(
        cls,
        rows: list[dict[str, Any]],
        shape: dict[str, Any],
    ) -> str:
        label_key = shape.get("labelKey")
        numeric_keys = shape.get("numericKeys") or []
        value_key = numeric_keys[0] if numeric_keys else None

        if not label_key or not value_key:
            return "A série temporal destaca a evolução dos valores ao longo do período."

        values = [
            float(row.get(value_key))
            for row in rows
            if isinstance(row.get(value_key), (int, float))
        ]

        if len(values) < 2:
            return "A série temporal destaca a evolução dos valores ao longo do período."

        peak_index = max(range(len(values)), key=lambda index: values[index])
        low_index = min(range(len(values)), key=lambda index: values[index])
        peak_label = str(rows[peak_index].get(label_key) or "").strip() or "um ponto"
        low_label = str(rows[low_index].get(label_key) or "").strip() or "outro ponto"

        if peak_index == low_index:
            return f"O maior valor ocorreu em {peak_label}."

        return (
            f"O maior valor ocorreu em {peak_label}; "
            f"o menor, em {low_label}."
        )

    @classmethod
    def _ranking_insight(
        cls,
        rows: list[dict[str, Any]],
        shape: dict[str, Any],
    ) -> str:
        label_key = shape.get("labelKey")
        numeric_keys = shape.get("numericKeys") or []
        value_key = numeric_keys[0] if numeric_keys else None

        if not label_key or not value_key or not rows:
            return "O ranking ordena os itens pelo valor para destacar os maiores."

        leader = max(
            rows,
            key=lambda row: float(row.get(value_key) or 0)
            if isinstance(row.get(value_key), (int, float))
            else 0,
        )
        leader_label = str(leader.get(label_key) or "").strip() or "o primeiro item"

        if len(rows) >= 3:
            return (
                f"Os destaques concentram-se em {leader_label} "
                f"e nos demais itens do topo do ranking."
            )

        return f"{leader_label} lidera o ranking pelos valores apresentados."

    @classmethod
    def _participation_insight(
        cls,
        rows: list[dict[str, Any]],
        shape: dict[str, Any],
    ) -> str:
        label_key = shape.get("labelKey")
        numeric_keys = shape.get("numericKeys") or []
        value_key = numeric_keys[0] if numeric_keys else None

        if not label_key or not value_key:
            return "A distribuição mostra a participação relativa de cada categoria."

        leader = max(
            rows,
            key=lambda row: float(row.get(value_key) or 0)
            if isinstance(row.get(value_key), (int, float))
            else 0,
        )
        leader_label = str(leader.get(label_key) or "").strip() or "uma categoria"

        return f"A maior fatia da distribuição está em {leader_label}."
