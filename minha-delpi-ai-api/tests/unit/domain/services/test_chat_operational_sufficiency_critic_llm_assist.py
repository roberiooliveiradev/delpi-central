from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_operational_sufficiency_critic_content_service import (
    ChatOperationalSufficiencyCriticContentService,
)
from app.domain.services.chat_operational_sufficiency_critic_service import (
    ChatOperationalSufficiencyCriticService,
    SufficiencyVerdict,
)


def test_llm_assist_flag_off_never_calls_classifier(monkeypatch):
    calls = {"n": 0}

    def classify(_payload):
        calls["n"] += 1
        return {"verdict": "need_follow_up", "followUpPlanId": "stock_low_needs_sales"}

    monkeypatch.setattr(
        ChatOperationalSufficiencyCriticContentService,
        "llm_assist_enabled",
        classmethod(lambda cls: False),
    )

    verdict = ChatOperationalSufficiencyCriticService.evaluate(
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "path": "/x", "emptyResult": True},
            }
        ],
        remaining_slots=1,
        llm_classify=classify,
    )
    assert calls["n"] == 0
    assert verdict.action == "sufficient"


def test_llm_assist_valid_plan_id_executes(monkeypatch):
    monkeypatch.setattr(
        ChatOperationalSufficiencyCriticContentService,
        "llm_assist_enabled",
        classmethod(lambda cls: True),
    )

    verdict = ChatOperationalSufficiencyCriticService.evaluate(
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/x/other",
                    "emptyResult": True,
                },
            }
        ],
        remaining_slots=2,
        llm_classify=lambda _p: {
            "verdict": "need_follow_up",
            "followUpPlanId": "stock_low_needs_sales",
            "clarifyKey": None,
        },
    )
    assert verdict.action == "execute"
    assert verdict.plan_id == "stock_low_needs_sales"
    assert "productSales" in verdict.follow_up_route_ids


def test_llm_assist_invalid_plan_id_falls_back(monkeypatch):
    monkeypatch.setattr(
        ChatOperationalSufficiencyCriticContentService,
        "llm_assist_enabled",
        classmethod(lambda cls: True),
    )
    fallback = SufficiencyVerdict(action="sufficient", reason_key="sufficient")
    resolved = ChatOperationalSufficiencyCriticService.resolve_from_llm_classification(
        {"verdict": "need_follow_up", "followUpPlanId": "not_a_real_plan"},
        remaining_slots=2,
        fallback=fallback,
    )
    assert resolved.reason_key == "invalidLlmPlan"
    assert resolved.action == "sufficient"
