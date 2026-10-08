"""Portal-facing product-guide read surface — same registry as TÉO.

Serves the help projection (public fields only) on the authenticated
domain surface so Portal Help and TÉO share one semantic authority.
Read-only; no writes, no AuthZ changes — transformometro.access gate
only. The GPT Actions façade (`gpt_get_product_guide`) stays the
external-agent surface; this route is the Portal surface.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from tm_app.application.product_guide.product_guide_service import (
    ProductGuideNotFoundError,
    ProductGuideService,
)
from tm_app.application.security.authorization_policy import (
    AuthorizationDenied,
    TransformometroAuthorizationPolicy,
)
from tm_app.core.responses import fail, ok

router = APIRouter(
    prefix="/transformometro/product-guides",
    tags=["Transformômetro Product Guides"],
)
_service = ProductGuideService()
_authz = TransformometroAuthorizationPolicy()


def _require_access(request: Request):
    user = getattr(request.state, "user", None)
    try:
        _authz.require_access(user)
    except AuthorizationDenied as exc:
        return fail(str(exc), exc.status_code)
    return None


@router.get("", operation_id="list_product_guide_topics")
def list_topics(request: Request, view: str | None = None):
    """Index of guide topics; ``?view=help`` returns full help views."""
    if denied := _require_access(request):
        return denied
    if view == "help":
        return ok(_service.get_help_view())
    return ok(_service.get_product_guide())


@router.get("/{topic}", operation_id="get_product_guide_topic")
def get_topic(request: Request, topic: str):
    """Single guide as help view (public fields only)."""
    if denied := _require_access(request):
        return denied
    try:
        return ok(_service.get_help_view(topic=topic))
    except ProductGuideNotFoundError as exc:
        return fail(str(exc), 404)
