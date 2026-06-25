from app.domain.services.chat_quality_action_plans_access_service import (
    ChatQualityActionPlansAccessService,
)


class _PacActionRepository:
    def __init__(self, actions: list[dict]) -> None:
        self._actions = actions

    def list_actions(self):
        return self._actions


def test_read_only_when_only_get_pac_actions_allowed():
    repository = _PacActionRepository(
        [
            {
                "actionId": "pac-dashboard",
                "path": "/quality/action-plans/dashboard",
                "method": "GET",
                "sensitivity": "read",
            },
            {
                "actionId": "pac-create",
                "path": "/quality/action-plans",
                "method": "POST",
                "sensitivity": "write",
            },
        ]
    )
    ChatQualityActionPlansAccessService.configure_external_action_repository(repository)

    assert (
        ChatQualityActionPlansAccessService.resolve_read_only_mode(
            ["pac-dashboard"]
        )
        is True
    )
    assert (
        ChatQualityActionPlansAccessService.resolve_read_only_mode(
            ["pac-dashboard", "pac-create"]
        )
        is False
    )


def test_read_only_from_action_id_markers_without_repository():
    ChatQualityActionPlansAccessService.configure_external_action_repository(None)

    assert (
        ChatQualityActionPlansAccessService.resolve_read_only_mode(
            ["list_quality_action_plans"]
        )
        is True
    )
    assert (
        ChatQualityActionPlansAccessService.resolve_read_only_mode(
            ["list_quality_action_plans", "create_quality_action_plan"]
        )
        is False
    )


def test_resolve_runtime_flags_sets_read_only_for_leadership_profile():
    from app.domain.skills.chat_skill_registry import ChatSkillRegistry

    repository = _PacActionRepository(
        [
            {
                "actionId": "list_quality_action_plans",
                "path": "/quality/action-plans",
                "method": "GET",
                "sensitivity": "read",
            }
        ]
    )
    ChatQualityActionPlansAccessService.configure_external_action_repository(repository)

    flags = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata={},
        allowed_action_ids=["list_quality_action_plans"],
        has_agent=True,
    )

    assert flags["qualityActionPlans"] is True
    assert flags["qualityActionPlansReadOnly"] is True
