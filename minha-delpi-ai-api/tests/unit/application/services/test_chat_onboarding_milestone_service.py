from app.application.services.chat_onboarding_milestone_service import (
    ChatOnboardingMilestoneService,
)


def test_first_operational_milestone_on_tool_success():
    celebrations = ChatOnboardingMilestoneService.detect_new_milestones(
        previous_messages=[],
        pipeline_stages=["ingress", "post_tool", "intent:operational_query"],
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "path": "/products/10080001"},
            }
        ],
    )

    assert len(celebrations) == 1
    assert celebrations[0]["id"] == "first_operational_query"


def test_milestone_not_repeated_from_history():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "onboardingMilestonesAchieved": ["first_operational_query"],
            },
        },
    ]

    celebrations = ChatOnboardingMilestoneService.detect_new_milestones(
        previous_messages=history,
        pipeline_stages=["post_tool"],
        tool_calls=[
            {"name": "execute_external_action", "metadata": {"ok": True}},
        ],
    )

    assert celebrations == []


def test_first_canvas_milestone():
    celebrations = ChatOnboardingMilestoneService.detect_new_milestones(
        previous_messages=[],
        pipeline_stages=["canvas"],
        tool_calls=[],
        canvas_open=True,
    )

    assert celebrations[0]["id"] == "first_canvas"
