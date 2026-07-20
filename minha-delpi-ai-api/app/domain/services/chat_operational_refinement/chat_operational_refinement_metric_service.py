"""Delegate — refinamento operacional."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_route_context_service import (
    ChatRouteContextService,
    RecentMetricRoute,
)

from app.domain.services.chat_operational_refinement.chat_operational_refinement_facade_access import (
    refinement_service,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_models import (
    OperationalRefinement,
)


class ChatOperationalRefinementMetricService:
    @classmethod
    def plan_metric_follow_ups(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        recent = ChatRouteContextService.collect_recent_metric_route(previous_messages)

        if not recent:
            return []

        # Intent fresco de KPI (ex.: «meta comercial») prevalece sobre sticky do
        # último path (ex.: novos negócios) — refino só para escopo puro (filial).
        if cls._fresh_department_kpi_overrides_sticky(message, recent):
            return []

        branch = refinement_service().extract_branch_code(normalized)

        if ChatRouteContextService.looks_like_metric_scope_reset(normalized):
            return [
                OperationalRefinement(
                    kind="metric_reset",
                    metric_kind=recent.kind,
                    metric_domain_prefix=recent.domain_prefix,
                    metric_path_token=recent.path_token,
                    reason=recent.reason,
                )
            ]

        if not refinement_service().looks_like_operational_refinement(normalized):
            return []

        if not branch and not refinement_service()._requires_stock_refinement(normalized):
            return []

        return [
            OperationalRefinement(
                kind="metric_refinement",
                branch=branch,
                metric_kind=recent.kind,
                metric_domain_prefix=recent.domain_prefix,
                metric_path_token=recent.path_token,
                reason=recent.reason,
            )
        ]

    @classmethod
    def _fresh_department_kpi_overrides_sticky(
        cls,
        message: str,
        recent: RecentMetricRoute,
    ) -> bool:
        if recent.kind != "department_kpi":
            return False

        from app.domain.services.chat_department_kpi_intent_service import (
            ChatDepartmentKpiIntentService,
        )

        fresh = ChatDepartmentKpiIntentService.resolve(message)

        if fresh is None:
            return False

        if fresh.domain_prefix and fresh.domain_prefix not in (recent.domain_prefix or ""):
            return True

        return not cls._recent_route_matches_kpi_token(
            recent_path=str(recent.path or ""),
            recent_token=str(recent.path_token or ""),
            fresh_token=str(fresh.path_token or ""),
        )

    @classmethod
    def _recent_route_matches_kpi_token(
        cls,
        *,
        recent_path: str,
        recent_token: str,
        fresh_token: str,
    ) -> bool:
        """Compatível só se o segmento recente for o mesmo KPI (não superconjunto).

        Ex.: ``branch_rol_target`` casa ``branch_rol_target_pct``, mas **não**
        ``branch_new_business_rol_target_pct``.
        """
        token = (recent_token or "").strip().lower().strip("/")
        fresh = (fresh_token or "").strip().lower().strip("/")
        path = (recent_path or "").strip().lower()

        if not fresh:
            return False

        if not token and path:
            parts = [part for part in path.strip("/").split("/") if part]
            token = parts[1] if len(parts) >= 2 else ""

        if not token:
            return False

        if token == fresh or token == f"{fresh}_pct":
            return True

        if token.startswith(f"{fresh}/") or token.startswith(f"{fresh}_"):
            return True

        return False
