import logging

from delpi_auth.authz_core import has_permission
from fastapi import Request

from helpdesk_app.domain.errors import PortalForbidden
from helpdesk_app.domain.models import Actor

logger = logging.getLogger("helpdesk.actor")

ACCESS_PERMISSION = "helpdesk.access"


def require_actor(request: Request) -> Actor:
    """AuthZ gate for every helpdesk route — also the canonical identity-projection
    trigger: reconcile runs on the first authenticated access (memoized), never
    blocks the request and never turns login success into fake parity."""
    user = request.state.user
    if not has_permission(user, ACCESS_PERMISSION):
        raise PortalForbidden("Sem permissão para Meus Chamados de TI.")
    subject = str(getattr(user, "sub", None) or getattr(user, "id", "") or "")
    if not subject:
        raise PortalForbidden("Sessão sem sujeito.")
    email = str(getattr(user, "email", "") or "")
    actor = Actor(
        subject=subject,
        email=email,
        name=str(getattr(user, "name", "") or ""),
        first_name=str(getattr(user, "given_name", "") or ""),
        last_name=str(getattr(user, "family_name", "") or ""),
    )
    sync = getattr(request.app.state, "profile_sync", None)
    if sync is not None:
        try:
            sync.ensure_profile(actor)
        except Exception:
            logger.exception("helpdesk_profile_sync_entry_failed subject=%s", subject)
    return actor
