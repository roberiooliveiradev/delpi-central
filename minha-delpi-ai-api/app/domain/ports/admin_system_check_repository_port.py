from abc import ABC, abstractmethod


class AdminSystemCheckRepositoryPort(ABC):
    @abstractmethod
    def check(self) -> dict:
        raise NotImplementedError
