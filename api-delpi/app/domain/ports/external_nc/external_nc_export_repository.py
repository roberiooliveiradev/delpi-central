# app/domain/ports/external_nc/external_nc_export_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod


class ExternalNcExportRepositoryPort(ABC):
    @abstractmethod
    def get_nonconformity_export_payload(self, nonconformity_id: str) -> dict | None:
        raise NotImplementedError