from app.domain.services.chat_platform_tools_content_service import (
    ChatPlatformToolsContentService,
)


def test_platform_tools_bundle_loads_routes_title():
    title = ChatPlatformToolsContentService.format(
        "directAnswer",
        "routes",
        "title",
        count="3",
    )

    assert "Rotas autorizadas" in title
    assert "3" in title
