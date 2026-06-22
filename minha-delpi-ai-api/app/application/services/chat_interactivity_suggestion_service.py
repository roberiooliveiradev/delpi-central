"""Consolidação de chips e sugestões — Playbook 07."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any

from app.application.services.chat_interactivity_preference_service import (
    ChatInteractivityPreferenceService,
)
from app.application.services.chat_interactivity_query_resolver import (
    ChatInteractivityQueryResolver,
)
from app.application.services.chat_operational_refinement_interactivity_service import (
    ChatOperationalRefinementInteractivityService,
)
from app.application.services.chat_presentation_interactivity_service import (
    ChatPresentationInteractivityService,
)
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ContentService.load_json("assistant/interactivity")


class ChatInteractivitySuggestionService:
    _SQL_TURN_OPERATIONAL_CHIP_LABELS = frozenset(
        {
            "Ver estoque",
            "Consultar produto",
            "Ver fornecedores",
            "Ver estrutura",
            "Ver vendas",
            "Onde é usado?",
        }
    )

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        workspace_context: dict | None = None,
        tool_calls: list | None = None,
        intent_route: dict | None = None,
        message: str | None = None,
    ) -> None:
        presentation = ChatPresentationInteractivityService.build_from_tool_calls(tool_calls)

        if presentation:
            metadata["presentationFollowUpSuggestions"] = presentation

        refinement = ChatOperationalRefinementInteractivityService.build_from_tool_calls(
            tool_calls,
        )

        if refinement:
            metadata["operationalRefinementFollowUpSuggestions"] = refinement

        from app.domain.services.chat_sql_authoring_guidance_service import (
            ChatSqlAuthoringGuidanceService,
        )

        sql_authoring = ChatSqlAuthoringGuidanceService.build_follow_up_suggestions(
            message=str(message or metadata.get("userMessage") or ""),
            tool_calls=tool_calls,
        )

        if sql_authoring:
            metadata["sqlAuthoringFollowUpSuggestions"] = sql_authoring

        from app.domain.services.chat_advanced_sql_specialist_service import (
            ChatAdvancedSqlSpecialistService,
        )

        sql_advanced = ChatAdvancedSqlSpecialistService.build_follow_up_suggestions(
            message=str(message or metadata.get("userMessage") or ""),
            tool_calls=tool_calls,
        )

        if sql_advanced:
            metadata["sqlAdvancedFollowUpSuggestions"] = sql_advanced

        raw = cls._collect_raw(
            metadata,
            intent_route=intent_route,
            tool_calls=tool_calls,
        )
        usage = ChatInteractivityPreferenceService.usage_from_workspace(workspace_context)
        enriched = [
            cls._enrich(
                item,
                metadata=metadata,
                workspace_context=workspace_context,
            )
            for item in raw
        ]
        deduped = cls._dedupe(enriched)
        ranked = cls._rank(
            deduped,
            metadata=metadata,
            intent_route=intent_route,
            usage=usage,
            tool_calls=tool_calls,
        )
        primary, more = cls._partition(ranked)

        context_bar = cls._build_context_bar(metadata)

        metadata["interactivity"] = {
            "consolidated": True,
            "maxPrimary": cls._max_primary(),
            "suggestions": primary,
            "moreSuggestions": more,
            "contextBar": context_bar,
            "sourceIntent": (
                str(intent_route.get("intent") or "").strip()
                if isinstance(intent_route, dict)
                else None
            ),
            "suggestionsShown": [item.get("label") for item in primary + sum(more.values(), [])],
        }

        admin_debug = metadata.get("adminDebug")

        if isinstance(admin_debug, dict):
            admin_debug["interactivity"] = {
                "primaryCount": len(primary),
                "moreCount": sum(len(items) for items in more.values()),
                "sourceIntent": metadata["interactivity"].get("sourceIntent"),
            }

    @classmethod
    def _collect_raw(
        cls,
        metadata: dict,
        *,
        intent_route: dict | None = None,
        tool_calls: list | None = None,
    ) -> list[dict[str, Any]]:
        from app.application.services.chat_web_search_follow_up_service import (
            ChatWebSearchFollowUpService,
        )

        collected: list[dict[str, Any]] = []
        sub_intent = (
            str(intent_route.get("subIntent") or intent_route.get("router", {}).get("subIntent") or "")
            if isinstance(intent_route, dict)
            else ""
        )
        sql_turn = sub_intent.startswith("sql_")
        web_primary_turn = ChatWebSearchFollowUpService.is_primary_web_search_turn(
            tool_calls,
            metadata=metadata,
        )

        for source in _content().get("metadataSources") or []:
            if not isinstance(source, dict):
                continue

            key = str(source.get("key") or "").strip()
            items = metadata.get(key)

            if not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue

                label = str(item.get("label") or "").strip()
                query = str(item.get("query") or "").strip()

                if not label or not query:
                    continue

                if (
                    sql_turn
                    and key == "followUpSuggestions"
                    and label in cls._SQL_TURN_OPERATIONAL_CHIP_LABELS
                ):
                    continue

                if (
                    web_primary_turn
                    and key == "followUpSuggestions"
                    and label in cls._SQL_TURN_OPERATIONAL_CHIP_LABELS
                ):
                    continue

                collected.append(
                    {
                        "label": label,
                        "query": query,
                        "group": str(source.get("group") or "consultar"),
                        "priority": int(source.get("priority") or 100),
                        "sourceKey": key,
                    }
                )

        return collected

    @classmethod
    def _enrich(
        cls,
        item: dict[str, Any],
        *,
        metadata: dict | None = None,
        workspace_context: dict | None,
    ) -> dict[str, Any]:
        label = str(item.get("label") or "").strip()
        query = ChatInteractivityQueryResolver.resolve(
            str(item.get("query") or "").strip(),
            metadata=metadata,
            workspace_context=workspace_context,
        )
        group = cls._resolve_group(label, str(item.get("group") or ""))
        kind = "primary" if label in (_content().get("primaryLabels") or []) else "secondary"
        suggestion_id = hashlib.sha1(f"{label}:{query}".encode()).hexdigest()[:12]

        enriched: dict[str, Any] = {
            "id": suggestion_id,
            "label": label,
            "query": query,
            "group": group,
            "kind": kind,
            "priority": item.get("priority", 100),
            "sourceKey": item.get("sourceKey"),
        }

        normalized_query = query.lower()

        if any(token in normalized_query for token in _content().get("sensitiveQueries") or []):
            enriched["requiresConfirmation"] = True
            enriched["tooltip"] = "Esta ação pede confirmação antes de executar."

        disabled = cls._disabled_reason(label, workspace_context=workspace_context)

        if disabled:
            enriched["disabledReason"] = disabled
            enriched["kind"] = "ghost"

        inline_action = str(item.get("inlineAction") or "").strip()

        if inline_action:
            enriched["inlineAction"] = inline_action

        return enriched

    @classmethod
    def _disabled_reason(
        cls,
        label: str,
        *,
        workspace_context: dict | None,
    ) -> str | None:
        capabilities = (workspace_context or {}).get("capabilities") or {}
        operational_labels = {
            str(item).strip()
            for item in (_content().get("operationalAgentRequiredLabels") or [])
            if str(item or "").strip()
        }
        operational_disabled = str(
            (_content().get("disabledReasons") or {}).get("operationalAgentRequired")
            or "Ative um agente com consultas operacionais para usar esta ação."
        ).strip()

        if label == "Colocar na lousa" and capabilities.get("canvas") is False:
            return "A lousa não está habilitada neste agente."

        if label in operational_labels:
            if not (workspace_context or {}).get("userActivatedAgent") and not (
                workspace_context or {}
            ).get("actionsEnabled"):
                return operational_disabled

        sql_action_labels = {
            "Executar query",
            "Ver colunas da tabela",
            "Ver schema completo",
            "Ver relações",
            "Interpretar resultado",
            "Gerar gráfico",
        }

        if label in sql_action_labels and not (workspace_context or {}).get("actionsEnabled"):
            return "Ative um agente com actions SQL/schema para consultar ou executar no banco."

        return None

    @classmethod
    def _resolve_group(cls, label: str, fallback: str) -> str:
        mapping = _content().get("labelGroups") or {}

        if isinstance(mapping, dict) and label in mapping:
            return str(mapping[label])

        return fallback or "consultar"

    @classmethod
    def _dedupe(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        output: list[dict[str, Any]] = []

        for item in items:
            token = f"{item.get('label')}|{item.get('query')}".lower()

            if token in seen:
                continue

            seen.add(token)
            output.append(item)

        return output

    @classmethod
    def _rank(
        cls,
        items: list[dict[str, Any]],
        *,
        metadata: dict,
        intent_route: dict | None,
        usage: dict[str, int] | None = None,
        tool_calls: list | None = None,
    ) -> list[dict[str, Any]]:
        from app.application.services.chat_web_search_follow_up_service import (
            ChatWebSearchFollowUpService,
        )

        intent = (
            str(intent_route.get("intent") or "").strip().lower()
            if isinstance(intent_route, dict)
            else ""
        )
        has_error = isinstance(metadata.get("errorHandling"), dict)
        web_primary_turn = ChatWebSearchFollowUpService.is_primary_web_search_turn(
            tool_calls,
            metadata=metadata,
        )

        def sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
            priority = int(item.get("priority") or 100)
            kind_rank = 0 if item.get("kind") == "primary" else 1
            disabled_rank = 1 if item.get("disabledReason") else 0

            intent_boost = 0

            if intent.startswith("text") and item.get("group") == "formatar":
                intent_boost = -15

            if (
                not web_primary_turn
                and intent in {"product_lookup", "operational_query", "self_help"}
                and item.get("group") == "consultar"
            ):
                intent_boost = -15

            if web_primary_turn and item.get("sourceKey") == "webSearchFollowUpSuggestions":
                intent_boost = -30

            if web_primary_turn and item.get("sourceKey") == "followUpSuggestions":
                intent_boost = 40

            sub_intent = (
                str(intent_route.get("subIntent") or intent_route.get("router", {}).get("subIntent") or "")
                if isinstance(intent_route, dict)
                else ""
            )

            if sub_intent.startswith("sql_"):
                if item.get("sourceKey") in {
                    "sqlAdvancedFollowUpSuggestions",
                    "sqlAuthoringFollowUpSuggestions",
                }:
                    intent_boost = -40
                elif item.get("sourceKey") == "followUpSuggestions":
                    intent_boost = 25

            if item.get("group") == "recuperar" and has_error:
                intent_boost = -20

            preference_boost = ChatInteractivityPreferenceService.rank_boost(
                str(item.get("label") or ""),
                usage,
            )

            presentation_boost = cls._presentation_view_chip_boost(item, tool_calls)

            return (
                disabled_rank,
                priority + intent_boost + kind_rank + preference_boost + presentation_boost,
                str(item.get("label")),
            )

        return sorted(items, key=sort_key)

    @classmethod
    def _presentation_view_chip_boost(
        cls,
        item: dict[str, Any],
        tool_calls: list | None,
    ) -> int:
        source_key = str(item.get("sourceKey") or "").strip()

        if source_key not in {
            "presentationFollowUpSuggestions",
            "operationalRefinementFollowUpSuggestions",
        }:
            return 0

        label = str(item.get("label") or "").strip()
        view_labels = {
            str(value).strip()
            for value in (_content().get("viewChipLabels") or {}).values()
            if str(value).strip()
        }

        if label not in view_labels:
            return 0

        decision = ChatPresentationInteractivityService._latest_presentation_decision(
            tool_calls,
        )

        if not isinstance(decision, dict):
            return 0

        available = [
            str(view or "").strip().lower()
            for view in (decision.get("availableViews") or [])
            if str(view or "").strip()
        ]

        if len(set(available)) < 2:
            return 0

        boost = _content().get("presentationViewChipBoost")

        if isinstance(boost, int):
            return boost

        return -28

    @classmethod
    def _partition(
        cls,
        items: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
        max_primary = cls._max_primary()
        enabled = [item for item in items if not item.get("disabledReason")]
        disabled = [item for item in items if item.get("disabledReason")]

        primary = enabled[:max_primary]
        overflow = enabled[max_primary:] + disabled
        more: dict[str, list[dict[str, Any]]] = {}
        group_labels = _content().get("groupLabels") or {}

        for item in overflow:
            group = str(item.get("group") or "consultar")
            more.setdefault(group, []).append(item)

        if not more:
            return primary, {}

        ordered: dict[str, list[dict[str, Any]]] = {}

        for group in sorted(more.keys(), key=lambda g: str(group_labels.get(g) or g)):
            ordered[group] = more[group][:8]

        return primary, ordered

    @classmethod
    def _build_context_bar(cls, metadata: dict) -> dict[str, Any] | None:
        chips = metadata.get("contextChips")

        if not isinstance(chips, list) or not chips:
            return None

        snapshot = metadata.get("contextSnapshot")
        memory_ux = metadata.get("memoryUx")
        summary = None

        if isinstance(memory_ux, dict):
            context_bar = memory_ux.get("contextBar")

            if isinstance(context_bar, dict) and context_bar.get("summary"):
                summary = str(context_bar["summary"]).strip() or None

        if not summary and isinstance(snapshot, dict):
            from app.domain.services.chat_memory_ux_service import ChatMemoryUxService

            summary = ChatMemoryUxService.build_context_bar_summary(snapshot)

        return {
            "items": chips,
            "summary": summary,
        }

    @classmethod
    def _max_primary(cls) -> int:
        token = _content().get("maxPrimary")

        if isinstance(token, int) and token > 0:
            return token

        return 4
