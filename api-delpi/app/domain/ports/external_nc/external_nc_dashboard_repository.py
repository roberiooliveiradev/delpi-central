# app/domain/ports/external_nc/external_nc_dashboard_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod


class ExternalNcDashboardRepositoryPort(ABC):
    @abstractmethod
    def get_summary(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_by_supplier(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_by_cause(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_overdue_actions(self) -> list[dict]:
        raise NotImplementedError