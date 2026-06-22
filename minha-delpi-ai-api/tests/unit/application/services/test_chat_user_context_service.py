from app.application.services.chat_user_context_service import ChatUserContextService


class StubCoreGateway:
    def __init__(self, *, me: dict, profile: dict | None = None, apps: list | None = None):
        self.me = me
        self.profile = profile
        self.apps = apps or []

    def get_me(self, access_token: str) -> dict:
        return self.me

    def get_access_profile(self, access_token: str) -> dict:
        return self.profile or {}

    def get_apps(self, access_token: str) -> list[dict]:
        return self.apps


def test_find_role_in_message_matches_partial_name():
    roles = [{"name": "Chat Full"}, {"name": "Transforma Mais"}]
    matched = ChatUserContextService._find_role_in_message(
        "quais as permissões de chat full?",
        roles,
    )
    assert matched["name"] == "Chat Full"


def test_format_role_detail_answer_lists_permissions_and_apps():
    role = {
        "name": "Chat Full",
        "description": "Acesso completo ao chat.",
        "sources": [{"type": "direct"}],
        "permissions": [
            {
                "code": "minha-delpi.chat.access",
                "name": "Acessar chat",
                "description": "Usar o Minha DELPI Chat",
                "module": "minha-delpi",
            }
        ],
        "apps": [
            {
                "name": "Minha DELPI",
                "routes": [
                    {
                        "label": "Chat",
                        "path": "/chat",
                        "permission": "minha-delpi.chat.access",
                    }
                ],
            }
        ],
    }

    answer = ChatUserContextService._format_role_detail_answer(role)

    assert "Chat Full" in answer
    assert "minha-delpi.chat.access" in answer
    assert "Minha DELPI" in answer
    assert "Chat" in answer


def test_core_api_url_joins_me_consents_without_duplicate_prefix():
    from app.application.services.chat_user_context_service import ChatUserContextService
    from app.infrastructure.config.settings import Settings

    original = Settings.CORE_API_BASE_URL
    try:
        Settings.CORE_API_BASE_URL = "http://core-api:8000"
        assert (
            ChatUserContextService._core_api_url("me/consents")
            == "http://core-api:8000/me/consents"
        )
        Settings.CORE_API_BASE_URL = "http://localhost/core-api"
        assert (
            ChatUserContextService._core_api_url("me/consents")
            == "http://localhost/core-api/me/consents"
        )
    finally:
        Settings.CORE_API_BASE_URL = original


def test_compose_llm_synthesis_user_message_includes_profile_facts():
    from app.composition.content_composer import configure_domain_infrastructure_ports
    from app.domain.services.chat_user_profile_llm_synthesis_service import (
        ChatUserProfileLlmSynthesisService,
    )

    configure_domain_infrastructure_ports()

    composed = ChatUserProfileLlmSynthesisService.compose_user_message(
        profile_facts="- **Nome:** Ana\n- **Email:** ana@delpi.com.br",
        question="quem sou eu?",
    )

    assert "Ana" in composed
    assert "ana@delpi.com.br" in composed
    assert "quem sou eu?" in composed.lower()


def test_build_user_context_includes_pii_for_identity_when_strip_enabled():
    gateway = StubCoreGateway(
        me={
            "authorized": True,
            "name": "Robério Oliveira",
            "email": "engenharia6@delpi.com.br",
            "is_superadmin": True,
            "roles": ["Chat Full"],
            "permissions": ["minha-delpi.chat.access"],
        },
        profile={"effectiveApps": [{"label": "Chat", "name": "Minha DELPI Chat"}]},
    )
    service = ChatUserContextService(gateway)
    service._should_strip_pii = lambda _token: True  # type: ignore[method-assign]

    without_pii = service.build_user_context("token")
    with_pii = service.build_user_context("token", include_pii_for_identity=True)

    assert "Robério Oliveira" not in without_pii
    assert "engenharia6@delpi.com.br" not in without_pii
    assert "Robério Oliveira" in with_pii
    assert "engenharia6@delpi.com.br" in with_pii


def test_build_direct_answer_keeps_name_email_for_identity_question():
    gateway = StubCoreGateway(
        me={
            "authorized": True,
            "name": "Robério Oliveira",
            "email": "engenharia6@delpi.com.br",
            "is_superadmin": True,
            "roles": [],
            "permissions": [],
        },
        profile={"effectiveApps": [{"label": "Chat", "name": "Minha DELPI Chat"}]},
    )
    service = ChatUserContextService(gateway)
    service._should_strip_pii = lambda _token: True  # type: ignore[method-assign]

    answer = service.build_direct_answer("token", "quem sou eu?")

    assert answer is not None
    assert "Robério Oliveira" in answer
    assert "engenharia6@delpi.com.br" in answer
    assert "Não informado" not in answer


def test_build_direct_answer_for_role_permissions_without_llm():
    gateway = StubCoreGateway(
        me={
            "authorized": True,
            "name": "Robério",
            "email": "rob@delpi.com",
            "roles": ["Chat Full"],
            "permissions": ["minha-delpi.chat.access"],
        },
        profile={
            "roles": [
                {
                    "name": "Chat Full",
                    "permissions": [{"code": "minha-delpi.chat.access", "name": "Acessar"}],
                    "apps": [],
                    "sources": [{"type": "direct"}],
                }
            ],
            "effectivePermissions": ["minha-delpi.chat.access"],
            "effectiveApps": [],
        },
    )
    service = ChatUserContextService(gateway)

    answer = service.build_direct_answer("token", "quais as permissões de chat full?")

    assert answer is not None
    assert "Chat Full" in answer
    assert "minha-delpi.chat.access" in answer
