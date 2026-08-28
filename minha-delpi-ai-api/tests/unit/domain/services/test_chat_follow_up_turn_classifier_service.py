"""Classificador residual de follow-up via port."""

from __future__ import annotations

from app.domain.ports.follow_up_turn_classifier_port import FollowUpTurnClassifierPort
from app.domain.services.chat_follow_up_turn_classifier_service import (
    ChatFollowUpTurnClassifierService,
)
from app.domain.services.chat_follow_up_turn_interpretation_service import (
    ChatFollowUpTurnInterpretationService,
)


class _FakeClassifier(FollowUpTurnClassifierPort):
    def __init__(self, label: str | None = None, *, raise_error: bool = False):
        self.label = label
        self.raise_error = raise_error

    def classify(self, message, last_action_summary=None):
        if self.raise_error:
            raise RuntimeError("classifier timeout")
        return self.label


def test_fake_port_revise_period_reenters_contract():
    ChatFollowUpTurnClassifierService.configure(_FakeClassifier("revise_period"))
    try:
        base = ChatFollowUpTurnInterpretationService.interpret(
            message="e no mesmo intervalo do ano passado?",
            last_action={
                "path": "/financial/rol",
                "params": {
                    "start_date": "01-08-2026",
                    "end_date": "28-08-2026",
                },
            },
            last_result_excerpt={"title": "ROL"},
        )
        # Determinístico pode já ter pego período; forçamos apply do label residual.
        labeled = ChatFollowUpTurnInterpretationService.apply_classifier_label(
            base
            if base.continuity_mode == "allow_discovery"
            else ChatFollowUpTurnInterpretationService.interpret(
                message="ainda sobre aquilo",
                last_action={
                    "path": "/financial/rol",
                    "params": {
                        "start_date": "01-08-2026",
                        "end_date": "28-08-2026",
                    },
                },
                last_result_excerpt={"title": "ROL"},
            ),
            "revise_period",
            message="ainda sobre aquilo",
            last_action={
                "path": "/financial/rol",
                "params": {
                    "start_date": "01-08-2026",
                    "end_date": "28-08-2026",
                },
            },
        )
        assert labeled.decision == "revise_last_query"
        assert labeled.continuity_mode == "consume_last_action"
        assert labeled.slot_delta.get("period") == "previous_year_same_range"
        assert labeled.slot_delta.get("start_date") == "01-08-2025"
        assert ChatFollowUpTurnClassifierService.classify("x", {}) == "revise_period"
    finally:
        ChatFollowUpTurnClassifierService.configure(None)


def test_port_raise_keeps_allow_discovery():
    ChatFollowUpTurnClassifierService.configure(_FakeClassifier(raise_error=True))
    try:
        assert ChatFollowUpTurnClassifierService.classify("x", {}) is None
        base = ChatFollowUpTurnInterpretationService.interpret(
            message="ainda sobre aquilo",
            last_action={"path": "/financial/rol", "params": {}},
            last_result_excerpt={"title": "ROL"},
        )
        assert base.allows_parallel_discovery()
    finally:
        ChatFollowUpTurnClassifierService.configure(None)
