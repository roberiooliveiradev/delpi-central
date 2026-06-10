"""Chips pós-resposta para tabelas, gráficos e árvores — Playbook 07."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_presentation_profile_service import ChatPresentationProfileService
from app.infrastructure.content.content_service import ContentService

_CHART_VIEWS = frozenset(
    {
        "chart",
        "line_chart",
        "area_chart",
        "bar_chart",
        "horizontal_bar",
        "donut",
        "scatter",
    }
)


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ContentService.load_json("assistant/interactivity")


class ChatPresentationInteractivityService:
    @classmethod
    def build_from_tool_calls(cls, tool_calls: list | None) -> list[dict[str, str]]:
        decision = cls._latest_presentation_decision(tool_calls)
        presentation_type = cls._detect_presentation_type(tool_calls)

        if not presentation_type:
            if cls._detect_sql_tool_call(tool_calls):
                presentation_type = "sql"
            elif isinstance(decision, dict):
                presentation_type = cls._resolve_chip_profile_type(decision)
            else:
                return []

        if not presentation_type:
            return []

        queries = _content().get("presentationQueries") or {}
        chip_labels = cls._filter_base_chips(
            presentation_type,
            tool_calls=tool_calls,
            queries=queries,
        )
        suggestions: list[dict[str, str]] = []

        for label in chip_labels[:6]:
            template = str(queries.get(label) or label).strip()
            item: dict[str, str] = {"label": str(label), "query": template}

            if str(label).strip() == "Explique esse gráfico":
                item["inlineAction"] = "explain_chart"

            if str(label).strip() == "Explique esse painel":
                item["inlineAction"] = "explain_dashboard"

            suggestions.append(item)

        suggestions.extend(
            cls._chips_from_presentation_decision(tool_calls, queries=queries)
        )

        if cls._detect_sql_tool_call(tool_calls):
            sql_labels = list(
                (_content().get("presentationChips") or {}).get("sql") or []
            )

            for label in sql_labels[:4]:
                template = str(queries.get(label) or label).strip()
                suggestions.append({"label": str(label), "query": template})

        return cls._dedupe_suggestions(suggestions)[:8]

    @classmethod
    def _resolve_chip_profile_type(cls, decision: dict[str, Any]) -> str | None:
        selected = str(decision.get("selected") or "").strip().lower()
        available = cls._normalized_views(decision)
        chips = _content().get("presentationChips") or {}

        if selected in chips:
            return selected

        if selected == "text" and "table" in available:
            return "table"

        if cls._is_chart_view(selected):
            return "chart"

        if selected in available:
            return selected

        for candidate in ("table", "chart", "tree", "kpi", "dashboard"):
            if candidate in available and candidate in chips:
                return candidate

        return None

    @classmethod
    def _filter_base_chips(
        cls,
        presentation_type: str,
        *,
        tool_calls: list | None,
        queries: dict[str, Any],
    ) -> list[str]:
        labels = list(
            (_content().get("presentationChips") or {}).get(presentation_type) or []
        )
        decision = cls._latest_presentation_decision(tool_calls)

        if not isinstance(decision, dict):
            return labels

        available = cls._normalized_views(decision)
        selected = str(decision.get("selected") or "").strip().lower()
        filtered: list[str] = []

        for label in labels:
            token = str(label).strip()

            if token in {"Gerar gráfico", "Ver em gráfico"} and not cls._chart_views_available(
                available,
                selected,
            ):
                continue

            if token in {"Ver como tabela", "Ver em tabela", "Exportar CSV"} and "table" not in available:
                continue

            if token == "Exportar CSV" and selected not in {"table", "text"} and "table" not in available:
                continue

            filtered.append(token)

        return filtered

    @classmethod
    def _chips_from_presentation_decision(
        cls,
        tool_calls: list | None,
        *,
        queries: dict[str, Any],
    ) -> list[dict[str, str]]:
        output: list[dict[str, str]] = []
        decision = cls._latest_presentation_decision(tool_calls)

        if not isinstance(decision, dict):
            return output

        metadata = cls._latest_tool_metadata(tool_calls) or {}
        selected = str(decision.get("selected") or "").strip().lower()
        available = cls._normalized_views(decision)
        profile_key = str(decision.get("presentationProfileKey") or "").strip()

        if not profile_key:
            path = str(metadata.get("path") or "")
            entity = str(metadata.get("entity") or "")
            profile = ChatPresentationProfileService.resolve_profile(path, entity)
            profile_key = str(profile.get("profileKey") or "").strip()

        profile = ChatPresentationProfileService.resolve_profile(
            str(metadata.get("path") or ""),
            str(metadata.get("entity") or ""),
        )
        view_order = [
            str(view).strip().lower()
            for view in (profile.get("viewOrder") or [])
            if str(view).strip()
        ]
        view_chip_labels = _content().get("viewChipLabels") or {}

        for view in view_order:
            if view == selected or view not in available:
                continue

            if cls._is_chart_view(view) and cls._is_chart_view(selected):
                continue

            label = str(view_chip_labels.get(view) or "").strip()

            if not label:
                continue

            output.append(
                {
                    "label": label,
                    "query": str(queries.get(label) or cls._default_query_for_view(view, queries)),
                }
            )

        profile_extra = (_content().get("profileExtraChips") or {}).get(profile_key) or []

        for label in profile_extra:
            token = str(label).strip()

            if not token:
                continue

            if token in {"Ver em gráfico", "Gerar gráfico"} and not cls._chart_views_available(
                available,
                selected,
            ):
                continue

            output.append(
                {
                    "label": token,
                    "query": str(queries.get(token) or token),
                }
            )

        for item in decision.get("recommendations") or []:
            if not isinstance(item, dict):
                continue

            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or queries.get(label) or label).strip()

            if not label or not query:
                continue

            output.append({"label": label, "query": query})

        return output

    @staticmethod
    def _default_query_for_view(view: str, queries: dict[str, Any]) -> str:
        mapping = {
            "table": "mostre o último resultado em tabela",
            "chart": "gere um gráfico com os dados acima",
            "tree": "mostre o último resultado em árvore",
            "text": "mostre o último resultado em texto",
            "canvas": "coloque o resultado acima na lousa",
        }

        fallback = mapping.get(view, f"mostre o último resultado em {view}")
        label = (_content().get("viewChipLabels") or {}).get(view, "")

        return str(queries.get(label) or fallback)

    @classmethod
    def _latest_presentation_decision(cls, tool_calls: list | None) -> dict[str, Any] | None:
        for call in reversed(tool_calls or []):
            if not isinstance(call, dict):
                continue

            metadata = call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            decision = metadata.get("presentationDecision")

            if isinstance(decision, dict):
                return decision

        return None

    @classmethod
    def _latest_tool_metadata(cls, tool_calls: list | None) -> dict[str, Any] | None:
        for call in reversed(tool_calls or []):
            if not isinstance(call, dict):
                continue

            metadata = call.get("metadata")

            if isinstance(metadata, dict) and metadata.get("ok"):
                return metadata

        return None

    @staticmethod
    def _normalized_views(decision: dict[str, Any]) -> set[str]:
        return {
            str(view or "").strip().lower()
            for view in (decision.get("availableViews") or [])
            if str(view or "").strip()
        }

    @classmethod
    def _chart_views_available(cls, available: set[str], selected: str) -> bool:
        if cls._is_chart_view(selected):
            return False

        return bool(available & _CHART_VIEWS) or "chart" in available

    @staticmethod
    def _is_chart_view(view: str) -> bool:
        token = str(view or "").strip().lower()
        return token in _CHART_VIEWS or token == "chart"

    @staticmethod
    def _dedupe_suggestions(suggestions: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[str] = set()
        output: list[dict[str, str]] = []

        for item in suggestions:
            label = str(item.get("label") or "").strip()

            if not label or label in seen:
                continue

            seen.add(label)
            output.append(item)

        return output

    @classmethod
    def _detect_presentation_type(cls, tool_calls: list | None) -> str | None:
        decision = cls._latest_presentation_decision(tool_calls)

        if isinstance(decision, dict):
            selected = str(decision.get("selected") or "").strip().lower()

            if selected in {"table", "chart", "tree", "kpi", "dashboard"}:
                return selected

            if selected in {"text", "canvas", ""}:
                return None

        for call in reversed(tool_calls or []):
            if not isinstance(call, dict):
                continue

            metadata = call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            presentation = metadata.get("presentation")

            if not isinstance(presentation, dict):
                continue

            token = str(presentation.get("type") or "").strip().lower()

            if token in {"table", "chart", "tree", "kpi", "dashboard"}:
                return token

        return None

    @classmethod
    def _detect_sql_tool_call(cls, tool_calls: list | None) -> bool:
        for call in reversed(tool_calls or []):
            if not isinstance(call, dict):
                continue

            metadata = call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            path = str(metadata.get("path") or "").lower()
            sensitivity = str(metadata.get("sensitivity") or "").lower()
            action_id = str(metadata.get("actionId") or "").lower()

            if path == "/data/sql" or sensitivity == "sql" or "sql" in action_id:
                return True

        return False
