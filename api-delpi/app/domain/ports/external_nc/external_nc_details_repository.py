# app/domain/ports/external_nc/external_nc_details_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod


class ExternalNcDetailsRepositoryPort(ABC):
    @abstractmethod
    def get_full_details(self, nonconformity_id: str) -> dict | None:
        raise NotImplementedError