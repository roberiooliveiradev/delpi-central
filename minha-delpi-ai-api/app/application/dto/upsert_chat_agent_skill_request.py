from dataclasses import dataclass


@dataclass
class UpsertChatAgentSkillRequest:
    user_id: str
    agent_id: str
    skill_key: str
    enabled: bool
    can_manage_official_agents: bool = False
