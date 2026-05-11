from abc import ABC, abstractmethod


class AdminMetricsRepositoryPort(ABC):
    @abstractmethod
    def get_summary(self) -> dict:
        raise NotImplementedError
