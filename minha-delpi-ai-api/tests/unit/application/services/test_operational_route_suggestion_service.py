"""Sugestão dry-run de rotas operacionais."""

from __future__ import annotations

from app.application.services.external_actions.operational_route_suggestion_service import (
    OperationalRouteSuggestionService,
)
from app.application.use_cases.suggest_operational_routes_use_case import (
    SuggestOperationalRoutesUseCase,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class _FakeRepo:
    def __init__(self, actions: list[dict]) -> None:
        self._actions = actions

    def list_actions(self, provider_key: str | None = None) -> list[dict]:
        return list(self._actions)

    def find_candidate_actions(
        self,
        query: str,
        limit: int = 8,
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]:
        allowed = {str(a) for a in (allowed_action_ids or [])}
        q = str(query or "").lower()
        out = []
        for action in self._actions:
            if allowed and str(action.get("actionId")) not in allowed:
                continue
            hay = " ".join(
                [
                    str(action.get("summary") or ""),
                    str(action.get("description") or ""),
                    str(action.get("path") or ""),
                    str(action.get("operationId") or ""),
                ]
            ).lower()
            if q and q not in hay and "oee" not in hay and "estoque" not in hay:
                # Still return for ranker when query mentions related terms
                if "oee" in q and "oee" not in hay:
                    continue
                if "estoque" in q and "stock" not in hay and "estoque" not in hay:
                    continue
            out.append(dict(action))
            if len(out) >= limit:
                break
        return out or [dict(a) for a in self._actions[:limit] if not allowed or str(a.get("actionId")) in allowed]


class _FakeRanker:
    def rank(self, message, candidates, *, allowed_action_ids=None):
        scored = []
        q = str(message or "").lower()
        for idx, action in enumerate(candidates):
            score = 0.9 - idx * 0.05
            hay = " ".join(
                [
                    str(action.get("summary") or ""),
                    str(action.get("path") or ""),
                    str(action.get("operationId") or ""),
                ]
            ).lower()
            if any(token in hay for token in q.split() if len(token) > 2):
                score += 0.2
            row = dict(action)
            row["selectionScore"] = score
            row["selectionReason"] = ExternalActionResponseContentService.format(
                "selectionReasons",
                "routeSuggestionSemantic",
                score=f"{score:.2f}",
            )
            scored.append(row)
        scored.sort(key=lambda item: float(item.get("selectionScore") or 0), reverse=True)
        return scored


def test_route_suggestion_content_keys_exist():
    assert ExternalActionResponseContentService.get(
        "selectionReasons",
        "routeSuggestionSemantic",
    )
    assert ExternalActionResponseContentService.get(
        "selectionReasons",
        "routeSuggestionRegistry",
    )
    assert ExternalActionResponseContentService.get(
        "selectionReasons",
        "routeSuggestionEmpty",
    )


def test_operational_route_suggestion_service_ranks_by_query():
    repo = _FakeRepo(
        [
            {
                "actionId": "a1",
                "operationId": "getProductionOeeOverview",
                "path": "/production/oee/overview",
                "method": "GET",
                "summary": "OEE produção visão geral",
            },
            {
                "actionId": "a2",
                "operationId": "getProductStock",
                "path": "/products/{code}/stock",
                "method": "GET",
                "summary": "Estoque do produto",
            },
        ]
    )
    service = OperationalRouteSuggestionService(repo, semantic_ranker=_FakeRanker())
    rows = service.suggest("oee da fábrica", limit=3)
    assert rows
    assert rows[0]["operationId"] == "getProductionOeeOverview"
    assert rows[0]["actionId"] == "a1"
    assert rows[0]["reason"]
    assert rows[0]["domain"]


def test_suggest_operational_routes_use_case_envelope():
    repo = _FakeRepo(
        [
            {
                "actionId": "a1",
                "operationId": "getProductStock",
                "path": "/products/{code}/stock",
                "method": "GET",
                "summary": "Estoque",
            }
        ]
    )
    use_case = SuggestOperationalRoutesUseCase(
        OperationalRouteSuggestionService(repo, semantic_ranker=_FakeRanker())
    )
    result = use_case.execute("estoque produto", limit=5)
    assert result["ok"] is True
    assert result["query"] == "estoque produto"
    assert result["total"] >= 1
    assert result["suggestions"][0]["operationId"] == "getProductStock"
