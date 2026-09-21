from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from helpdesk_app.interface.http.actor import require_actor
from helpdesk_app.domain.errors import HelpdeskError

router = APIRouter(tags=["Helpdesk OAuth"])


def _services(request: Request):
    return request.app.state.oauth


@router.get("/auth/glpi/start")
def start_glpi(request: Request):
    actor = require_actor(request)
    url = _services(request).start(actor.subject)
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return {"authorize_url": url}
    response = RedirectResponse(url, status_code=302)
    response.headers["Access-Control-Expose-Headers"] = "Location"
    return response


@router.get("/auth/glpi/callback")
def glpi_callback(request: Request, code: str = "", state: str = ""):
    try:
        _services(request).complete(code=code, state=state)
    except HelpdeskError as exc:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code})
    base = request.app.state.public_base_url.rstrip("/")
    target = f"{base}/apps/helpdesk" if base else "/apps/helpdesk"
    return RedirectResponse(target, status_code=302)


@router.get("/auth/glpi/session")
def glpi_session(request: Request):
    actor = require_actor(request)
    return {"linked": _services(request).linked(actor.subject)}


@router.delete("/auth/glpi/session")
def delete_glpi_session(request: Request):
    actor = require_actor(request)
    _services(request).unlink(actor.subject)
    return {"linked": False}
