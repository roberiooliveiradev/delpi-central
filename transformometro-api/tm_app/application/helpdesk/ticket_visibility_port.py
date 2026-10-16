"""Ticket visibility probe for room link authorization.

Minimal adapter over the existing Helpdesk BFF ``GET /tickets/{id}``
contract — same-user Bearer forward, no batch endpoint, no cached ACL.
GLPI remains the ticket authority; this port only answers whether the
*current* authenticated user can read the ticket right now.

States are the canonical domain link-state vocabulary
(``tm_app.domain.services.interaction_room_access_service``). Every
non-``visible`` outcome denies — fail closed.
"""

from __future__ import annotations

from typing import Protocol


class TicketVisibilityPort(Protocol):
    def check_ticket_visibility(self, authorization: str, ticket_key: str) -> str:
        """Resolve the link-state for one ticket under the user's session.

        Returns one of ``LINK_STATE_*``: ``visible`` | ``restricted`` |
        ``not_found`` | ``session_missing`` | ``unavailable``.
        """
        ...
