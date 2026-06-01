"""Escolha automática do formato de apresentação — Playbook 09 Fase 1."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_chart_type_selection_service import (
    ChatChartTypeSelectionService,
)
from app.domain.services.chat_presentation_chart_policy_service import (
    ChatPresentationChartPolicyService,
)
from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)
from app.domain.services.chat_presentation_insight_service import (
    ChatPresentationInsightService,
)

_SELECTED_TO_CHART_TYPE = {
    "line_chart": "line",
    "area_chart": "area",
    "bar_chart": "bar",
    "horizontal_bar": "horizontal_bar",
    "donut": "donut",
    "grouped_bar": "grouped_bar",
    "stacked_bar": "stacked_bar",
    "combo_chart": "combo",
    "histogram": "histogram",
    "heatmap": "heatmap",
    "gauge": "gauge",
    "scatter": "scatter",
    "chart": "bar",
}

_CHART_TYPE_TO_SELECTED = {
    "line": "line_chart",
    "multi_line": "line_chart",
    "area": "area_chart",
    "bar": "bar_chart",
    "horizontal_bar": "horizontal_bar",
    "donut": "donut",
    "pie": "donut",
    "grouped_bar": "grouped_bar",
    "stacked_bar": "stacked_bar",
    "combo": "combo_chart",
    "histogram": "histogram",
    "heatmap": "heatmap",
    "gauge": "gauge",
    "scatter": "scatter",
}

_USER_FORMAT_ALIASES = {
    "text": "text",
    "texto": "text",
    "table": "table",
    "tabela": "table",
    "chart": "chart",
    "grafico": "chart",
    "gráfico": "chart",
    "kpi": "kpi",
    "tree": "tree",
    "arvore": "tree",
    "árvore": "tree",
    "checklist": "checklist",
    "canvas": "canvas",
    "lousa": "canvas",
    "dashboard": "dashboard",
    "line": "line_chart",
    "line_chart": "line_chart",
    "bar_chart": "bar_chart",
    "horizontal_bar": "horizontal_bar",
    "donut": "donut",
}


class ChatPresentationDecisionService:
    @classmethod
    def decide(
        cls,
        *,
        intent: str | None = None,
        rows: list[dict[str, Any]] | None = None,
        user_message: str | None = None,
        user_preference: str | None = None,
        primary_presentation: dict[str, Any] | None = None,
        table_presentation: dict[str, Any] | None = None,
        chart_presentation: dict[str, Any] | None = None,
        tree_presentation: dict[str, Any] | None = None,
        dashboard_presentation: dict[str, Any] | None = None,
        text_presentation: dict[str, Any] | None = None,
        available_formats: list[str] | None = None,
    ) -> dict[str, Any]:
        message = re.sub(r"\s+", " ", str(user_message or "").strip().lower())
        preferred = cls._normalize_user_preference(user_preference, message)

        if preferred:
            return cls._decision_for_preference(
                preferred,
                rows=rows,
                user_message=message,
                available_formats=available_formats,
                intent=intent,
            )

        if cls._looks_like_checklist(message):
            return cls._build(
                selected="checklist",
                fallback="text",
                reason="plano de ação ou pendências",
                available_views=["checklist", "text", "canvas"],
                rows=rows,
                intent=intent,
            )

        if cls._looks_like_canvas(message):
            return cls._build(
                selected="canvas",
                fallback="text",
                reason="documento ou relatório longo",
                available_views=["canvas", "text"],
                rows=rows,
                intent=intent,
            )

        if tree_presentation or (
            primary_presentation and primary_presentation.get("type") == "tree"
        ):
            return cls._build(
                selected="tree",
                fallback="table",
                reason="hierarquia ou estrutura de produto",
                available_views=cls._merge_views(
                    available_formats,
                    ["tree", "table", "text"],
                ),
                rows=rows,
                intent=intent,
            )

        if dashboard_presentation or (
            primary_presentation and primary_presentation.get("type") == "dashboard"
        ):
            return cls._build(
                selected="dashboard",
                fallback="table",
                reason="visão consolidada com múltiplos indicadores",
                available_views=cls._merge_views(
                    available_formats,
                    ["dashboard", "table", "chart", "kpi"],
                ),
                rows=rows,
                intent=intent,
            )

        if primary_presentation and primary_presentation.get("type") == "kpi":
            return cls._build(
                selected="kpi",
                fallback="table",
                reason="indicador único",
                available_views=["kpi", "table", "chart", "text"],
                rows=rows,
                intent=intent,
            )

        table_rows = rows or cls._rows_from_presentation(
            table_presentation or (
                primary_presentation
                if primary_presentation and primary_presentation.get("type") == "table"
                else None
            )
        )

        shape = ChatPresentationDataShapeAnalyzer.analyze(rows=table_rows)

        if shape["rows"] == 0:
            return cls._build(
                selected="text",
                fallback="text",
                reason="sem dados tabulares para visualização",
                available_views=["text"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if chart_presentation or (
            primary_presentation and primary_presentation.get("type") == "chart"
        ):
            chart_type = cls._resolve_chart_type(
                table_rows=table_rows,
                shape=shape,
                user_message=message,
                fallback_chart=str(
                    (chart_presentation or primary_presentation or {}).get("chartType") or "bar"
                ),
            )
            selected = _CHART_TYPE_TO_SELECTED.get(chart_type, "chart")

            return cls._build(
                selected=selected,
                fallback="table",
                reason=cls._chart_reason(chart_type, shape),
                available_views=cls._merge_views(
                    available_formats,
                    [selected, "table", "chart", "text"],
                ),
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if shape["rows"] == 1 and shape["hasNumeric"] and len(shape.get("numericKeys") or []) == 1:
            return cls._build(
                selected="kpi",
                fallback="table",
                reason="um único valor numérico principal",
                available_views=["kpi", "table", "chart"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if shape["hasHierarchy"]:
            return cls._build(
                selected="tree",
                fallback="table",
                reason="estrutura hierárquica detectada",
                available_views=["tree", "table"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        numeric_keys = list(shape.get("numericKeys") or [])

        if len(numeric_keys) >= 2 and table_rows:
            lowered = {key.lower() for key in numeric_keys}
            has_target = any(
                any(token in key for token in ("meta", "target", "goal", "objetivo"))
                for key in lowered
            )
            has_actual = any(
                any(token in key for token in ("realizado", "actual", "atual", "valor"))
                for key in lowered
            )

            if has_target and has_actual or any(
                token in message for token in ("versus", " vs ", "meta", "compar")
            ):
                label_key = shape.get("labelKey") or "label"
                chart_type = ChatChartTypeSelectionService.resolve(
                    rows=table_rows[:24],
                    label_key=str(label_key),
                    numeric_keys=numeric_keys[:3],
                    user_message=message or None,
                )
                selected = _CHART_TYPE_TO_SELECTED.get(chart_type, "grouped_bar")

                return cls._build(
                    selected=selected,
                    fallback="table",
                    reason="comparação entre meta e realizado",
                    available_views=cls._merge_views(
                        available_formats,
                        [selected, "kpi", "table", "chart"],
                    ),
                    rows=table_rows,
                    intent=intent,
                    data_shape=shape,
                )

        if shape["hasDate"] and shape["hasNumeric"] and table_rows:
            label_key = shape.get("labelKey") or "label"
            chart_type = ChatChartTypeSelectionService.resolve(
                rows=table_rows[:24],
                label_key=str(label_key),
                numeric_keys=numeric_keys or ["value"],
                user_message=message or None,
            )
            selected = _CHART_TYPE_TO_SELECTED.get(chart_type, "line_chart")

            return cls._build(
                selected=selected,
                fallback="table",
                reason="dados temporais com valor numérico",
                available_views=cls._merge_views(
                    available_formats,
                    [selected, "table", "chart"],
                ),
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if (
            shape["hasNumeric"]
            and shape["categoryCardinality"] > 6
            and table_rows
        ):
            return cls._build(
                selected="horizontal_bar",
                fallback="table",
                reason="muitas categorias — ranking em barra horizontal",
                available_views=["horizontal_bar", "table", "chart"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if (
            shape["hasNumeric"]
            and 3 <= shape["categoryCardinality"] <= 6
            and table_rows
        ):
            label_key = shape.get("labelKey") or "label"
            numeric_keys = list(shape.get("numericKeys") or ["value"])
            chart_type = ChatChartTypeSelectionService.resolve(
                rows=table_rows[:12],
                label_key=str(label_key),
                numeric_keys=numeric_keys,
                user_message=message or None,
            )
            selected = _CHART_TYPE_TO_SELECTED.get(chart_type, "donut")

            return cls._build(
                selected=selected,
                fallback="table",
                reason="participação ou distribuição por categoria",
                available_views=[selected, "table", "chart"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        if text_presentation and not table_rows:
            return cls._build(
                selected="text",
                fallback="text",
                reason="resposta explicativa sem dados tabulares",
                available_views=["text"],
                rows=table_rows,
                intent=intent,
                data_shape=shape,
            )

        return cls._build(
            selected="table",
            fallback="text",
            reason="lista detalhada ou comparação auditável",
            available_views=cls._merge_views(
                available_formats,
                ["table", "chart", "text"],
            ),
            rows=table_rows,
            intent=intent,
            data_shape=shape,
        )

    @classmethod
    def enrich_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        intent: str | None = None,
        user_message: str | None = None,
        user_preference: str | None = None,
        axis_user_message: str | None = None,
    ) -> dict[str, Any]:
        decision = cls.decide(
            intent=intent,
            rows=cls._rows_from_presentation(metadata.get("tablePresentation"))
            or cls._rows_from_presentation(metadata.get("presentation")),
            user_message=user_message,
            user_preference=user_preference or metadata.get("preferredFormat"),
            primary_presentation=metadata.get("presentation"),
            table_presentation=metadata.get("tablePresentation"),
            chart_presentation=metadata.get("chartPresentation"),
            tree_presentation=metadata.get("treePresentation"),
            dashboard_presentation=(
                metadata.get("presentation")
                if isinstance(metadata.get("presentation"), dict)
                and metadata["presentation"].get("type") == "dashboard"
                else None
            ),
            text_presentation=metadata.get("textPresentation"),
            available_formats=metadata.get("availableFormats"),
        )

        table_rows = cls._rows_from_presentation(metadata.get("tablePresentation")) or cls._rows_from_presentation(
            metadata.get("presentation")
        )
        shape = decision.get("dataShape") if isinstance(decision.get("dataShape"), dict) else {}

        decision["insight"] = ChatPresentationInsightService.build(
            selected=str(decision.get("selected") or ""),
            rows=table_rows,
            data_shape={**shape, "labelKey": shape.get("labelKey")},
            reason=str(decision.get("reason") or ""),
        )

        policy_notice = cls._apply_chart_policy_to_metadata(
            metadata,
            decision,
            user_message=axis_user_message or user_message,
        )

        if policy_notice:
            decision["policyNotice"] = policy_notice
            decision["insight"] = f"{decision['insight']} {policy_notice}".strip()

        chart_presentation = metadata.get("chartPresentation") or metadata.get("presentation")

        if (
            isinstance(chart_presentation, dict)
            and chart_presentation.get("type") == "chart"
        ):
            from app.domain.services.chat_presentation_chart_explain_service import (
                ChatPresentationChartExplainService,
            )

            explanation = ChatPresentationChartExplainService.build(
                presentation=chart_presentation,
                decision=decision,
                insight=str(decision.get("insight") or ""),
            )

            if explanation:
                decision["chartExplanation"] = explanation

        metadata["presentationDecision"] = decision

        legacy = cls._legacy_preferred_format(decision.get("selected"))

        if legacy:
            metadata["preferredFormat"] = legacy

        views = decision.get("availableViews") or []

        if views:
            metadata["availableFormats"] = cls._legacy_available_formats(views)

        return metadata

    @classmethod
    def _build(
        cls,
        *,
        selected: str,
        fallback: str,
        reason: str,
        available_views: list[str],
        rows: list[dict[str, Any]] | None,
        intent: str | None,
        data_shape: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        shape = data_shape or ChatPresentationDataShapeAnalyzer.analyze(rows=rows)

        return {
            "selected": selected,
            "fallback": fallback,
            "reason": reason,
            "availableViews": available_views,
            "dataShape": {
                "rows": shape.get("rows", 0),
                "columns": shape.get("columns", 0),
                "hasDate": shape.get("hasDate", False),
                "hasNumeric": shape.get("hasNumeric", False),
                "hasCategory": shape.get("hasCategory", False),
                "hasHierarchy": shape.get("hasHierarchy", False),
                "labelKey": shape.get("labelKey"),
                "numericKeys": shape.get("numericKeys") or [],
            },
            "intent": str(intent or "").strip() or None,
        }

    @classmethod
    def _apply_chart_policy_to_metadata(
        cls,
        metadata: dict[str, Any],
        decision: dict[str, Any],
        *,
        user_message: str | None = None,
    ) -> str | None:
        selected = str(decision.get("selected") or "")
        chart_type = _SELECTED_TO_CHART_TYPE.get(selected)

        if not chart_type:
            return None

        notices: list[str] = []

        for key in ("presentation", "chartPresentation"):
            presentation = metadata.get(key)

            if not isinstance(presentation, dict) or presentation.get("type") != "chart":
                continue

            config = presentation.get("config")

            if not isinstance(config, dict):
                config = {}
                presentation["config"] = config

            label_key = str(config.get("xAxis") or decision.get("dataShape", {}).get("labelKey") or "")
            y_axis = config.get("yAxis")
            value_key = y_axis[0] if isinstance(y_axis, list) and y_axis else None

            original = presentation.get("data") or []
            original_count = len(original) if isinstance(original, list) else 0

            capped = ChatPresentationChartPolicyService.apply(
                original if isinstance(original, list) else [],
                chart_type,
                label_key=label_key or None,
                value_key=str(value_key) if value_key else None,
            )

            presentation["chartType"] = chart_type
            config["recommendedChartType"] = chart_type
            presentation["data"] = capped

            from app.domain.services.chat_presentation_axis_preference_service import (
                ChatPresentationAxisPreferenceService,
            )

            ChatPresentationAxisPreferenceService.apply_to_chart_config(
                presentation,
                user_message=user_message,
            )

            notice = ChatPresentationChartPolicyService.fallback_notice(
                chart_type,
                original_count,
                len(capped),
            )

            if notice:
                notices.append(notice)

        return notices[0] if notices else None

    @classmethod
    def _decision_for_preference(
        cls,
        preferred: str,
        *,
        rows: list[dict[str, Any]] | None,
        user_message: str,
        available_formats: list[str] | None,
        intent: str | None,
    ) -> dict[str, Any]:
        fallback = "table" if rows else "text"
        views = cls._merge_views(available_formats, [preferred, fallback, "text"])

        return cls._build(
            selected=preferred,
            fallback=fallback,
            reason="formato solicitado pelo usuário",
            available_views=views,
            rows=rows,
            intent=intent,
        )

    @classmethod
    def _normalize_user_preference(
        cls,
        user_preference: str | None,
        message: str,
    ) -> str | None:
        token = str(user_preference or "").strip().lower()

        if token in _USER_FORMAT_ALIASES:
            return _USER_FORMAT_ALIASES[token]

        if not message:
            return None

        for alias, mapped in _USER_FORMAT_ALIASES.items():
            if alias in ("text", "table") and f"em {alias}" in message:
                return mapped

            if alias in ("grafico", "gráfico", "chart") and any(
                hint in message
                for hint in ("em gráfico", "em grafico", "como gráfico", "como grafico")
            ):
                if any(
                    token in message
                    for token in ("linha", "line", "área", "area", "barra", "rosca", "donut")
                ):
                    if "linha" in message or "line" in message:
                        return "line_chart"

                    if "área" in message or "area" in message:
                        return "area_chart"

                    if "rosca" in message or "donut" in message:
                        return "donut"

                    if "horizontal" in message:
                        return "horizontal_bar"

                return "chart"

            if alias in ("tabela", "table") and any(
                hint in message
                for hint in ("em tabela", "como tabela", "formato tabela")
            ):
                return "table"

        return None

    @classmethod
    def _rows_from_presentation(
        cls,
        presentation: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if not isinstance(presentation, dict):
            return []

        if presentation.get("type") != "table":
            return []

        rows = presentation.get("rows") or []

        return [row for row in rows if isinstance(row, dict)]

    @classmethod
    def _merge_views(
        cls,
        available_formats: list[str] | None,
        defaults: list[str],
    ) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()

        for token in list(available_formats or []) + defaults:
            normalized = cls._view_from_legacy_format(str(token))

            if normalized in seen:
                continue

            seen.add(normalized)
            merged.append(normalized)

        return merged

    @classmethod
    def _view_from_legacy_format(cls, token: str) -> str:
        lowered = token.strip().lower()

        if lowered == "chart":
            return "chart"

        return lowered

    @classmethod
    def _legacy_preferred_format(cls, selected: str | None) -> str | None:
        if not selected:
            return None

        if selected in {"line_chart", "area_chart", "bar_chart", "horizontal_bar", "donut", "grouped_bar", "stacked_bar", "combo_chart", "histogram", "heatmap", "gauge", "scatter"}:
            return "chart"

        if selected == "canvas":
            return "text"

        return selected

    @classmethod
    def _legacy_available_formats(cls, views: list[str]) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()

        for view in views:
            legacy = cls._legacy_preferred_format(view) or view

            if legacy in seen:
                continue

            seen.add(legacy)
            output.append(legacy)

        return output

    @classmethod
    def _resolve_chart_type(
        cls,
        *,
        table_rows: list[dict[str, Any]],
        shape: dict[str, Any],
        user_message: str,
        fallback_chart: str,
    ) -> str:
        if table_rows and shape.get("hasNumeric"):
            label_key = str(shape.get("labelKey") or "label")
            numeric_keys = list(shape.get("numericKeys") or ["value"])

            return ChatChartTypeSelectionService.resolve(
                rows=table_rows[:24],
                label_key=label_key,
                numeric_keys=numeric_keys,
                user_message=user_message or None,
            )

        return str(fallback_chart or "bar").strip() or "bar"

    @classmethod
    def _chart_reason(cls, chart_type: str, shape: dict[str, Any]) -> str:
        if chart_type in {"line", "multi_line", "area"}:
            return "dados temporais com valor numérico"

        if chart_type in {"donut", "pie"}:
            return "participação ou distribuição por categoria"

        if chart_type == "horizontal_bar":
            return "ranking ou nomes longos"

        if shape.get("rows", 0) > 6:
            return "volume de categorias melhor em gráfico"

        return "dados numéricos comparáveis"

    @classmethod
    def _looks_like_checklist(cls, message: str) -> bool:
        if not message:
            return False

        return any(
            token in message
            for token in (
                "checklist",
                "plano de ação",
                "plano de acao",
                "pendências",
                "pendencias",
                "próximos passos",
                "proximos passos",
                "tarefas",
            )
        )

    @classmethod
    def _looks_like_canvas(cls, message: str) -> bool:
        if not message:
            return False

        return any(
            token in message
            for token in (
                "na lousa",
                "coloque na lousa",
                "colocar na lousa",
                "gerar relatório",
                "gerar relatorio",
                "ata de reunião",
                "ata de reuniao",
                "comunicado",
            )
        )
