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

        # Intent fresco (outro KPI / outro departamento) prevalece sobre sticky.
        if cls._fresh_intent_overrides_sticky(message, recent):
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
    def _fresh_intent_overrides_sticky(
        cls,
        message: str,
        recent: RecentMetricRoute,
    ) -> bool:
        if cls._mentioned_department_conflicts_with_recent(message, recent):
            return True

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
    def _mentioned_department_conflicts_with_recent(
        cls,
        message: str,
        recent: RecentMetricRoute,
    ) -> bool:
        mentioned = cls._resolve_mentioned_department_id(message)
        recent_department = cls._department_id_for_recent_route(recent)

        if not mentioned or not recent_department:
            return False

        return mentioned != recent_department

    @classmethod
    def _resolve_mentioned_department_id(cls, message: str) -> str | None:
        from app.domain.services.chat_operational_api_domain_service import (
            ChatOperationalApiDomainService,
        )
        from app.domain.services.operational_api_parameter_builder_service import (
            OperationalApiParameterBuilderService,
        )

        spec = ChatOperationalApiDomainService.parameter_strategy_spec("department_idd")
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized or not isinstance(spec, dict):
            return None

        resolved = OperationalApiParameterBuilderService._resolve_source_value(
            "department_id_regex",
            {"source": "department_id_regex", "matchAliases": ["department_id"]},
            spec,
            {"normalized": normalized},
        )

        value = str(resolved or "").strip().lower()

        return value or None

    @classmethod
    def _department_id_for_recent_route(cls, recent: RecentMetricRoute) -> str | None:
        from app.domain.services.chat_operational_api_domain_service import (
            ChatOperationalApiDomainService,
        )

        spec = ChatOperationalApiDomainService.parameter_strategy_spec("department_idd")
        aliases = spec.get("departmentIdAliases") if isinstance(spec, dict) else None
        if not isinstance(aliases, dict):
            aliases = {}

        # J-R8: no pathPrefix→department map. Use semantic domain token from context.
        raw = str(recent.domain_prefix or "").strip().lower()
        token = raw.strip("/")
        if "/" in token:
            token = token.split("/")[0]
        if not token:
            return None

        known = {
            "commercial",
            "financial",
            "production",
            "quality",
            "hr",
            "supplies",
            "engineering",
        }
        if token in aliases:
            value = str(aliases.get(token) or "").strip().lower()
            return value or None
        if token in known:
            return token
        return None

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
