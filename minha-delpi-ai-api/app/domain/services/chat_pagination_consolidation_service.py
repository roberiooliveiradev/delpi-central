"""Consolidação automática de rotas paginadas (total/completo/continuar)."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from math import ceil
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_tool_context_content_service import (
    ChatToolContextContentService,
)
from app.domain.services.chat_domain_config_service import ChatDomainConfigService


@dataclass(frozen=True)
class PaginationSnapshot:
    page: int
    page_size: int
    total: int | None
    total_pages: int | None
    shown: int | None


@dataclass(frozen=True)
class PaginationConsolidationState:
    action_id: str
    path: str
    parameters: dict[str, Any]
    fetched_pages: tuple[int, ...]
    merged_count: int
    api_total: int | None
    total_pages: int | None
    completed: bool


@dataclass(frozen=True)
class PaginationFetchPlan:
    mode: str
    pages_to_fetch: tuple[int, ...]
    base_parameters: dict[str, Any]
    action_id: str
    path: str
    resume_state: PaginationConsolidationState | None = None


class ChatPaginationConsolidationService:
    @classmethod
    def _full_fetch_terms(cls) -> tuple[str, ...]:
        return ChatToolContextContentService.list("pagination", "fullFetchTerms")

    @classmethod
    def _continue_terms(cls) -> tuple[str, ...]:
        return ChatToolContextContentService.list("pagination", "continueTerms")

    @classmethod
    def _yes_only_terms(cls) -> tuple[str, ...]:
        return ChatToolContextContentService.list("pagination", "yesOnlyTerms")

    _FULL_FETCH_PATTERNS = (
        re.compile(
            r"\b(tabela|lista|listagem|registros?|resultados?|itens?)"
            r"\s+(completo|completa|total|inteira?)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(completo|completa|total|inteira?)\s+(em\s+)?"
            r"(tabela|lista|listagem|arvore|árvore)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(traga|mostre|exiba|liste|busque|traga|trazer)\s+"
            r"(tudo|todos?|completo|completa)\b",
            re.IGNORECASE,
        ),
    )
    @classmethod
    def _yes_only_re(cls) -> re.Pattern[str]:
        joined = "|".join(re.escape(term) for term in cls._yes_only_terms())

        return re.compile(rf"^({joined})\.?$", re.IGNORECASE)

    @classmethod
    def enabled(cls) -> bool:
        return ChatDomainConfigService.chat_pagination_auto_fetch_enabled()

    @classmethod
    def max_pages_per_turn(cls) -> int:
        return max(1, min(ChatDomainConfigService.chat_pagination_max_pages_per_turn(), 8))

    @classmethod
    def looks_like_full_fetch_request(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if ChatMessageNormalizationService.contains_any(
            normalized,
            cls._full_fetch_terms(),
        ):
            return True

        return any(pattern.search(normalized) for pattern in cls._FULL_FETCH_PATTERNS)

    @classmethod
    def looks_like_continue_fetch_request(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if ChatMessageNormalizationService.contains_any(normalized, cls._continue_terms()):
            return True

        return cls._yes_only_re().match(normalized.strip()) is not None

    @classmethod
    def extract_snapshot(
        cls,
        *,
        metadata: dict | None,
        data: object,
    ) -> PaginationSnapshot | None:
        coverage = (metadata or {}).get("dataCoverageNotice")

        if isinstance(coverage, dict):
            details = coverage.get("details")

            if isinstance(details, dict):
                for key in ("pagination", "structurePagination", "stockPagination"):
                    pagination = details.get(key)

                    if isinstance(pagination, dict):
                        return PaginationSnapshot(
                            page=cls._as_int(pagination.get("page")) or 1,
                            page_size=cls._as_int(pagination.get("pageSize")) or 0,
                            total=cls._as_int(pagination.get("total")),
                            total_pages=cls._as_int(pagination.get("totalPages")),
                            shown=cls._as_int(pagination.get("shown")),
                        )

        root = cls._unwrap(data)

        if not isinstance(root, dict):
            return None

        items = root.get("items")

        if not isinstance(items, list):
            return None

        page = cls._as_int(root.get("page")) or 1
        page_size = cls._as_int(root.get("page_size")) or len(items)
        total = cls._as_int(root.get("total"))
        total_pages = cls._as_int(root.get("total_pages"))

        if total is None:
            return None

        if total_pages is None and page_size > 0 and total > 0:
            total_pages = max(1, ceil(total / page_size))

        if total <= len(items) and (total_pages is None or total_pages <= 1):
            return None

        return PaginationSnapshot(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            shown=len(items),
        )

    @classmethod
    def build_continue_plan(
        cls,
        *,
        message: str | None,
        previous_messages: list[Any] | None,
    ) -> PaginationFetchPlan | None:
        if not cls.enabled() or not cls.looks_like_continue_fetch_request(message):
            return None

        state = cls.collect_state(previous_messages)

        if not state:
            return None

        return cls._plan_from_state(state, mode="continue")

    @classmethod
    def build_fetch_plan(
        cls,
        *,
        message: str | None,
        metadata: dict | None,
        data: object,
        arguments: dict | None,
        previous_messages: list[Any] | None = None,
    ) -> PaginationFetchPlan | None:
        if not cls.enabled():
            return None

        resume = cls.collect_state(previous_messages)

        if resume and cls.looks_like_continue_fetch_request(message):
            return cls._plan_from_state(resume, mode="continue")

        snapshot = cls.extract_snapshot(metadata=metadata, data=data)

        if not snapshot or not snapshot.total_pages or snapshot.total_pages <= 1:
            resume = cls.collect_state(previous_messages)

            if resume and cls.looks_like_continue_fetch_request(message):
                return cls._plan_from_state(resume, mode="continue")

            return None

        args = dict((arguments or {}).get("parameters") or {})
        action_id = str(
            (metadata or {}).get("actionId")
            or (arguments or {}).get("actionId")
            or ""
        ).strip()
        path = str((metadata or {}).get("path") or "")

        resume = cls.collect_state(previous_messages)

        if resume and cls.looks_like_continue_fetch_request(message):
            if action_id and resume.action_id and action_id != resume.action_id:
                return None

            return cls._plan_from_state(resume, mode="continue")

        if not cls.looks_like_full_fetch_request(message):
            return None

        start_page = snapshot.page + 1
        remaining_pages = [
            page
            for page in range(start_page, snapshot.total_pages + 1)
        ][: cls.max_pages_per_turn()]

        if not remaining_pages and snapshot.page >= snapshot.total_pages:
            return None

        if not remaining_pages:
            remaining_pages = [snapshot.page + 1]

        return PaginationFetchPlan(
            mode="full_fetch",
            pages_to_fetch=tuple(remaining_pages),
            base_parameters=args,
            action_id=action_id,
            path=path,
            resume_state=PaginationConsolidationState(
                action_id=action_id,
                path=path,
                parameters=args,
                fetched_pages=(snapshot.page,),
                merged_count=snapshot.shown or len(cls._unwrap_items(data)),
                api_total=snapshot.total,
                total_pages=snapshot.total_pages,
                completed=False,
            ),
        )

    @classmethod
    def _plan_from_state(
        cls,
        state: PaginationConsolidationState,
        *,
        mode: str,
    ) -> PaginationFetchPlan | None:
        if state.completed or not state.total_pages:
            return None

        fetched = set(state.fetched_pages)
        remaining = [
            page
            for page in range(1, state.total_pages + 1)
            if page not in fetched
        ][: cls.max_pages_per_turn()]

        if not remaining:
            return None

        return PaginationFetchPlan(
            mode=mode,
            pages_to_fetch=tuple(remaining),
            base_parameters=dict(state.parameters),
            action_id=state.action_id,
            path=state.path,
            resume_state=state,
        )

    @classmethod
    def state_to_metadata(cls, state: PaginationConsolidationState, *, merged_data: object | None = None) -> dict:
        payload = {
            "actionId": state.action_id,
            "path": state.path,
            "parameters": state.parameters,
            "fetchedPages": list(state.fetched_pages),
            "mergedCount": state.merged_count,
            "apiTotal": state.api_total,
            "totalPages": state.total_pages,
            "completed": state.completed,
        }

        cached = cls.extract_cached_payload(merged_data)

        if cached:
            payload["consolidatedPayload"] = cached

        return payload

    @classmethod
    def extract_cached_payload(cls, data: object | None) -> dict | None:
        root = cls._unwrap(data)

        if not isinstance(root, dict):
            return None

        items = root.get("items")

        if not isinstance(items, list) or not items:
            return None

        return {
            "items": items,
            "total": cls._as_int(root.get("total")) or len(items),
            "page": 1,
            "page_size": len(items),
            "total_pages": 1,
        }

    @classmethod
    def load_cached_payload(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict | None:
        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)
            tool_calls = metadata.get("toolCalls") or []

            for tool_call in reversed(tool_calls):
                tool_meta = tool_call.get("metadata") or {}
                consolidation = tool_meta.get("paginationConsolidation")

                if not isinstance(consolidation, dict):
                    continue

                cached = consolidation.get("consolidatedPayload")

                if isinstance(cached, dict) and isinstance(cached.get("items"), list):
                    return cached

        return None

    @classmethod
    def merge_payloads(cls, payloads: list[object], *, cached: dict | None = None) -> object:
        if cached and not payloads:
            return {"data": cached}

        if not payloads and cached:
            return {"data": cached}

        if not payloads:
            return {}

        if len(payloads) == 1 and not cached:
            return copy.deepcopy(payloads[0])

        first_root = cls._unwrap(payloads[0])
        merged_root = copy.deepcopy(first_root) if isinstance(first_root, dict) else {}

        if cached:
            merged_root = copy.deepcopy(cached)

        if not isinstance(merged_root, dict):
            return payloads[0]

        all_items: list = list(merged_root.get("items") or []) if cached else []

        for payload in payloads:
            root = cls._unwrap(payload)

            if not isinstance(root, dict):
                continue

            items = root.get("items")

            if isinstance(items, list):
                all_items.extend(items)

        merged_root["items"] = all_items
        merged_root["page"] = 1
        merged_root["page_size"] = max(len(all_items), 1)
        merged_root["total"] = merged_root.get("total") or len(all_items)
        merged_root["total_pages"] = 1

        return cls._rewrap(payloads[0], merged_root)

    @classmethod
    def build_state(
        cls,
        *,
        plan: PaginationFetchPlan,
        fetched_pages: list[int],
        merged_count: int,
        api_total: int | None,
        total_pages: int | None,
    ) -> PaginationConsolidationState:
        resume = plan.resume_state
        pages = sorted(set((resume.fetched_pages if resume else ()) + tuple(fetched_pages)))

        completed = bool(
            total_pages
            and pages
            and max(pages) >= total_pages
            and merged_count >= (api_total or merged_count)
        )

        return PaginationConsolidationState(
            action_id=plan.action_id,
            path=plan.path,
            parameters=dict(plan.base_parameters),
            fetched_pages=tuple(pages),
            merged_count=merged_count,
            api_total=api_total,
            total_pages=total_pages,
            completed=completed,
        )

    @classmethod
    def collect_last_paginated_reference(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_operational_refinement_service import (
            ChatOperationalRefinementService,
        )

        recent = ChatOperationalRefinementService.collect_recent_paginated_action(
            previous_messages,
        )

        if not recent:
            return None

        action_id = str(recent.action_id or "").strip()

        if not action_id:
            return None

        return {
            "actionId": action_id,
            "path": recent.path,
            "parameters": dict(recent.parameters),
        }

    @classmethod
    def collect_last_preferred_format(
        cls,
        previous_messages: list[Any] | None,
    ) -> str | None:
        """Herda formato do turno anterior **apenas** quando foi escolha explícita.

        Decisão automática (`presentationDecision.selected` sem
        `explicitSessionFormat`) não é preferência do usuário: herdá-la torna o
        formato pegajoso e transforma seleção automática em modo explícito nos
        turnos seguintes (ex.: «text» para sempre no Automático). Escolha
        explícita — pedido na mensagem, toolbar ou formato de sessão — sempre
        grava `explicitSessionFormat` no metadata do turno.
        """
        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)
            tool_calls = metadata.get("toolCalls") or []

            for tool_call in reversed(tool_calls):
                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}
                explicit = str(tool_meta.get("explicitSessionFormat") or "").strip().lower()

                if not explicit:
                    continue

                decision = tool_meta.get("presentationDecision")

                if isinstance(decision, dict):
                    selected = str(decision.get("selected") or "").strip().lower()

                    if selected in {"table", "tree", "chart", "text", "canvas"}:
                        if selected == "table" and isinstance(tool_meta.get("treePresentation"), dict):
                            return "tree"

                        return selected

                    if selected in {
                        "line_chart",
                        "area_chart",
                        "bar_chart",
                        "horizontal_bar",
                        "donut",
                        "scatter",
                        "kpi",
                    }:
                        if selected == "kpi":
                            return "chart"

                        return "chart"

                preferred = str(tool_meta.get("preferredFormat") or "").strip().lower()

                if preferred in {"table", "tree", "chart", "text", "canvas"}:
                    if preferred == "table" and isinstance(tool_meta.get("treePresentation"), dict):
                        return "tree"
                    return preferred

                tree_presentation = tool_meta.get("treePresentation")

                if isinstance(tree_presentation, dict):
                    return "tree"

                presentation = tool_meta.get("presentation")

                if isinstance(presentation, dict):
                    presentation_type = str(presentation.get("type") or "").strip().lower()

                    if presentation_type == "tree":
                        return "tree"

                    if presentation_type in {"table", "chart", "kpi", "canvas"}:
                        if presentation_type == "kpi":
                            return "chart"

                        return presentation_type

                table_presentation = tool_meta.get("tablePresentation")

                if isinstance(table_presentation, dict):
                    return "table"

        return None

    @classmethod
    def collect_state(
        cls,
        previous_messages: list[Any] | None,
    ) -> PaginationConsolidationState | None:
        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)
            tool_calls = metadata.get("toolCalls") or []

            for tool_call in reversed(tool_calls):
                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}
                consolidation = tool_meta.get("paginationConsolidation")

                if not isinstance(consolidation, dict):
                    continue

                if consolidation.get("completed"):
                    continue

                fetched_pages = tuple(
                    int(page)
                    for page in consolidation.get("fetchedPages") or []
                    if cls._as_int(page)
                )

                return PaginationConsolidationState(
                    action_id=str(consolidation.get("actionId") or tool_meta.get("actionId") or ""),
                    path=str(consolidation.get("path") or tool_meta.get("path") or ""),
                    parameters=dict(consolidation.get("parameters") or {}),
                    fetched_pages=fetched_pages,
                    merged_count=cls._as_int(consolidation.get("mergedCount")) or 0,
                    api_total=cls._as_int(consolidation.get("apiTotal")),
                    total_pages=cls._as_int(consolidation.get("totalPages")),
                    completed=bool(consolidation.get("completed")),
                )

        return None

    @classmethod
    def build_continue_prompt(
        cls,
        *,
        state: PaginationConsolidationState,
        label: str = "registro(s)",
    ) -> str:
        total = state.api_total or state.merged_count
        remaining = max(0, total - state.merged_count)

        if remaining <= 0:
            return ""

        pages_left = 0

        if state.total_pages and state.fetched_pages:
            pages_left = max(
                0,
                state.total_pages - len(set(state.fetched_pages)),
            )

        return (
            f"Consolidei **{state.merged_count}** de **{total}** {label} "
            f"(páginas {', '.join(str(p) for p in state.fetched_pages)}). "
            f"Ainda faltam cerca de **{remaining}** {label}"
            f"{f' em {pages_left} página(s)' if pages_left else ''}. "
            "**Deseja que eu continue buscando?** Responda *sim, continue* para trazer o restante."
        )

    @classmethod
    def _unwrap_items(cls, data: object) -> list:
        root = cls._unwrap(data)

        if isinstance(root, dict) and isinstance(root.get("items"), list):
            return root["items"]

        return []

    @classmethod
    def _unwrap(cls, data: object):
        root = data

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        return root

    @classmethod
    def _rewrap(cls, original: object, root: dict):
        if not isinstance(original, dict):
            return root

        wrapped = copy.deepcopy(original)

        if "data" in wrapped and isinstance(wrapped["data"], dict) and "data" in wrapped["data"]:
            wrapped["data"]["data"] = root
            return wrapped

        if "data" in wrapped:
            wrapped["data"] = root
            return wrapped

        return root

    @classmethod
    def _as_int(cls, value) -> int | None:
        if value in (None, ""):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _message_metadata(cls, message: Any) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)
        return metadata if isinstance(metadata, dict) else {}
