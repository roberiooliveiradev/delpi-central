from __future__ import annotations

from abc import ABC, abstractmethod


class PortalAccessPort(ABC):
    @abstractmethod
    def has_commercial_portal_access(self, user_id: str) -> bool:
        raise NotImplementedError
