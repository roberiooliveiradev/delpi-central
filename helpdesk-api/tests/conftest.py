from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from helpdesk_app.application.oauth_service import OAuthService
from helpdesk_app.application.ticket_service import TicketService
from helpdesk_app.domain.errors import GlpiForbidden, GlpiNotFound, GlpiValidation, HelpdeskError
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
                assigned_display_name="Ana Silva",
                assigned_user_id=15,
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
        self.solutions: list[tuple[int, str]] = []
        self.tasks: list[tuple[int, str]] = []
        self.created_validations: list[tuple[int, int, str]] = []
        self.observers = []
        self.assignees = []
        self.removed_assignees = []
        self.users = [
            SimpleNamespace(id=2, display_name="glpi", email=""),
            SimpleNamespace(id=15, display_name="Ana Silva", email="ana.silva@delpi.com.br"),
            SimpleNamespace(id=22, display_name="Bruno Costa", email="bruno.costa@delpi.com.br"),
            SimpleNamespace(id=99, display_name="0", email=""),
            SimpleNamespace(id=40, display_name="Sônia RH", email="rh_ues@delpi.com.br"),
        ]
        # Technician profile users (Ana, Bruno). Excludes system/noise and RH.
        self.technician_ids = {15, 22}
        self.can_assign = True
        # GLPI OAuth session user id (None = unknown / not linked in tests).
        self.session_uid: int | None = None
        self.uploads = []
        self.accepted_solutions: list[tuple[int, str]] = []
        self.rejected_solutions: list[tuple[int, str]] = []
        self.satisfactions: dict[int, tuple[int, str]] = {}
        self.validation_decisions: list[tuple[int, int, bool, str]] = []
        self.legacy_cycle = True
        # document_id → ticket_id for Document_Item membership (may lag Timeline).
        self.document_links: dict[int, int] = {2: 7, 4: 7}
        self.calls = 0
        # When False, upload does not appear on ticket.attachments (Timeline lag).
        self.attach_uploads_to_timeline = True
        self.refresh_error: Exception | None = None

    def authorization_url(self, *, state: str, code_challenge: str) -> str:
        return f"https://glpi.example/authorize?state={state}&challenge={code_challenge}"

    def exchange_code(self, *, code: str, code_verifier: str) -> TokenSet:
        assert code_verifier
        return self.tokens_by_code[code]

    def refresh(self, refresh_token: str) -> TokenSet:
        if self.refresh_error is not None:
            raise self.refresh_error
        return TokenSet("access-new", refresh_token, 3600)

    def list_categories(self, access_token: str):
        self.calls += 1
        assert access_token
        return [Category(3, "Hardware")]

    def list_tickets(self, access_token: str, query):
        self.calls += 1
        assert access_token
        self.last_list_query = query
        items = list(self.tickets)
        assignee_id = getattr(query, "assignee_id", None)
        if assignee_id is not None:
            items = [
                row
                for row in items
                if getattr(row, "assigned_user_id", None) == int(assignee_id)
            ]
        client_sort = getattr(query, "client_sort", "") or ""
        primary = client_sort.split(",")[0].strip() if client_sort else ""
        if primary.startswith("assigned:"):
            reverse = not primary.endswith(":asc")
            items = sorted(
                items,
                key=lambda row: (getattr(row, "assigned_display_name", "") or "").lower(),
                reverse=reverse,
            )
        return TicketListPage(
            items=tuple(items),
            page=query.page,
            page_size=query.page_size,
            has_more=False,
        )

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

    def add_ticket_assignee(self, access_token: str, ticket_id: int, user_id: int):
        from dataclasses import replace

        self.calls += 1
        assert access_token
        assert "requester" not in str(user_id)
        assert "entity" not in str(user_id)
        self.assignees.append((ticket_id, user_id, access_token))
        if self.detail.id == ticket_id:
            name = next((u.display_name for u in self.users if u.id == user_id), f"User {user_id}")
            self.detail = replace(self.detail, assigned_user_id=user_id, assigned_display_name=name)

    def remove_ticket_assignee(self, access_token: str, ticket_id: int, user_id: int):
        from dataclasses import replace

        self.calls += 1
        assert access_token
        self.removed_assignees.append((ticket_id, user_id, access_token))
        if self.detail.id == ticket_id and self.detail.assigned_user_id == user_id:
            self.detail = replace(self.detail, assigned_user_id=None, assigned_display_name="")

    def list_users(self, access_token: str, *, q: str = "", limit: int = 20):
        self.calls += 1
        assert access_token
        if not self.can_assign:
            raise GlpiForbidden("negado")
        term = (q or "").strip().lower()
        rows = self.users
        if term:
            rows = [
                u
                for u in rows
                if term in str(u.id)
                or term in u.display_name.lower()
                or term in str(getattr(u, "email", "") or "").lower()
            ]
        return rows[: max(1, min(int(limit or 20), 50))]

    def list_technician_user_ids(self, access_token: str):
        self.calls += 1
        assert access_token
        if not self.can_assign:
            raise GlpiForbidden("negado")
        return set(getattr(self, "technician_ids", {15, 22}))

    def find_user_by_email(self, access_token: str, email: str):
        self.calls += 1
        assert access_token
        if not self.can_assign:
            raise GlpiForbidden("negado")
        needle = (email or "").strip().lower()
        for user in self.users:
            if str(getattr(user, "email", "") or "").lower() == needle:
                return user
        return None

    def session_user_id(self, access_token: str):
        self.calls += 1
        assert access_token
        uid = getattr(self, "session_uid", None)
        return int(uid) if uid else None

    def can_assign_tickets(self, access_token: str) -> bool:
        self.calls += 1
        assert access_token
        return bool(self.can_assign)

    def add_followup(self, access_token: str, ticket_id: int, content: str):
        self.calls += 1
        if ticket_id == 99:
            raise GlpiNotFound("ausente")
        self.followups.append((ticket_id, content))
        return 8

    def add_ticket_solution(self, access_token: str, ticket_id: int, content: str):
        from dataclasses import replace

        self.calls += 1
        assert access_token
        if ticket_id == 99:
            raise GlpiNotFound("ausente")
        solution_id = 50 + len(self.solutions)
        self.solutions.append((ticket_id, content))
        if self.detail.id == ticket_id:
            entry = TimelineEntry(
                solution_id,
                "solution",
                content,
                "2026-09-24T12:00:00Z",
                "Ana",
            )
            self.detail = replace(
                self.detail,
                status_id=5,
                status="Solucionado",
                timeline=self.detail.timeline + (entry,),
            )
        return solution_id

    def add_ticket_task(self, access_token: str, ticket_id: int, content: str):
        from dataclasses import replace

        self.calls += 1
        assert access_token
        if ticket_id == 99:
            raise GlpiNotFound("ausente")
        task_id = 60 + len(self.tasks)
        self.tasks.append((ticket_id, content))
        if self.detail.id == ticket_id:
            entry = TimelineEntry(
                task_id,
                "task",
                content,
                "2026-09-24T12:05:00Z",
                "Ana",
            )
            self.detail = replace(
                self.detail,
                timeline=self.detail.timeline + (entry,),
            )
        return task_id

    def create_ticket_validation(
        self,
        access_token: str,
        ticket_id: int,
        *,
        approver_user_id: int,
        comment: str = "",
    ):
        from dataclasses import replace
        from helpdesk_app.domain.models import TicketValidation

        self.calls += 1
        assert access_token
        if ticket_id == 99:
            raise GlpiNotFound("ausente")
        validation_id = 70 + len(self.created_validations)
        self.created_validations.append((ticket_id, int(approver_user_id), comment))
        if self.detail.id == ticket_id:
            item = TicketValidation(
                id=validation_id,
                status=2,
                submission_comment=str(comment or ""),
                requested_approver_id=int(approver_user_id),
                mine_to_decide=False,
            )
            self.detail = replace(
                self.detail,
                validations=self.detail.validations + (item,),
            )
        return validation_id

    def download_attachment(self, access_token: str, document_id: int):
        self.calls += 1
        assert access_token
        if document_id not in self.files:
            raise GlpiNotFound("ausente")
        self.downloaded.append(document_id)
        return self.files[document_id]

    def ticket_owns_document(self, access_token: str, ticket_id: int, document_id: int) -> bool:
        self.calls += 1
        assert access_token
        return self.document_links.get(int(document_id)) == int(ticket_id)

    def upload_ticket_document(
        self,
        access_token: str,
        *,
        ticket_id: int,
        filename: str,
        content: bytes,
        mime: str,
    ):
        from dataclasses import replace

        self.calls += 1
        assert access_token
        if ticket_id == 99:
            raise GlpiNotFound("ausente")
        if not content:
            raise GlpiValidation("Arquivo vazio.")
        document_id = 100 + len(self.uploads)
        attachment = Attachment(document_id, filename, mime or "application/octet-stream")
        self.uploads.append((ticket_id, filename, content, mime))
        self.files[document_id] = (content, mime or "application/octet-stream")
        self.document_links[document_id] = ticket_id
        if self.attach_uploads_to_timeline and self.detail.id == ticket_id:
            self.detail = replace(
                self.detail,
                attachments=self.detail.attachments + (attachment,),
            )
        return attachment

    def legacy_cycle_enabled(self) -> bool:
        return bool(self.legacy_cycle)

    def accept_ticket_solution(self, access_token: str, ticket_id: int, content: str = "") -> None:
        from dataclasses import replace

        self.calls += 1
        assert access_token
        if ticket_id == 99:
            raise GlpiNotFound("ausente")
        self.accepted_solutions.append((ticket_id, content))
        if self.detail.id == ticket_id:
            self.detail = replace(self.detail, status_id=6, status="Fechado", can_followup=False)

    def reject_ticket_solution(self, access_token: str, ticket_id: int, content: str = "") -> None:
        from dataclasses import replace

        self.calls += 1
        assert access_token
        if ticket_id == 99:
            raise GlpiNotFound("ausente")
        self.rejected_solutions.append((ticket_id, content))
        if self.detail.id == ticket_id:
            self.detail = replace(self.detail, status_id=1, status="Novo", can_followup=True)

    def get_ticket_satisfaction(self, access_token: str, ticket_id: int):
        self.calls += 1
        assert access_token
        return self.satisfactions.get(int(ticket_id))

    def submit_ticket_satisfaction(
        self,
        access_token: str,
        ticket_id: int,
        *,
        satisfaction: int,
        comment: str = "",
    ) -> None:
        self.calls += 1
        assert access_token
        if int(ticket_id) in self.satisfactions:
            raise GlpiValidation("Pesquisa de satisfação já registrada.")
        self.satisfactions[int(ticket_id)] = (int(satisfaction), str(comment or ""))

    def decide_ticket_validation(
        self,
        access_token: str,
        ticket_id: int,
        validation_id: int,
        *,
        accept: bool,
        comment: str = "",
    ) -> None:
        from dataclasses import replace

        self.calls += 1
        assert access_token
        updated = []
        found = False
        for item in self.detail.validations:
            if item.id == validation_id:
                found = True
                updated.append(
                    replace(
                        item,
                        status=3 if accept else 4,
                        approval_comment=str(comment or ""),
                        mine_to_decide=False,
                    )
                )
            else:
                updated.append(item)
        if not found:
            raise GlpiNotFound("ausente")
        self.detail = replace(
            self.detail,
            validations=tuple(updated),
            can_decide_validation=any(item.mine_to_decide for item in updated),
        )
        self.validation_decisions.append((ticket_id, validation_id, accept, comment))


def build_client(
    glpi: FakeGlpi | None = None,
    directory=None,
    person_profiles=None,
) -> tuple[TestClient, FakeGlpi]:
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
    app.state.tickets = TicketService(
        glpi,
        oauth,
        MemoryIdempotencyStore(),
        directory=directory,
        person_profiles=person_profiles,
    )
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
    from helpdesk_app.interface.http.person_profile_routes import router as person_profile_router

    app.include_router(person_profile_router)
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
