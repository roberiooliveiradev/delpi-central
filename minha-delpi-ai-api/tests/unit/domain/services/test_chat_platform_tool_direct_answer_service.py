from app.domain.services.chat_platform_tool_direct_answer_service import (
    ChatPlatformToolDirectAnswerService,
)


def test_format_allowed_routes_lists_real_paths_only():
    data = [
        {
            "appId": "minha-delpi",
            "appName": "Minha DELPI",
            "path": "/apps/minha-delpi/chat",
            "label": "Chat",
        },
        {
            "appId": "maintenance",
            "appName": "Manutenção",
            "path": "/apps/maintenance/ferramentas",
            "label": "Ferramentas",
        },
    ]

    answer = ChatPlatformToolDirectAnswerService.format(
        "get_allowed_routes",
        data=data,
        metadata={"count": 2, "truncated": False},
        message="quais rotas vc acessa",
    )

    assert answer is not None
    assert "/apps/minha-delpi/chat" in answer
    assert "/apps/maintenance/ferramentas" in answer
    assert "/api/v1/chat" not in answer
    assert "portal DELPI" in answer


def test_format_allowed_routes_empty():
    answer = ChatPlatformToolDirectAnswerService.format(
        "get_allowed_routes",
        data=[],
        metadata={"count": 0},
    )

    assert answer is not None
    assert "Não encontrei rotas" in answer


def test_format_allowed_routes_truncated_notice():
    data = [
        {
            "appName": "Minha DELPI",
            "path": "/apps/minha-delpi/chat",
            "label": "Chat",
        }
    ]

    answer = ChatPlatformToolDirectAnswerService.format(
        "get_allowed_routes",
        data=data,
        metadata={"count": 61, "truncated": True},
    )

    assert answer is not None
    assert "61" in answer
    assert "primeiras" in answer


def test_format_allowed_apps():
    data = [
        {
            "id": "minha-delpi",
            "name": "Minha DELPI",
            "basePath": "/apps/minha-delpi",
            "routeCount": 12,
        }
    ]

    answer = ChatPlatformToolDirectAnswerService.format(
        "get_allowed_apps",
        data=data,
        metadata={"count": 1},
    )

    assert answer is not None
    assert "Minha DELPI" in answer
    assert "/apps/minha-delpi" in answer
    assert "12 rota" in answer


def test_format_current_user():
    answer = ChatPlatformToolDirectAnswerService.format(
        "get_current_user",
        data={
            "name": "Robério",
            "email": "rober@delpi.com.br",
            "isSuperadmin": True,
        },
        metadata={"source": "core-api:/me"},
    )

    assert answer is not None
    assert "Robério" in answer
    assert "rober@delpi.com.br" in answer
    assert "Superadministrador" in answer


def test_format_ignores_unknown_tool():
    assert (
        ChatPlatformToolDirectAnswerService.format(
            "search_knowledge_base",
            data={"items": []},
            metadata={},
        )
        is None
    )
