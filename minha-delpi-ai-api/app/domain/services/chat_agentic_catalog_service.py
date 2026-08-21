"""Catálogo enxuto de actions para o loop agentic (Onda 11.3.1)."""

from __future__ import annotations

from typing import Any, Protocol

from app.domain.services.chat_agentic_action_schema_service import (
    ChatAgenticActionSchemaService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_domain_config_service import ChatDomainConfigService


class ExternalActionCatalogRepositoryPort(Protocol):
    def find_candidate_actions(
        self,
        query: str,
        limit: int = 8,
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]: ...


class ChatAgenticCatalogService:
    _INTENT_PATH_HINTS: dict[str, tuple[str, ...]] = {
        ChatProductQueryIntent.STOCK: ("/stock", "stock", "estoque"),
        ChatProductQueryIntent.SALES: ("/sales", "sales", "vendas", "venda"),
        ChatProductQueryIntent.STRUCTURE: ("/structure", "structure", "estrutura", "bom"),
        ChatProductQueryIntent.PARENTS: ("/parents", "parents", "where-used", "onde"),
        ChatProductQueryIntent.SUMMARY: ("/summary", "summary", "resumo"),
        ChatProductQueryIntent.ANALYSER: ("/analyser", "analyser", "analisador", "ficha"),
        ChatProductQueryIntent.DESCRIPTION: ("/products/{code}", "/products/", "detail", "cadastro"),
    }

    _GENERIC_PRODUCT_HINTS = ("/products/", "product", "produto")

    @classmethod
    def resolve_limit(cls) -> int:
        return max(1, ChatDomainConfigService.chat_agentic_catalog_max_actions())

    @classmethod
    def build_ranked_candidates(
        cls,
        message: str,
        allowed_action_ids: list[str] | None,
        repository: ExternalActionCatalogRepositoryPort | None,
    ) -> list[dict[str, Any]]:
        allowed = [
            str(item).strip()
            for item in (allowed_action_ids or [])
            if str(item).strip()
        ]

        if not allowed:
            return []

        limit = cls.resolve_limit()
        candidates: list[dict[str, Any]] = []

        if repository is not None:
            candidates = repository.find_candidate_actions(
                message,
                limit=max(limit, limit * 2),
                allowed_action_ids=allowed,
            )

        if not candidates:
            return [{"actionId": action_id} for action_id in allowed[:limit]]

        intent = ChatProductQueryIntentService.resolve_product_intent(message)
        ranked = cls._rank_candidates(candidates, intent=intent)

        selected: list[dict[str, Any]] = []
        seen: set[str] = set()

        for action in ranked:
            action_id = str(action.get("actionId") or "").strip()

            if not action_id or action_id in seen:
                continue

            seen.add(action_id)
            selected.append(action)

            if len(selected) >= limit:
                break

        return selected

    @classmethod
    def build_action_ids(
        cls,
        message: str,
        allowed_action_ids: list[str] | None,
        repository: ExternalActionCatalogRepositoryPort | None,
    ) -> list[str]:
        return [
            str(action.get("actionId") or "").strip()
            for action in cls.build_ranked_candidates(message, allowed_action_ids, repository)
            if str(action.get("actionId") or "").strip()
        ]

    @classmethod
    def build_slim_catalog(
        cls,
        message: str,
        allowed_action_ids: list[str] | None,
        repository: ExternalActionCatalogRepositoryPort | None,
        *,
        memory_snapshot: dict | None = None,
        exclude_action_ids: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        ranked = cls.build_ranked_candidates(message, allowed_action_ids, repository)
        excluded = {
            str(item).strip() for item in (exclude_action_ids or set()) if str(item).strip()
        }
        product_code = cls._resolve_focus_product_code(message, memory_snapshot)
        slim_entries: list[dict[str, Any]] = []

        for action in ranked:
            action_id = str(action.get("actionId") or "").strip()

            if not action_id or action_id in excluded:
                continue

            slim = ChatAgenticActionSchemaService.build_slim_action(action)

            if not slim:
                continue

            if product_code:
                slim = cls._inject_product_code_examples(slim, product_code)
            elif cls._requires_product_code(slim) and not (
                ChatProductQueryIntentService.extract_product_code(message or "")
            ):
                # Sem código groundable neste turno — não oferecer a action ao planner.
                continue

            slim_entries.append(slim)

        return slim_entries

    @classmethod
    def _resolve_focus_product_code(
        cls,
        message: str | None,
        memory_snapshot: dict | None,
    ) -> str | None:
        from app.domain.services.chat_snapshot_operational_focus import (
            ChatSnapshotOperationalFocus,
        )
        from app.domain.services.chat_user_context_item_service import (
            ChatUserContextItemService,
        )

        code = ChatProductQueryIntentService.extract_product_code(message or "")

        if code:
            return code

        if not isinstance(memory_snapshot, dict):
            return None

        from_items = ChatUserContextItemService.resolve_product_code_from_items(
            memory_snapshot.get("userContextItems"),
        )

        if from_items:
            return from_items

        focus = ChatSnapshotOperationalFocus.get(memory_snapshot)

        if isinstance(focus, dict):
            token = str(focus.get("productCode") or "").strip()

            if token and ChatProductQueryIntentService.is_plausible_product_code(token):
                return token

        return None

    @classmethod
    def _requires_product_code(cls, slim: dict[str, Any]) -> bool:
        for parameter in slim.get("parameters") or []:
            if not isinstance(parameter, dict):
                continue

            name = str(parameter.get("name") or "").strip()

            if name in {"code", "productCode", "product_code"} and (
                parameter.get("required") or parameter.get("in") == "path"
            ):
                return True

        return False

    @classmethod
    def _inject_product_code_examples(
        cls,
        slim: dict[str, Any],
        product_code: str,
    ) -> dict[str, Any]:
        enriched = dict(slim)
        example = dict(enriched.get("exampleArguments") or {})

        for name in ("code", "productCode", "product_code"):
            for parameter in enriched.get("parameters") or []:
                if not isinstance(parameter, dict):
                    continue

                if str(parameter.get("name") or "").strip() == name:
                    example[name] = product_code

        if example:
            enriched["exampleArguments"] = example
            enriched["operationalFocusProductCode"] = product_code

        return enriched

    @classmethod
    def describe_catalog(
        cls,
        message: str,
        allowed_action_ids: list[str] | None,
        repository: ExternalActionCatalogRepositoryPort | None,
    ) -> dict[str, object]:
        action_ids = cls.build_action_ids(message, allowed_action_ids, repository)

        return {
            "actionIds": action_ids,
            "size": len(action_ids),
            "maxActions": cls.resolve_limit(),
            "intent": ChatProductQueryIntentService.resolve_product_intent(message),
        }

    @classmethod
    def _rank_candidates(cls, candidates: list[dict[str, Any]], *, intent: str) -> list[dict[str, Any]]:
        hints = cls._INTENT_PATH_HINTS.get(intent) or cls._GENERIC_PRODUCT_HINTS

        def score(action: dict[str, Any]) -> tuple[int, str]:
            haystack = " ".join(
                str(action.get(key) or "")
                for key in ("path", "operationId", "summary", "description", "actionId")
            ).lower()

            match_score = sum(2 if hint in haystack else 0 for hint in hints)

            if intent == ChatProductQueryIntent.FULL and any(
                hint in haystack for hint in cls._GENERIC_PRODUCT_HINTS
            ):
                match_score += 1

            return (-match_score, str(action.get("actionId") or ""))

        return sorted(candidates, key=score)
