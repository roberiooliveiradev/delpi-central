# app/domain/ports/ppm/ppm_query_repository_port.py

from abc import ABC, abstractmethod


class PpmQueryRepositoryPort(ABC):

    @abstractmethod
    def get_summary(self, request):
        raise NotImplementedError

    @abstractmethod
    def list_items(self, request):
        raise NotImplementedError