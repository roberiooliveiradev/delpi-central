"""Solution catalog service — TÉO projection of Core solution knowledge.

Semantics carried to the caller:
- catalog lists ALL discoverable active solutions, never filtered to the
  user's accessible set — `accessible` is a flag, not a gate;
- `features`/`permissions`/`routes` are registered Core metadata (PROVEN
  evidence of existence, not full proof of behavior);
- `evolution` is CALCULATED structural diff between manifest snapshots —
  never inferred release purpose.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.solutions.solution_catalog_port import SolutionCatalogPort
from tm_app.infrastructure.gateways.core_solution_catalog_gateway import (
    CoreSolutionCatalogGateway,
)

_NOT_AUTHORITY_NOTE = (
    "Core solution metadata — knowledge, not authorization. `accessible` "
    "reports the user's effective access; it never grants it. Domain "
    "reads/writes inside a solution still require that app's own AuthZ."
)


class SolutionCatalogService:
    def __init__(self, gateway: SolutionCatalogPort | None = None) -> None:
        self._gateway = gateway or CoreSolutionCatalogGateway()

    def get_solution_catalog(self, authorization: str) -> dict[str, Any]:
        solutions = self._gateway.list_solutions(authorization)
        return {
            "schema": "solution_catalog_v1",
            "authority": "core_api",
            "note": _NOT_AUTHORITY_NOTE,
            "count": len(solutions),
            "solutions": solutions,
        }

    def get_solution_context(
        self, authorization: str, *, solution_id: str
    ) -> dict[str, Any]:
        plugin_id = str(solution_id or "").strip()
        if not plugin_id:
            raise GptActionsError(
                "solution_id é obrigatório.", 400, {"error_kind": "validation"}
            )
        solution = self._gateway.get_solution(plugin_id, authorization)
        if solution is None:
            raise GptActionsError(
                f"Solução desconhecida ou inativa: {plugin_id!r}.",
                404,
                {
                    "error_kind": "not_found",
                    "error_code": "solution_not_found",
                },
            )
        return {
            "schema": "solution_context_v1",
            "authority": "core_api",
            "note": _NOT_AUTHORITY_NOTE,
            "solution": solution,
        }
