from app.domain.services.chat_agent_personality_service import ChatAgentPersonalityService
from app.domain.services.chat_agent_profile_service import ChatAgentProfile


def test_from_profile_uses_defaults():
    profile = ChatAgentProfile(
        name="Agente",
        description="",
        system_prompt=None,
        category=None,
        metadata={},
        platform_name="Minha DELPI",
    )

    personality = ChatAgentPersonalityService.from_profile(profile)

    assert personality.humor_level == 2
    assert personality.suggest_follow_ups is True


def test_from_profile_reads_metadata():
    profile = ChatAgentProfile(
        name="Agente",
        description="",
        system_prompt=None,
        category=None,
        metadata={
            "personality": {
                "humorLevel": 0,
                "suggestFollowUps": False,
                "tone": "neutro",
            },
        },
        platform_name="Minha DELPI",
    )

    personality = ChatAgentPersonalityService.from_profile(profile)

    assert personality.humor_level == 0
    assert personality.suggest_follow_ups is False
    assert personality.tone == "neutro"


def test_effective_humor_reduced_on_high_risk():
    profile = ChatAgentPersonalityService.from_profile(
        ChatAgentProfile(
            name="",
            description="",
            system_prompt=None,
            category=None,
            metadata={"personality": {"humorLevel": 3}},
            platform_name="Minha DELPI",
        )
    )

    assert ChatAgentPersonalityService.effective_humor_level(profile, risk_level=3) == 0
