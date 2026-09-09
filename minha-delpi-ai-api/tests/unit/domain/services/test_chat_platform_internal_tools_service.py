from app.domain.services.chat_platform_internal_tools_service import (
    PLANNER_SIGNAL_TOOL_NAMES,
    PLATFORM_DIRECT_ANSWER_TOOL_NAMES,
    PLATFORM_INTERNAL_TOOL_NAMES,
    ChatPlatformInternalToolsService,
)


def test_platform_internal_tool_names_include_routes_and_rag():
    assert "get_allowed_routes" in PLATFORM_INTERNAL_TOOL_NAMES
    assert "search_knowledge_base" in PLATFORM_INTERNAL_TOOL_NAMES


def test_direct_answer_tools_are_subset_of_internal_tools():
    assert PLATFORM_DIRECT_ANSWER_TOOL_NAMES <= PLATFORM_INTERNAL_TOOL_NAMES


def test_planner_signal_tools_are_not_platform_internal():
    assert "clarify_external_action" in PLANNER_SIGNAL_TOOL_NAMES
    assert "unknown_tool" in PLANNER_SIGNAL_TOOL_NAMES
    assert PLANNER_SIGNAL_TOOL_NAMES.isdisjoint(PLATFORM_INTERNAL_TOOL_NAMES)
    assert ChatPlatformInternalToolsService.is_non_executable_planner_signal(
        "clarify_external_action"
    )
    assert not ChatPlatformInternalToolsService.is_non_executable_planner_signal(
        "execute_external_action"
    )


def test_is_platform_direct_answer_turn():
    assert ChatPlatformInternalToolsService.is_platform_direct_answer_turn(
        [{"name": "get_allowed_routes"}]
    )
    assert not ChatPlatformInternalToolsService.is_platform_direct_answer_turn(
        [{"name": "get_allowed_routes"}, {"name": "web_search"}]
    )
    assert not ChatPlatformInternalToolsService.is_platform_direct_answer_turn(
        [{"name": "search_knowledge_base"}]
    )
