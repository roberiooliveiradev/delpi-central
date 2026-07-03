from app.domain.services.chat_platform_tool_selection_service import (
    ChatPlatformToolSelectionService,
)


def test_portal_routes_terms_loaded_from_json():
    terms = ChatPlatformToolSelectionService.portal_routes_terms()

    assert "menus do portal" in terms
    assert "quais rotas" not in terms


def test_matches_portal_routes_inquiry():
    assert ChatPlatformToolSelectionService.matches_portal_routes_inquiry(
        "quais menus do portal estão autorizados?"
    )
    assert not ChatPlatformToolSelectionService.matches_portal_routes_inquiry(
        "quais rotas vc acessa?"
    )
