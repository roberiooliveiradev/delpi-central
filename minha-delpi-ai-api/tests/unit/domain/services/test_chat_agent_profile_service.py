from app.domain.services.chat_agent_profile_service import ChatAgentProfileService


def test_profile_uses_published_agent_fields():
    profile = ChatAgentProfileService.from_workspace(
        {
            "agentId": "11111111-1111-4111-8111-111111111111",
            "agent": {
                "name": "Agente Minha DELPI",
                "description": "Assistente corporativo geral da Minha DELPI.",
                "category": "general",
                "metadata": {},
            },
            "agentPrompt": "Você é o assistente corporativo Minha DELPI Chat.",
        }
    )

    assert profile.name == "Agente Minha DELPI"
    assert "corporativo" in profile.self_description


def test_profile_falls_back_to_system_prompt_excerpt():
    profile = ChatAgentProfileService.from_workspace(
        {
            "agentId": "11111111-1111-4111-8111-111111111111",
            "agent": {"name": "Meu Agente", "description": "", "metadata": {}},
            "agentPrompt": (
                "Você é um especialista em logística. "
                "Priorize dados operacionais e responda em português."
            ),
        }
    )

    assert profile.self_description.startswith("Você é um especialista em logística")


def test_custom_identity_override_from_metadata():
    profile = ChatAgentProfileService.from_workspace(
        {
            "agent": {
                "name": "Agente X",
                "description": "Descrição curta.",
                "metadata": {
                    "identity": {
                        "responses": {
                            "who": "Custom: sou {agent_name} — {agent_description}",
                        }
                    }
                },
            }
        }
    )

    custom = ChatAgentProfileService.custom_identity_response(profile, "who")

    assert custom == "Custom: sou Agente X — Descrição curta."
