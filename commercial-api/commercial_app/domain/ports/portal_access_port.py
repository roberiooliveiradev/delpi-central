from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence


class PortalAccessPort(ABC):
    def has_commercial_portal_access(self, user_id: str) -> bool:
        uid = str(user_id or "").strip()
        if not uid:
            return False
        return bool(self.has_commercial_portal_access_batch([uid]).get(uid, False))

    @abstractmethod
    def has_commercial_portal_access_batch(
        self,
        user_ids: Sequence[str],
    ) -> dict[str, bool]:
        """Mapa user_id → acesso ao app commercial (batch-friendly)."""
        raise NotImplementedError
