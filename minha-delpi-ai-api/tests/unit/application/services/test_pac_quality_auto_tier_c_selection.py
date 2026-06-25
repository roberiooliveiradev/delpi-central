"""PAC Qualidade — seleção via autoTierCRoutes (Playbook 22 Fase A)."""

from __future__ import annotations

import pytest

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from tests.fixtures.pac_quality_regression_cases import PAC_QUALITY_SELECTION_CASES


class _PacSemanticRanker:
    """Simula ranker OpenAPI: coloca a action esperada no topo com selectionScore."""

    def __init__(self, expected_action_id: str) -> None:
        self._expected_action_id = expected_action_id

    def rank(
        self,
        message: str,
        candidates: list[dict],
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]:
        ranked: list[dict] = []

        for action in candidates:
            item = dict(action)
            item["selectionScore"] = (
                0.95 if item.get("actionId") == self._expected_action_id else 0.1
            )
            ranked.append(item)

        ranked.sort(key=lambda item: float(item.get("selectionScore") or 0), reverse=True)
        return ranked


class _PacRepository:
    def __init__(self, actions: list[dict]) -> None:
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}

        return [
            action
            for action in self.actions
            if not allowed or str(action.get("actionId")) in allowed
        ]

    def list_actions(self):
        return self.actions


def setup_module() -> None:
    configure_domain_infrastructure_ports()


@pytest.mark.parametrize("case", PAC_QUALITY_SELECTION_CASES)
def test_pac_quality_selection_uses_auto_tier_c(case: dict) -> None:
    service = ExternalActionSelectionService(
        _PacRepository(case["actions"]),
        semantic_ranker=_PacSemanticRanker(case["expected_action_id"]),
    )
    allowed = [action["actionId"] for action in case["actions"]]

    selected = service.select_action(
        case["message"],
        allowed_action_ids=allowed,
        previous_messages=case.get("previous_messages"),
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == case["expected_action_id"]
