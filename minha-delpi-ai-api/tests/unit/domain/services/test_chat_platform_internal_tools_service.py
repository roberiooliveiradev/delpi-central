from app.domain.services.chat_platform_internal_tools_service import (
    PLATFORM_DIRECT_ANSWER_TOOL_NAMES,
    PLATFORM_INTERNAL_TOOL_NAMES,
    ChatPlatformInternalToolsService,
)


def test_platform_internal_tool_names_include_routes_and_rag():
    assert "get_allowed_routes" in PLATFORM_INTERNAL_TOOL_NAMES
    assert "search_knowledge_base" in PLATFORM_INTERNAL_TOOL_NAMES


def test_direct_answer_tools_are_subset_of_internal_tools():
    assert PLATFORM_DIRECT_ANSWER_TOOL_NAMES <= PLATFORM_INTERNAL_TOOL_NAMES


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
