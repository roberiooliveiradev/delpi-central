"""GET /viewer-context — identidade e capabilities do viewer humano.

Contrato congelado IMP-MFE-HOME (doc 45 §14.1; decisões D1=A e D2=A):

- ``principal_type == "user"`` obrigatório, verificado antes de qualquer
  bypass de superadmin — service tokens são minted como superadmin;
- Core é a authority de effective permissions (populadas pelo middleware
  compartilhado a partir de ``/me`` — nunca do JWT);
- exige ``controllership-finance.access``; ``manage`` não implica ``access``;
- ``rbac_unavailable`` (Core indisponível sem snapshot válido) falha fechado
  com 503 — nunca converte indisponibilidade em autorização local;
- leitura adere à política D1: o middleware já aplica stale ≤900s para
  reads; este handler apenas recusa quando não há snapshot válido.
"""

from fastapi import APIRouter, Request

from delpi_auth.authz_core import has_permission

from controllership_finance_app.core.responses import ok

ACCESS_PERMISSION = "controllership-finance.access"
MANAGE_PERMISSION = "controllership-finance.manage"

router = APIRouter(tags=["Viewer"])


def _resolve_first_name(user) -> str | None:
    """Primeiro nome sem inventar identidade.

    Usa o claim ``given_name`` populado pelo middleware; fallback para o
    primeiro token do display name. Retorna ``None`` quando só existe um
    e-mail — a UI cai na saudação genérica em vez de exibir o endereço.
    """
    given_name = (getattr(user, "given_name", None) or "").strip()
    if given_name:
        return given_name
    display_name = (getattr(user, "name", None) or "").strip()
    if not display_name or "@" in display_name:
        return None
    return display_name.split(" ", 1)[0].strip() or None


@router.get("/viewer-context", operation_id="get_viewer_context")
def get_viewer_context(request: Request):
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unauthorized")
    if getattr(user, "principal_type", None) != "user":
        raise Exception("Forbidden")
    if getattr(user, "rbac_unavailable", False):
        raise Exception("Service Unavailable")
    if not has_permission(user, ACCESS_PERMISSION):
        raise Exception("Forbidden")

    permissions = getattr(user, "permissions", None) or []
    is_superadmin = bool(getattr(user, "is_superadmin", False))

    return ok(
        {
            "firstName": _resolve_first_name(user),
            "capabilities": {
                "access": True,
                "manage": is_superadmin or MANAGE_PERMISSION in permissions,
            },
        },
        operation_id="get_viewer_context",
    )
