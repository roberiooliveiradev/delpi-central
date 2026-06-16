"""Execução declarativa de fallbackPolicy SQL (DOCIE Fase 10)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
)
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_operational_intent_service import (
    ChatSqlOperationalIntentService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


@dataclass
class SqlFallbackRunState:
    abort_remaining: bool = False


class ExternalActionSqlFallbackPolicyService:
    """Resolve políticas ``fallbackPolicies`` do operational_route_registry."""

    @classmethod
    def try_policy(
        cls,
        policy: dict,
        *,
        message: str,
        sql_source: str,
        allowed_action_ids: list[str],
        select_sql: Callable[..., dict | None],
        after_rest_miss: bool = False,
        state: SqlFallbackRunState | None = None,
    ) -> dict | None:
        if not cls._matches_when(policy, message, after_rest_miss=after_rest_miss):
            return None

        selected = cls._execute_resolver(
            policy,
            message,
            allowed_action_ids=allowed_action_ids,
            select_sql=select_sql,
            sql_source=sql_source,
        )

        if selected:
            return selected

        if policy.get("blockRemainingWhenRequiresSqlKnowledge") and (
            ChatSqlOperationalIntentService.requires_sql_knowledge(message)
            and not ChatSqlIntentService.is_authoring_request(message)
        ):
            if state is not None:
                state.abort_remaining = True

        return None

    @classmethod
    def try_sql_refinement(
        cls,
        *,
        message: str,
        sql_source: str,
        allowed_action_ids: list[str],
        previous_messages: list | None,
        select_sql: Callable[..., dict | None],
        policy: dict | None = None,
    ) -> dict | None:
        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        sql_refinement = ChatSqlQueryRefinementService.resolve(
            message,
            previous_messages=previous_messages,
        )

        if not sql_refinement or sql_refinement.mode != "execute":
            return None

        reason_key = str(
            (policy or {}).get("reasonKey") or "sqlRefinement"
        ).strip()

        selected = select_sql(
            message,
            allowed_action_ids,
            sql=sql_refinement.sql,
            selection_reason_key=reason_key,
            raw_message=sql_source,
        )

        if not selected:
            return None

        selected["reason"] = ExternalActionResponseContentService.get(
            "selectionReasons",
            reason_key,
        )
        return selected

    @classmethod
    def _matches_when(
        cls,
        policy: dict,
        message: str,
        *,
        after_rest_miss: bool,
    ) -> bool:
        when = policy.get("when")

        if not isinstance(when, dict):
            return True

        if when.get("notAuthoring") and ChatSqlIntentService.is_authoring_request(message):
            return False

        if when.get("requiresProductionSqlKnowledge") and (
            not ChatSqlOperationalIntentService.requires_production_sql_knowledge(message)
        ):
            return False

        if when.get("productionQueryExecute"):
            from app.domain.services.chat_sql_production_query_service import (
                ChatSqlProductionQueryService,
            )

            resolution = ChatSqlProductionQueryService.resolve(message)

            if not resolution or resolution.mode != "execute":
                return False

        if when.get("requiresSqlKnowledge") and (
            not ChatSqlOperationalIntentService.requires_sql_knowledge(message)
        ):
            return False

        if when.get("requiresAutoExecuteSql") and (
            not ChatSqlIntentService.should_auto_execute_sql(message)
        ):
            return False

        if when.get("notProductionRestRoute") and (
            ChatProductionOperationalIntentService.matches_rest_route(message)
        ):
            return False

        if when.get("productionRestRoute") and (
            not ChatProductionOperationalIntentService.matches_rest_route(message)
        ):
            return False

        if when.get("afterRestMiss") and not after_rest_miss:
            return False

        return True

    @classmethod
    def _execute_resolver(
        cls,
        policy: dict,
        message: str,
        *,
        allowed_action_ids: list[str],
        select_sql: Callable[..., dict | None],
        sql_source: str,
    ) -> dict | None:
        resolver = str(policy.get("resolver") or "").strip()
        reason_key = str(policy.get("reasonKey") or "").strip() or None

        if resolver == "production_query":
            from app.domain.services.chat_sql_production_query_service import (
                ChatSqlProductionQueryService,
            )

            resolution = ChatSqlProductionQueryService.resolve(message)

            if not resolution or resolution.mode != "execute":
                return None

            return select_sql(
                message,
                allowed_action_ids,
                sql=resolution.sql,
                selection_reason_key=reason_key or "productionSqlFastPath",
                raw_message=sql_source,
            )

        if resolver == "inventory_query":
            from app.domain.services.chat_sql_inventory_query_service import (
                ChatSqlInventoryQueryService,
            )

            resolution = ChatSqlInventoryQueryService.resolve(message)

            if not resolution or resolution.mode != "execute":
                return None

            return select_sql(
                message,
                allowed_action_ids,
                sql=resolution.sql,
                selection_reason_key=reason_key or "inventorySqlFastPath",
                raw_message=sql_source,
            )

        if resolver == "generic_auto_execute":
            if not ChatSqlIntentService.should_auto_execute_sql(message):
                return None

            return select_sql(
                message,
                allowed_action_ids,
                raw_message=sql_source,
                selection_reason_key=reason_key or "genericSql",
            )

        return None
