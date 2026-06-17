"""Dicas de visual (tabela/árvore) — desacopladas de markdown e linhas de presenter."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)

_PROFILE_ROUTE_NAMESPACE: dict[str, str] = {
    "stock": "stock",
    "production_status": "productionStatus",
    "shipping_status": "shippingStatus",
    "structure_exclusivity": "structureExclusivity",
    "factory_status": "factoryStatus",
    "sale_pricing": "salePricing",
    "raw_material_price": "rawMaterialPriceIntelligence",
    "cost_impact": "costImpactSimulation",
    "purchase_history": "purchaseHistory",
    "purchases": "purchases",
    "directives": "directives",
    "factory_production_report": "factoryProductionReport",
}


class ChatPresentationVisualUiHintService:
    @classmethod
    def resolve_namespace(
        cls,
        *,
        path: str = "",
        profile_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        key = str(profile_key or "").strip()

        if not key and isinstance(metadata, dict):
            stack_plan = metadata.get("stackPresentationPlan")

            if isinstance(stack_plan, dict):
                key = str(stack_plan.get("presentationProfileKey") or "").strip()

        if not key:
            entity = None
            meta = metadata if isinstance(metadata, dict) else {}

            api_meta = meta.get("apiDelpiResponseMeta")

            if isinstance(api_meta, dict):
                entity = str(api_meta.get("entity") or "").strip() or None

            key = ChatPresentationProfileService.resolve_profile_key(path, entity)

        return _PROFILE_ROUTE_NAMESPACE.get(key, "")

    @classmethod
    def resolve_table_hint(
        cls,
        *,
        path: str = "",
        profile_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        namespace = cls.resolve_namespace(
            path=path,
            profile_key=profile_key,
            metadata=metadata,
        )

        if not namespace:
            return None

        hint = ChatAssistantContentService.get(
            "presenter_content",
            "routePresentations",
            namespace,
            "tableVisualizationHint",
            default="",
        )

        token = str(hint or "").strip()

        return token or None

    @classmethod
    def resolve_tree_hint(
        cls,
        *,
        path: str = "",
        profile_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        namespace = cls.resolve_namespace(
            path=path,
            profile_key=profile_key,
            metadata=metadata,
        )

        if not namespace:
            return None

        hint = ChatAssistantContentService.get(
            "presenter_content",
            "routePresentations",
            namespace,
            "treeVisualizationHint",
            default="",
        )

        token = str(hint or "").strip()

        return token or None

    @classmethod
    def view_will_render_in_contract(
        cls,
        *,
        decision: dict[str, Any],
        metadata: dict[str, Any] | None,
        view: str,
    ) -> bool:
        token = str(view or "").strip().lower()

        if not token:
            return False

        available = {
            str(item or "").strip().lower()
            for item in (decision.get("availableViews") or [])
            if str(item or "").strip()
        }

        if token not in available:
            return False

        meta = metadata if isinstance(metadata, dict) else {}
        selected = str(decision.get("selected") or "").strip().lower()
        layout_mode = str(decision.get("layoutMode") or "").strip().lower()

        if selected == token:
            return True

        if layout_mode != "stack":
            return False

        slot_key = {
            "tree": "treePresentation",
            "table": "tablePresentation",
            "chart": "chartPresentation",
            "kpi": "kpiPresentation",
            "dashboard": "dashboardPresentation",
        }.get(token)

        if slot_key and isinstance(meta.get(slot_key), dict):
            return bool(meta[slot_key].get("type"))

        if token == "table" and isinstance(meta.get("tablePresentations"), list):
            return any(
                isinstance(item, dict) and item.get("type") == "table"
                for item in meta["tablePresentations"]
            )

        presentation = meta.get("presentation")

        if isinstance(presentation, dict) and str(presentation.get("type") or "").strip().lower() == token:
            return True

        return False

    @classmethod
    def enrich_recommendations(
        cls,
        recommendations: list[dict[str, str]],
        *,
        decision: dict[str, Any],
        path: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        if not isinstance(decision, dict):
            return recommendations

        selected = str(decision.get("selected") or "").strip().lower()
        available = {
            str(view or "").strip().lower()
            for view in (decision.get("availableViews") or [])
            if str(view or "").strip()
        }
        output = list(recommendations)
        seen = {
            str(item.get("view") or "").strip().lower()
            for item in output
            if isinstance(item, dict)
        }

        def append(view: str, reason: str) -> None:
            token = str(view or "").strip().lower()
            message = str(reason or "").strip()

            if not token or not message or token == selected or token in seen:
                return

            if token not in available:
                return

            from app.domain.services.chat_presentation_recommendation_service import (
                ChatPresentationRecommendationService,
            )

            labels = ChatPresentationRecommendationService._view_labels()
            queries = ChatPresentationRecommendationService._view_queries()

            output.append(
                {
                    "view": token,
                    "label": labels.get(token, f"Ver como {token}"),
                    "reason": message,
                    "query": queries.get(token, f"mostre em {token}"),
                }
            )
            seen.add(token)

        table_hint = cls.resolve_table_hint(path=path, metadata=metadata)

        if table_hint and cls.view_will_render_in_contract(
            decision=decision,
            metadata=metadata,
            view="table",
        ):
            append("table", table_hint)

        tree_hint = cls.resolve_tree_hint(path=path, metadata=metadata)

        if tree_hint and cls.view_will_render_in_contract(
            decision=decision,
            metadata=metadata,
            view="tree",
        ):
            append("tree", tree_hint)

        return output[:3]
