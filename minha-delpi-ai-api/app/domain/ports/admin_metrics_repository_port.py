from abc import ABC, abstractmethod


class AdminMetricsRepositoryPort(ABC):
    @abstractmethod
    def get_summary(self, *, hours: int = 24) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_timeseries(self, *, hours: int = 168, bucket_hours: int = 24) -> dict:
        raise NotImplementedError
