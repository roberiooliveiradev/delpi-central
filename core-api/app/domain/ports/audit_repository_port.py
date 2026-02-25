# app/domain/ports/audit_repository_port.py

from abc import ABC, abstractmethod
from typing import Dict, Any


class AuditRepositoryPort(ABC):

    @abstractmethod
    def log(self, data: Dict[str, Any]) -> None:
        ...