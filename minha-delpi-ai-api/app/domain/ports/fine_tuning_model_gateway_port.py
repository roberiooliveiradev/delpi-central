from __future__ import annotations

from abc import ABC, abstractmethod


class FineTuningModelGatewayPort(ABC):
    @abstractmethod
    def supports_local_deploy(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_from_modelfile(self, *, name: str, modelfile: str) -> dict:
        raise NotImplementedError
