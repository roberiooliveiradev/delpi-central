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
