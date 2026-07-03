from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_capabilities_detection_service import (
    ChatCapabilitiesDetectionService,
)
from app.domain.services.chat_platform_tool_selection_service import (
    ChatPlatformToolSelectionService,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService


class ToolSelectionService:
    def select_tools(
        self,
        message: str,
        *,
        attachment_context: str | None = None,
        previous_messages: list | None = None,
    ) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        selected: list[dict] = []

        if self._matches_current_user(normalized):
            selected.append(
                {
                    "name": "get_current_user",
                    "arguments": {},
                    "reason": "A pergunta solicita dados do usuário autenticado.",
                }
            )

        if self._matches_allowed_apps(normalized):
            selected.append(
                {
                    "name": "get_allowed_apps",
                    "arguments": {},
                    "reason": "A pergunta solicita aplicativos disponíveis ao usuário.",
                }
            )

        if self._matches_portal_routes(message, normalized):
            selected.append(
                {
                    "name": "get_allowed_routes",
                    "arguments": {},
                    "reason": ChatPlatformToolSelectionService.portal_routes_reason(),
                }
            )

        if ChatWebSearchIntentService.matches(message):
            web_search = ChatWebSearchIntentService.resolve(
                message,
                attachment_context=attachment_context,
                previous_messages=previous_messages,
            )

            if web_search:
                selected.append(web_search)

        return selected

    def _matches_current_user(self, value: str) -> bool:
        terms = [
            "quem sou eu",
            "meus dados",
            "meu usuário",
            "usuario atual",
            "usuário atual",
            "meu perfil",
            "qual meu email",
            "qual meu e-mail",
        ]

        return any(term in value for term in terms)

    def _matches_allowed_apps(self, value: str) -> bool:
        terms = [
            "quais apps",
            "quais aplicativos",
            "aplicativos disponíveis",
            "apps disponíveis",
            "sistemas que tenho acesso",
            "sistemas disponíveis",
            "módulos que tenho acesso",
            "modulos que tenho acesso",
            "apps que tenho acesso",
            "o que posso acessar",
            "modulos disponiveis",
        ]

        return any(term in value for term in terms)

    def _matches_portal_routes(self, message: str, normalized: str) -> bool:
        if ChatCapabilitiesDetectionService.is_api_action_routes_inquiry(message):
            return False

        return ChatPlatformToolSelectionService.matches_portal_routes_inquiry(message)
