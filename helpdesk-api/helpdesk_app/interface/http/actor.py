from delpi_auth.authz_core import has_permission
from fastapi import Request

from helpdesk_app.domain.errors import PortalForbidden
from helpdesk_app.domain.models import Actor

ACCESS_PERMISSION = "helpdesk.access"


def require_actor(request: Request) -> Actor:
    user = request.state.user
    if not has_permission(user, ACCESS_PERMISSION):
        raise PortalForbidden("Sem permissão para Meus Chamados de TI.")
    subject = str(getattr(user, "sub", None) or getattr(user, "id", "") or "")
    if not subject:
        raise PortalForbidden("Sessão sem sujeito.")
    return Actor(subject=subject)
