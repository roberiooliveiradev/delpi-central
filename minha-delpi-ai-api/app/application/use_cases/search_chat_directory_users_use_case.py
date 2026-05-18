from app.domain.exceptions.authorization_exceptions import CoreApiUnavailableError
from app.domain.ports.core_api_gateway_port import CoreApiGatewayPort


class SearchChatDirectoryUsersUseCase:
    def __init__(self, core_api_gateway: CoreApiGatewayPort):
        self.core_api_gateway = core_api_gateway

    def execute(
        self,
        *,
        access_token: str,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        normalized = (query or "").strip()

        if len(normalized) < 2:
            return []

        try:
            return self.core_api_gateway.search_directory_users(
                access_token,
                query=normalized,
                limit=limit,
            )
        except CoreApiUnavailableError:
            return []
