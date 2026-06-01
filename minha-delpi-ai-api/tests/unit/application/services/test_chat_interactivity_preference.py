from app.application.services.chat_interactivity_preference_service import (
    ChatInteractivityPreferenceService,
)


def test_rank_boost_increases_with_usage():
    usage = {"Colocar na lousa": 3}

    assert ChatInteractivityPreferenceService.rank_boost("Colocar na lousa", usage) == -24


def test_usage_from_workspace_parses_json():
    usage = ChatInteractivityPreferenceService.usage_from_workspace(
        {
            "workingMemory": {
                "behaviorInstructions": {
                    "interactivityUsage": '{"Ver estoque": 2}',
                },
            },
        },
    )

    assert usage == {"Ver estoque": 2}
