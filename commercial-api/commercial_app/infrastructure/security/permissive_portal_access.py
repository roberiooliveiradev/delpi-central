from __future__ import annotations

from commercial_app.domain.ports.portal_access_port import PortalAccessPort


class PermissivePortalAccessPort(PortalAccessPort):
    """Default até existir lookup RBAC no core — sempre permite."""

    def has_commercial_portal_access(self, user_id: str) -> bool:
        return True
