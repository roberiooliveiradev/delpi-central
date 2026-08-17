from __future__ import annotations

from typing import Sequence

from commercial_app.domain.ports.portal_access_port import PortalAccessPort


class PermissivePortalAccessPort(PortalAccessPort):
    """Stub para testes / ambiente sem core-api — sempre permite."""

    def has_commercial_portal_access_batch(
        self,
        user_ids: Sequence[str],
    ) -> dict[str, bool]:
        return {
            str(user_id).strip(): True
            for user_id in user_ids
            if str(user_id or "").strip()
        }
