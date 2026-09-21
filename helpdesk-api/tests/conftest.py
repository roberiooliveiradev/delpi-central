from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from helpdesk_app.application.oauth_service import OAuthService
from helpdesk_app.application.ticket_service import TicketService
from helpdesk_app.domain.errors import GlpiForbidden, GlpiNotFound, HelpdeskError
from helpdesk_app.domain.models import (
    Attachment,
    Category,
    TicketDetail,
    TicketListPage,
    TicketSummary,
    TimelineEntry,
    TokenSet,
)
from helpdesk_app.infrastructure.persistence.memory import (
    MemoryIdempotencyStore,
    MemorySessionStore,
    MemoryStateStore,
)
from helpdesk_app.interface.http.auth_routes import router as auth_router
from helpdesk_app.interface.http.ticket_routes import router as ticket_router


class FakeGlpi:
    def __init__(self):
        self.tokens_by_code = {"good-code": TokenSet("access-a", "refresh-a", 3600)}
        self.tickets = [
            TicketSummary(
                7,
                "Impressora",
                "Novo",
                "Hardware",
                "Média",
                "2026-09-21T12:00:00Z",
                requester_display_name="Robério Teixeira",
                status_id=1,
            )
        ]
        self.detail = TicketDetail(
            7,
            "Impressora",
            "Novo",
            "Hardware",
            "Média",
            "2026-09-21T12:00:00Z",
            "Não imprime",
            (
                TimelineEntry(1, "followup", "Já reiniciei", "2026-09-21T13:00:00Z", "Ana"),
            ),
            (
                Attachment(2, "logo.png", "image/png"),
                Attachment(4, "foto.jpg", "image/jpeg"),
            ),
            "2026-09-21T11:00:00Z",
            "Robério Teixeira",
            status_id=1,
        )
        self.files = {
            2: (b"png-bytes", "image/png"),
            4: (b"jpg-bytes", "image/jpeg"),
        }
        self.downloaded = []
        self.created = []
        self.followups = []
        self.observers = []
        self.calls = 0

    def authorization_url(self, *, state: str, code_challenge: str) -> str:
        return f"https://glpi.example/authorize?state={state}&challenge={code_challenge}"

    def exchange_code(self, *, code: str, code_verifier: str) -> TokenSet:
        assert code_verifier
        return self.tokens_by_code[code]

    def refresh(self, refresh_token: str) -> TokenSet:
        return TokenSet("access-new", refresh_token, 3600)

    def list_categories(self, access_token: str):
        self.calls += 1
        assert access_token
        return [Category(3, "Hardware")]

    def list_tickets(self, access_token: str, query):
        self.calls += 1
        assert access_token
        self.last_list_query = query
        return TicketListPage(items=tuple(self.tickets), page=query.page, page_size=query.page_size, has_more=False)

    def get_ticket(self, access_token: str, ticket_id: int, viewer_email: str = ""):
        self.calls += 1
        if ticket_id == 99:
            raise GlpiNotFound("ausente")
        if ticket_id == 403:
            raise GlpiForbidden("negado")
        return self.detail

    def create_ticket(self, access_token: str, *, title, description, category_id, urgency_id):
        self.calls += 1
        assert "requester" not in title
        self.created.append((title, description, category_id, urgency_id, access_token))
        return 42

    def add_ticket_observer(self, access_token: str, ticket_id: int, user_id: int):
        self.calls += 1
        assert access_token
        assert "requester" not in str(user_id)
        assert "entity" not in str(user_id)
        self.observers.append((ticket_id, user_id, access_token))

    def add_followup(self, access_token: str, ticket_id: int, content: str):
        self.calls += 1
        if ticket_id == 99:
            raise GlpiNotFound("ausente")
        self.followups.append((ticket_id, content))
        return 8

    def download_attachment(self, access_token: str, document_id: int):
        self.calls += 1
        assert access_token
        if document_id not in self.files:
            raise GlpiNotFound("ausente")
        self.downloaded.append(document_id)
        return self.files[document_id]


def build_client(glpi: FakeGlpi | None = None) -> tuple[TestClient, FakeGlpi]:
    glpi = glpi or FakeGlpi()
    app = FastAPI()

    @app.exception_handler(HelpdeskError)
    async def helpdesk_error_handler(_request, exc: HelpdeskError):
        body = {"error": exc.code}
        if exc.code == "glpi_link_required":
            body["authorize_url"] = "/apps/helpdesk-api/auth/glpi/start"
        return JSONResponse(status_code=exc.status_code, content=body)

    now = lambda: datetime(2026, 9, 21, tzinfo=timezone.utc)
    states = MemoryStateStore(now)
    sessions = MemorySessionStore()
    oauth = OAuthService(glpi, states, sessions, now)
    app.state.oauth = oauth
    app.state.tickets = TicketService(glpi, oauth, MemoryIdempotencyStore())
    app.state.public_base_url = "https://centraldelpi.com.br"

    @app.middleware("http")
    async def test_auth(request, call_next):
        if request.url.path == "/auth/glpi/callback":
            return await call_next(request)
        permissions = [item for item in request.headers.get("x-permissions", "").split(",") if item]
        request.state.user = SimpleNamespace(
            sub=request.headers.get("x-subject", ""),
            email=request.headers.get("x-email", ""),
            permissions=permissions,
            is_superadmin=False,
        )
        return await call_next(request)

    app.include_router(auth_router)
    app.include_router(ticket_router)
    return TestClient(app), glpi


def auth_headers(subject="user-a"):
    return {"x-subject": subject, "x-permissions": "helpdesk.access"}


def link(client: TestClient, subject="user-a"):
    started = client.get("/auth/glpi/start", headers=auth_headers(subject), follow_redirects=False)
    state = started.headers["location"].split("state=")[1].split("&")[0]
    done = client.get(
        "/auth/glpi/callback",
        params={"code": "good-code", "state": state},
        follow_redirects=False,
    )
    assert done.status_code == 302
    return started
