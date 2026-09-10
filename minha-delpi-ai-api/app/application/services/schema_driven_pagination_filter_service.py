"""E3.S6 — fast paths de paginação/filtro com delta apenas em parâmetros do schema."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.services.schema_driven_argument_binder_service import (
    SchemaDrivenArgumentBinderService,
    SchemaDrivenBindResult,
)
from app.domain.entities.turn_refinement import TurnRefinement, TurnRefinementTarget
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)


@dataclass(frozen=True)
class SchemaDrivenPaginationFilterPlan:
    refinement: TurnRefinement
    bind: SchemaDrivenBindResult

    @property
    def ok(self) -> bool:
        return self.bind.ok and bool(
            set(self.refinement.argument_delta).intersection(self.bind.parameters)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "refinement": self.refinement.as_dict(),
            "bind": self.bind.as_dict(),
            "ok": self.ok,
        }


class SchemaDrivenPaginationFilterService:
    """Parsers determinísticos + binder OpenAPI (não inventa campo fora do schema)."""

    @classmethod
    def extract_argument_delta(
        cls,
        message: str,
        *,
        inherited_parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        if not normalized:
            return {}

        delta: dict[str, Any] = {}
        inherited = dict(inherited_parameters or {})

        page_size = ChatOperationalRefinementService.extract_requested_page_size(normalized)
        if page_size is not None:
            delta["page_size"] = page_size

        page = ChatOperationalRefinementService.extract_requested_page(normalized)
        if page is None and ChatOperationalRefinementService.looks_like_next_page_request(
            normalized
        ):
            current = _as_int(inherited.get("page")) or 1
            page = current + 1
        if page is None and ChatOperationalRefinementService.looks_like_prev_page_request(
            normalized
        ):
            current = _as_int(inherited.get("page")) or 1
            page = max(1, current - 1)
        if page is None and ChatOperationalRefinementService.looks_like_more_results_request(
            normalized
        ):
            current = _as_int(inherited.get("page")) or 1
            page = current + 1
        if page is not None:
            delta["page"] = page

        branch = None
        if "filial" in normalized:
            branch = ChatOperationalRefinementService.extract_branch_code(normalized)
        if branch:
            delta["branch"] = branch

        warehouse = None
        if "armazem" in normalized or "armazém" in normalized:
            warehouse = ChatOperationalRefinementService.extract_warehouse_code(normalized)
        if warehouse:
            delta["warehouse"] = warehouse

        return delta

    @classmethod
    def plan(
        cls,
        message: str,
        *,
        action: dict[str, Any],
        inherited_parameters: dict[str, Any] | None = None,
        action_id: str | None = None,
        provider: dict[str, Any] | None = None,
    ) -> SchemaDrivenPaginationFilterPlan | None:
        delta = cls.extract_argument_delta(
            message,
            inherited_parameters=inherited_parameters,
        )
        if not delta:
            return None

        target = None
        if action_id:
            target = TurnRefinementTarget(kind="action", action_id=str(action_id))

        refinement = TurnRefinement(
            kind="argument_delta",
            confidence=0.85,
            target=target,
            argument_delta=delta,
            reason="schema_driven_pagination_filter_fast_path",
            source="schema_driven_pagination_filter",
        )
        bind = SchemaDrivenArgumentBinderService.bind(
            action=action,
            refinement=refinement,
            inherited_parameters=inherited_parameters,
            message=message,
            provider=provider,
        )
        return SchemaDrivenPaginationFilterPlan(refinement=refinement, bind=bind)


def _as_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
