"""GET /viewer-context — identidade e capabilities do viewer humano.

Contrato congelado IMP-MFE-HOME (doc 45 §14.1; decisões D1=A e D2=A):

- ``principal_type == "user"`` obrigatório, verificado antes de qualquer
  bypass de superadmin — service tokens são minted como superadmin;
- Core é a authority de effective permissions (populadas pelo middleware
  compartilhado a partir de ``/me`` — nunca do JWT);
- exige ``controllership-finance.access`` OU
  ``controllership-finance.closing-documents.read`` (DRE-019 — o
  destinatário externo também é viewer do produto; o payload limita a
  UI, a autorização efetiva continua em cada rota);
- ``manage`` não implica ``access``; ``read`` não implica ``access``;
- ``rbac_unavailable`` (Core indisponível sem snapshot válido) falha fechado
  com 503 — nunca converte indisponibilidade em autorização local;
- leitura adere à política D1: o middleware já aplica stale ≤900s para
  reads; este handler apenas recusa quando não há snapshot válido.
"""

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response

from controllership_finance_app.config import settings

from delpi_auth.authz_core import has_permission

from controllership_finance_app.core.responses import ok

ACCESS_PERMISSION = "controllership-finance.access"
MANAGE_PERMISSION = "controllership-finance.manage"
READ_DOCUMENTS_PERMISSION = (
    "controllership-finance.closing-documents.read"
)

router = APIRouter(tags=["Viewer"])


def _display_name(user) -> str | None:
    name = (getattr(user, "name", None) or "").strip()
    return name if name and "@" not in name else None


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
    if not (
        has_permission(user, ACCESS_PERMISSION)
        or has_permission(user, READ_DOCUMENTS_PERMISSION)
    ):
        raise Exception("Forbidden")

    permissions = getattr(user, "permissions", None) or []
    is_superadmin = bool(getattr(user, "is_superadmin", False))

    return ok(
        {
            "firstName": _resolve_first_name(user),
            "displayName": _display_name(user),
            "capabilities": {
                "access": has_permission(user, ACCESS_PERMISSION),
                "manage": is_superadmin or MANAGE_PERMISSION in permissions,
                "closingDocumentsRead": has_permission(
                    user, READ_DOCUMENTS_PERMISSION
                ),
            },
        },
        operation_id="get_viewer_context",
    )


@router.get("/viewer-photo", operation_id="get_viewer_photo")
async def get_viewer_photo(request: Request):
    """Self-only read-through proxy to Core Person Profile; never stores photos."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unauthorized")
    if getattr(user, "principal_type", None) != "user":
        raise Exception("Forbidden")
    if getattr(user, "rbac_unavailable", False):
        raise Exception("Service Unavailable")
    if not has_permission(user, ACCESS_PERMISSION):
        raise Exception("Forbidden")
    bearer = request.headers.get("Authorization", "")
    if not bearer.startswith("Bearer "):
        raise Exception("Unauthorized")
    # Gateway maps /core-api/me/* to the Core service's /me/*.
    url = settings.CORE_API_BASE_URL.rstrip("/") + "/me/person-profile/photo"
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            upstream = await client.get(
                url,
                headers={"Authorization": bearer, "Accept": "image/*"},
            )
    except httpx.RequestError:
        return Response(status_code=503)
    if upstream.status_code == 404:
        return Response(status_code=404)
    if upstream.status_code in (401, 403):
        return Response(status_code=upstream.status_code)
    if upstream.status_code != 200:
        return Response(status_code=502)
    media_type = upstream.headers.get("content-type", "").split(";", 1)[0].lower()
    if media_type not in ("image/jpeg", "image/png", "image/webp"):
        return Response(status_code=502)
    if not upstream.content or len(upstream.content) > 2 * 1024 * 1024:
        return Response(status_code=502)
    return Response(
        content=upstream.content,
        media_type=media_type,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )
