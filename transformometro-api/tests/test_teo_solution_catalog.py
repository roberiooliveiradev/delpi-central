"""TÉO solution intelligence — Core catalog projection tests.

Semantics under test:
- catalog is NOT filtered to accessible apps (knowledge != authorization);
- accessible flag passes through Core's computation verbatim;
- unknown solution → typed not-found, never silent fallback;
- no generic proxy — only list/detail calls with user Bearer forward.
"""

from __future__ import annotations

import pytest

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.solutions.solution_catalog_service import (
    SolutionCatalogService,
    SolutionNotFoundError,
)


class _FakeGateway:
    def __init__(self, solutions):
        self._solutions = {s["id"]: s for s in solutions}
        self.calls: list[tuple[str, str | None, str]] = []

    def list_solutions(self, authorization: str):
        self.calls.append(("list", None, authorization))
        return list(self._solutions.values())

    def get_solution(self, plugin_id: str, authorization: str):
        self.calls.append(("get", plugin_id, authorization))
        return self._solutions.get(plugin_id)


SOLUTIONS = [
    {
        "id": "transformometro",
        "name": "Portal Transforma+",
        "description": "Processos, indicadores, atas.",
        "type": "microfrontend",
        "version": "0.5.5",
        "routes": [{"path": "/apps/transformometro", "label": "Portal"}],
        "features": None,
        "permissions": [{"code": "transformometro.access"}],
        "accessible": True,
    },
    {
        "id": "tv-dashboard",
        "name": "Painéis TV",
        "description": "Indicadores em TVs.",
        "type": "microfrontend",
        "version": "0.2.0",
        "routes": [{"path": "/apps/tv-dashboard", "label": "Painéis"}],
        "features": None,
        "permissions": [{"code": "tv-dashboard.access"}],
        "accessible": False,  # Core-computed flag — knowledge still visible
    },
]


def test_catalog_lists_inaccessible_solutions() -> None:
    svc = SolutionCatalogService(gateway=_FakeGateway(SOLUTIONS))
    result = svc.get_solution_catalog("Bearer token")
    assert result["schema"] == "solution_catalog_v1"
    by_id = {s["id"]: s for s in result["solutions"]}
    # Scenario A core assertion: inaccessible app still discoverable.
    assert by_id["tv-dashboard"]["accessible"] is False
    assert by_id["transformometro"]["accessible"] is True
    assert result["count"] == 2


def test_solution_context_detail_and_unknown() -> None:
    gateway = _FakeGateway(SOLUTIONS)
    svc = SolutionCatalogService(gateway=gateway)
    ctx = svc.get_solution_context("Bearer token", solution_id="tv-dashboard")
    assert ctx["solution"]["id"] == "tv-dashboard"
    assert ctx["solution"]["accessible"] is False
    with pytest.raises(SolutionNotFoundError):
        svc.get_solution_context("Bearer token", solution_id="nope")


def test_bearer_is_forwarded_verbatim() -> None:
    gateway = _FakeGateway(SOLUTIONS)
    svc = SolutionCatalogService(gateway=gateway)
    svc.get_solution_catalog("Bearer user-token-123")
    assert gateway.calls == [("list", None, "Bearer user-token-123")]


def test_solution_id_required() -> None:
    svc = SolutionCatalogService(gateway=_FakeGateway(SOLUTIONS))
    with pytest.raises(GptActionsError):
        svc.get_solution_context("Bearer t", solution_id="  ")


def test_note_carries_knowledge_not_authorization() -> None:
    svc = SolutionCatalogService(gateway=_FakeGateway(SOLUTIONS))
    assert "not authorization" in svc.get_solution_catalog("Bearer t")["note"]
