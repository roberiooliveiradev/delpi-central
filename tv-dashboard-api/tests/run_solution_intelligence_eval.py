"""P6 eval runner — executes the frozen corpus against search_data_routes.

Usage: python -m tests.run_solution_intelligence_eval [baseline|candidate]

Same corpus in both modes; the mode only labels the report. The stub
gateway records how many times Core would have been called.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

from tv_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
)
from tv_app.application.gpt_actions.errors import GptActionsError
from tests.solution_intelligence_corpus import (
    CORE_5XX,
    CORE_INVALID,
    CORE_NO_AUTH,
    CORE_TIMEOUT,
    CORE_UNAUTHORIZED,
    P6_CORPUS,
)


class _SuggestStub:
    def __init__(self, suggestions):
        self._suggestions = suggestions

    def suggest(self, *, query, limit, category=None):
        return {"suggestions": list(self._suggestions)}


class _GatewayStub:
    """Records calls; returns the scripted Core result."""

    def __init__(self, result):
        self._result = result
        self.calls = 0
        self.authorizations = []

    def list_solutions(self, authorization):
        self.calls += 1
        self.authorizations.append(authorization)
        if self._result == CORE_TIMEOUT:
            raise GptActionsError(
                "timeout", 502, {"error_kind": "upstream_unavailable"}
            )
        if self._result == CORE_5XX:
            raise GptActionsError(
                "5xx", 502, {"error_kind": "upstream_error", "status": 500}
            )
        if self._result == CORE_UNAUTHORIZED:
            raise GptActionsError(
                "unauthorized", 502,
                {"error_kind": "upstream_error", "status": 401},
            )
        if self._result == CORE_INVALID:
            # Mirrors the real gateway: malformed payload fails closed at
            # the projection boundary instead of reaching the classifier.
            raise GptActionsError(
                "Contrato de soluções inválido.",
                code="INVALID_CONTRACT",
                status_code=502,
                details={"error_kind": "invalid_contract"},
            )
        return list(self._result or [])


def evaluate_case(case: dict) -> dict:
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=MagicMock(), commit=MagicMock(),
        suggest=_SuggestStub(case["tv_routes"]),
    )
    gateway = _GatewayStub(case["core_result"])
    # Inject the stub only if the dispatch already exposes the seam
    # (baseline: attribute ignored → records zero enrichment).
    dispatch._solutions = gateway
    auth = None if case["core_result"] == CORE_NO_AUTH else "Bearer user-token"
    kwargs = {"user": SimpleNamespace(
        is_superadmin=True, permissions=[], id="eval-actor"
    ), "query": case["query"], "limit": 8}
    try:
        result = dispatch.search_data_routes(authorization=auth, **kwargs)
    except TypeError:
        result = dispatch.search_data_routes(**kwargs)
    except GptActionsError as exc:
        return {
            "id": case["id"],
            "raised": True,
            "error": str(exc),
            "core_calls": gateway.calls,
        }
    intel = result.get("solutionIntelligence") or {}
    return {
        "id": case["id"],
        "raised": False,
        "total": result.get("total"),
        "miss_invariant": bool(result.get("searchMissDoesNotProveAbsence")),
        "gap": intel.get("gapClassification"),
        "candidates": [c.get("id") for c in intel.get("candidates") or []],
        "candidate_keys": sorted(
            {k for c in intel.get("candidates") or [] for k in c}
        ),
        "core_calls": gateway.calls,
        "authorizations": list(gateway.authorizations),
    }


def run(mode: str) -> dict:
    rows = [evaluate_case(c) for c in P6_CORPUS]
    print(f"MODE={mode}")
    for row in rows:
        print(row)
    return {"mode": mode, "rows": rows}


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "candidate")
