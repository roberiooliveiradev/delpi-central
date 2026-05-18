from abc import ABC, abstractmethod


class CoreApiGatewayPort(ABC):
    @abstractmethod
    def get_me(self, access_token: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_apps(self, access_token: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_routes(self, access_token: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def search_directory_users(
        self,
        access_token: str,
        *,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def lookup_directory_users(
        self,
        access_token: str,
        user_ids: list[str],
    ) -> list[dict]:
        raise NotImplementedError
