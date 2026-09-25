from dataclasses import replace
import logging
import unicodedata

from helpdesk_app.application.oauth_service import OAuthService
from helpdesk_app.application.ports import GlpiGateway, IdempotencyStore
from helpdesk_app.application.services.message_html_sanitizer import (
    MAX_MESSAGE_HTML_CHARS,
    extract_bff_attachment_refs,
    prepare_outbound_message_html,
)
from helpdesk_app.domain.errors import (
    GlpiFeatureDisabled,
    GlpiForbidden,
    GlpiNotFound,
    GlpiUnauthorized,
    GlpiValidation,
    LinkRequired,
    MissingIdempotencyKey,
)
from helpdesk_app.domain.models import CatalogUser, StoredResponse, TicketDetail, TicketListPage, TicketListQuery
from helpdesk_app.infrastructure.glpi.mapping import (
    filter_assignable_catalog_users,
    normalize_assignee_id,
    normalize_observer_ids,
    search_term_variants,
    solicitante_cycle_flags,
    ticket_allows_technician_ops,
    timeline_has_entry,
    timeline_has_solution,
)

logger = logging.getLogger("helpdesk.tickets")


def _fold_name(value: str) -> str:
    text = " ".join(str(value or "").split()).casefold()
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


class TicketService:
    def __init__(
        self,
        glpi: GlpiGateway,
        oauth: OAuthService,
        idempotency: IdempotencyStore,
        directory=None,
        person_profiles=None,
    ):
        self._glpi = glpi
        self._oauth = oauth
        self._idempotency = idempotency
        self._directory = directory
        self._person_profiles = person_profiles

    def categories(self, subject: str):
        return self._glpi.list_categories(self._token(subject))

    def request_types(self, subject: str):
        return self._glpi.list_request_types(self._token(subject))

    def followup_templates(self, subject: str):
        return self._glpi.list_followup_templates(self._token(subject))

    def solution_types(self, subject: str):
        return self._glpi.list_solution_types(self._token(subject))

    def solution_templates(self, subject: str):
        return self._glpi.list_solution_templates(self._token(subject))

    def task_categories(self, subject: str):
        return self._glpi.list_task_categories(self._token(subject))

    def task_templates(self, subject: str):
        return self._glpi.list_task_templates(self._token(subject))

    def task_statuses(self):
        return self._glpi.list_task_statuses()

    def groups(self, subject: str):
        return self._glpi.list_groups(self._token(subject))

    def validation_templates(self, subject: str):
        return self._glpi.list_validation_templates(self._token(subject))

    def approval_steps(self, subject: str):
        return self._glpi.list_approval_steps(self._token(subject))

    def users(
        self, subject: str, *, q: str = "", limit: int = 20, purpose: str = "mention"
    ) -> list[CatalogUser]:
        token = self._token(subject)
        safe_limit = max(1, min(int(limit or 20), 50))
        term = (q or "").strip()
        by_id: dict[int, CatalogUser] = {}
        purpose_key = (purpose or "mention").strip().lower()
        assignee_only = purpose_key in {"assignee", "technician", "tech"}
        technician_ids: set[int] | None = None
        if assignee_only:
            try:
                technician_ids = set(self._glpi.list_technician_user_ids(token))
            except Exception:
                logger.exception("helpdesk_technician_ids_failed")
                technician_ids = set()
            if not technician_ids:
                return []

        def put(
            user: CatalogUser,
            *,
            prefer_name: str = "",
            prefer_email: str = "",
            prefer_directory_user_id: str = "",
        ) -> None:
            if technician_ids is not None and int(user.id) not in technician_ids:
                return
            name = (prefer_name or user.display_name or "").strip() or user.display_name
            email = (prefer_email or user.email or "").strip().lower()
            directory_user_id = (
                prefer_directory_user_id
                or getattr(user, "directory_user_id", "")
                or ""
            ).strip()
            has_photo = bool(getattr(user, "has_photo", False))
            previous = by_id.get(int(user.id))
            if previous is None:
                by_id[int(user.id)] = CatalogUser(
                    id=int(user.id),
                    display_name=name,
                    email=email,
                    directory_user_id=directory_user_id,
                    has_photo=has_photo,
                )
                return
            by_id[int(user.id)] = CatalogUser(
                id=int(user.id),
                display_name=name or previous.display_name,
                email=email or previous.email,
                directory_user_id=directory_user_id or previous.directory_user_id,
                has_photo=has_photo or previous.has_photo,
            )

        # 1) Sempre busca no GLPI (nome/username) — fonte do id atribuível.
        try:
            for row in filter_assignable_catalog_users(
                self._glpi.list_users(token, q=term, limit=safe_limit)
            ):
                put(row)
        except GlpiValidation:
            pass

        directory = self._directory
        if directory is not None and getattr(directory, "configured", lambda: False)() and term:
            delpi_hits: list[dict[str, str]] = []
            seen_keys: set[str] = set()
            queries: list[str] = []
            if "@" in term:
                queries.append(term.lower())
                queries.append(term.split("@", 1)[0])
            queries.extend(list(search_term_variants(term))[:4])
            dir_kwargs: dict = {}
            if assignee_only:
                # Só pessoas com console GLPI no Minha DELPI (técnicos operacionais).
                dir_kwargs["permission"] = "helpdesk.console"
            for variant in queries:
                variant = (variant or "").strip()
                if not variant:
                    continue
                for person in directory.search_users(
                    q=variant, limit=safe_limit, browse=False, **dir_kwargs
                ):
                    email = str(person.get("email") or "").strip().lower()
                    key = email or str(person.get("id") or "")
                    if not key or key in seen_keys:
                        continue
                    seen_keys.add(key)
                    delpi_hits.append(person)

            finder = getattr(self._glpi, "find_user_by_email", None)
            for person in delpi_hits:
                email = str(person.get("email") or "").strip().lower()
                name = str(person.get("name") or "").strip()
                directory_user_id = str(person.get("id") or "").strip()
                glpi_user = finder(token, email) if callable(finder) and "@" in email else None
                if glpi_user is not None:
                    put(
                        glpi_user,
                        prefer_name=name,
                        prefer_email=email,
                        prefer_directory_user_id=directory_user_id,
                    )
                    continue
                needle = _fold_name(name)
                if not needle:
                    continue
                matched = next(
                    (
                        row
                        for row in by_id.values()
                        if needle == _fold_name(row.display_name)
                        or needle in _fold_name(row.display_name)
                        or _fold_name(row.display_name) in needle
                    ),
                    None,
                )
                if matched is not None:
                    put(
                        matched,
                        prefer_name=name or matched.display_name,
                        prefer_email=email,
                        prefer_directory_user_id=directory_user_id,
                    )
                    continue
                for token_q in [part for part in name.replace("-", " ").split() if len(part) >= 3][:2]:
                    try:
                        rows = filter_assignable_catalog_users(
                            self._glpi.list_users(token, q=token_q, limit=safe_limit)
                        )
                    except GlpiValidation:
                        continue
                    for row in rows:
                        put(row)
                        folded = _fold_name(row.display_name)
                        if needle == folded or needle in folded or folded in needle:
                            put(
                                row,
                                prefer_name=name or row.display_name,
                                prefer_email=email,
                                prefer_directory_user_id=directory_user_id,
                            )
                        elif email and (row.email or "").lower() == email:
                            put(
                                row,
                                prefer_name=name or row.display_name,
                                prefer_email=email,
                                prefer_directory_user_id=directory_user_id,
                            )

        rows = list(by_id.values())[:safe_limit]
        profiles = self._person_profiles
        if profiles is not None and getattr(profiles, "configured", lambda: False)():
            directory_ids = [
                row.directory_user_id for row in rows if (row.directory_user_id or "").strip()
            ]
            flags = profiles.lookup_has_photo(directory_ids) if directory_ids else {}
            if flags:
                enriched: list[CatalogUser] = []
                for row in rows:
                    uid = (row.directory_user_id or "").strip()
                    has_photo = bool(flags.get(uid)) if uid else False
                    enriched.append(
                        CatalogUser(
                            id=row.id,
                            display_name=row.display_name,
                            email=row.email,
                            directory_user_id=uid,
                            has_photo=has_photo,
                        )
                    )
                return enriched
        return rows

    def _require_technician(self, token: str, user_id: int) -> None:
        try:
            tech_ids = set(self._glpi.list_technician_user_ids(token))
        except Exception:
            tech_ids = set()
        if not tech_ids:
            raise GlpiValidation("Catálogo de técnicos indisponível.")
        if int(user_id) not in tech_ids:
            raise GlpiValidation("Usuário não é técnico atribuível no GLPI.")

    def capabilities(self, subject: str) -> dict:
        token = self._token(subject)
        return {"can_assign": bool(self._glpi.can_assign_tickets(token))}

    def tickets(self, subject: str, query: TicketListQuery) -> TicketListPage:
        return self._glpi.list_tickets(self._token(subject), query)

    def ticket(self, subject: str, ticket_id: int, viewer_email: str = "") -> TicketDetail:
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        detail = replace(detail, can_assign=bool(self._glpi.can_assign_tickets(token)))
        detail = self._with_technician_ops_flags(token, detail, viewer_email=viewer_email)
        return self._with_cycle_flags(token, detail)

    def attachment(self, subject: str, ticket_id: int, document_id: int) -> tuple[bytes, str, str]:
        token = self._token(subject)
        ticket = self._glpi.get_ticket(token, ticket_id, viewer_email="")
        match = next((item for item in ticket.attachments if item.document_id == document_id), None)
        if match is None:
            # H12: Timeline HLAPI pode omitir Document_Item recém-criado via upload legado.
            if not self._glpi.ticket_owns_document(token, ticket_id, document_id):
                raise GlpiNotFound("Anexo não encontrado.")
            content, mime = self._glpi.download_attachment(token, document_id)
            return content, mime, "anexo"
        content, mime = self._glpi.download_attachment(token, document_id)
        return content, mime, match.filename

    def upload_attachment(
        self,
        subject: str,
        ticket_id: int,
        *,
        filename: str,
        content: bytes,
        mime: str,
        title: str | None = None,
        idempotency_key: str | None = None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        operation = f"upload_attachment:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        uploaded = self._glpi.upload_ticket_document(
            self._token(subject),
            ticket_id=ticket_id,
            filename=filename,
            content=content,
            mime=mime,
            title=title,
        )
        stored = StoredResponse(
            status_code=201,
            body={
                "document_id": uploaded.document_id,
                "filename": uploaded.filename,
                "mime": uploaded.mime,
            },
        )
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def create(
        self,
        subject: str,
        *,
        title: str,
        description: str,
        category_id: int,
        urgency_id: int,
        observer_ids: list[int] | tuple[int, ...] | None = None,
        assignee_id: int | None = None,
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        _validate_text(title, "title")
        # Opening has no ticket yet — strip every document image (upload after create).
        description_html = _prepare_message_html(description, "description", ticket_id=0)
        observers = normalize_observer_ids(observer_ids)
        assignee = normalize_assignee_id(assignee_id)
        operation = "create_ticket"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        ticket_id = self._glpi.create_ticket(
            token,
            title=title.strip(),
            description=description_html,
            category_id=category_id,
            urgency_id=urgency_id,
        )
        for user_id in observers:
            self._glpi.add_ticket_observer(token, ticket_id, user_id)
        if assignee is not None:
            self._require_technician(token, assignee)
            self._glpi.add_ticket_assignee(token, ticket_id, assignee)
        stored = StoredResponse(status_code=201, body={"id": ticket_id})
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def set_assignee(
        self,
        subject: str,
        ticket_id: int,
        *,
        user_id: int,
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        assignee = normalize_assignee_id(user_id)
        if assignee is None:
            raise GlpiValidation("assignee_id inválido.")
        operation = f"set_assignee:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email="")
        current = detail.assigned_user_id
        if current == assignee:
            stored = StoredResponse(
                status_code=200,
                body={"user_id": assignee, "assigned_display_name": detail.assigned_display_name},
            )
            self._idempotency.save(subject, operation, key, stored)
            return stored
        if current is not None and current != assignee:
            self._glpi.remove_ticket_assignee(token, ticket_id, current)
        self._require_technician(token, assignee)
        self._glpi.add_ticket_assignee(token, ticket_id, assignee)
        refreshed = self._glpi.get_ticket(token, ticket_id, viewer_email="")
        stored = StoredResponse(
            status_code=200,
            body={
                "user_id": refreshed.assigned_user_id or assignee,
                "assigned_display_name": refreshed.assigned_display_name,
            },
        )
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def followup(
        self,
        subject: str,
        ticket_id: int,
        *,
        content: str,
        request_type_id: int | None = None,
        idempotency_key: str | None = None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        # H12: Document_Item via legacy upload may still be absent from Timeline.
        token = self._token(subject)
        ticket = self._glpi.get_ticket(token, ticket_id, viewer_email="")
        allowed = {item.document_id for item in ticket.attachments}
        # H12: after upload, re-read once if HTML refs are not yet in attachments.
        html_refs = {
            doc_id
            for ref_ticket, doc_id in extract_bff_attachment_refs(content)
            if ref_ticket == ticket_id
        }
        if html_refs - allowed:
            ticket = self._glpi.get_ticket(token, ticket_id, viewer_email="")
            allowed = {item.document_id for item in ticket.attachments}
        for doc_id in html_refs - allowed:
            if self._glpi.ticket_owns_document(token, ticket_id, doc_id):
                allowed.add(doc_id)
        content_html = _prepare_message_html(
            content,
            "content",
            ticket_id=ticket_id,
            allowed_document_ids=allowed,
        )
        operation = f"followup:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        followup_id = self._glpi.add_followup(
            self._token(subject),
            ticket_id,
            content_html,
            request_type_id=request_type_id,
        )
        stored = StoredResponse(status_code=201, body={"id": followup_id})
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def create_solution(
        self,
        subject: str,
        ticket_id: int,
        *,
        content: str,
        solution_type_id: int | None = None,
        viewer_email: str = "",
        idempotency_key: str | None = None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        operation = f"create_solution:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        self._require_technician_ops(token, detail, viewer_email=viewer_email, action="solução")
        content_html = _prepare_message_html(content, "content", ticket_id=ticket_id)
        solution_id = self._glpi.add_ticket_solution(
            token,
            ticket_id,
            content_html,
            solution_type_id=solution_type_id,
        )
        refreshed = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        if not (
            timeline_has_entry(refreshed.timeline, kind="solution", entry_id=solution_id)
            or timeline_has_solution(refreshed.timeline)
        ):
            raise GlpiValidation("A solução não foi confirmada no chamado.")
        stored = StoredResponse(
            status_code=201,
            body={"id": solution_id, "status_id": refreshed.status_id},
        )
        self._idempotency.save(subject, operation, key, stored)
        logger.info(
            "helpdesk_create_solution ticket_id=%s solution_id=%s status_id=%s",
            ticket_id,
            solution_id,
            refreshed.status_id,
        )
        return stored

    def create_task(
        self,
        subject: str,
        ticket_id: int,
        *,
        content: str,
        state: int | None = None,
        duration_seconds: int | None = None,
        category_id: int | None = None,
        user_tech_id: int | None = None,
        group_tech_id: int | None = None,
        planned_begin: str | None = None,
        planned_end: str | None = None,
        viewer_email: str = "",
        idempotency_key: str | None = None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        operation = f"create_task:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        self._require_technician_ops(token, detail, viewer_email=viewer_email, action="tarefa")
        content_html = _prepare_message_html(content, "content", ticket_id=ticket_id)
        task_id = self._glpi.add_ticket_task(
            token,
            ticket_id,
            content_html,
            state=state,
            duration_seconds=duration_seconds,
            category_id=category_id,
            user_tech_id=user_tech_id,
            group_tech_id=group_tech_id,
            planned_begin=planned_begin,
            planned_end=planned_end,
        )
        refreshed = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        if not timeline_has_entry(refreshed.timeline, kind="task", entry_id=task_id):
            raise GlpiValidation("A tarefa não foi confirmada no chamado.")
        entry = next(
            (item for item in refreshed.timeline if item.kind == "task" and item.id == task_id),
            None,
        )
        body: dict = {"id": task_id}
        if entry is not None:
            body.update(
                {
                    "state": entry.state,
                    "duration_seconds": entry.duration_seconds,
                    "category_name": entry.category_name,
                    "user_tech_display_name": entry.user_tech_display_name,
                    "group_tech_display_name": entry.group_tech_display_name,
                    "planned_begin": entry.planned_begin,
                    "planned_end": entry.planned_end,
                }
            )
        stored = StoredResponse(status_code=201, body=body)
        self._idempotency.save(subject, operation, key, stored)
        logger.info("helpdesk_create_task ticket_id=%s task_id=%s", ticket_id, task_id)
        return stored

    def request_approval(
        self,
        subject: str,
        ticket_id: int,
        *,
        approver_user_id: int | None = None,
        approver_type: str = "user",
        approver_id: int | None = None,
        content: str = "",
        viewer_email: str = "",
        idempotency_key: str | None = None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        operation = f"request_approval:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        self._require_technician_ops(token, detail, viewer_email=viewer_email, action="aprovação")
        target_type = "Group" if str(approver_type).lower() == "group" else "User"
        raw_id = approver_id if approver_id is not None else approver_user_id
        try:
            target_id = int(raw_id) if raw_id is not None else 0
        except (TypeError, ValueError) as exc:
            raise GlpiValidation("approver_id inválido.") from exc
        if target_id <= 0:
            raise GlpiValidation("approver_id inválido.")
        if target_type == "User":
            catalog = self._glpi.list_users(token, q=str(target_id), limit=20)
            if not any(int(getattr(user, "id", 0) or 0) == target_id for user in catalog):
                raise GlpiValidation("Aprovador inválido ou inacessível.")
        else:
            groups = self._glpi.list_groups(token)
            if not any(int(getattr(group, "id", 0) or 0) == target_id for group in groups):
                raise GlpiValidation("Grupo aprovador inválido ou inacessível.")
        comment = (content or "").strip()
        if comment:
            comment = _prepare_message_html(comment, "content", ticket_id=ticket_id)
        validation_id = self._glpi.create_ticket_validation(
            token,
            ticket_id,
            approver_type=target_type,
            approver_id=target_id,
            comment=comment,
        )
        refreshed = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        match = next((item for item in refreshed.validations if item.id == validation_id), None)
        if match is None:
            raise GlpiValidation("A solicitação de aprovação não foi confirmada.")
        stored = StoredResponse(
            status_code=201,
            body={
                "id": validation_id,
                "status": match.status,
                "requested_approver_id": match.requested_approver_id,
                "requested_approver_type": match.requested_approver_type,
            },
        )
        self._idempotency.save(subject, operation, key, stored)
        logger.info(
            "helpdesk_request_approval ticket_id=%s validation_id=%s approver_type=%s approver=%s",
            ticket_id,
            validation_id,
            target_type,
            target_id,
        )
        return stored

    def accept_solution(
        self,
        subject: str,
        ticket_id: int,
        *,
        content: str = "",
        viewer_email: str = "",
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        operation = f"accept_solution:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        if not detail.requester_mine:
            raise GlpiForbidden("Só o solicitante pode aceitar a solução.")
        if detail.status_id != 5:
            raise GlpiValidation("Só é possível aceitar solução em chamado solucionado.")
        message = (content or "").strip() or "Solução aceita."
        self._glpi.accept_ticket_solution(token, ticket_id, message)
        refreshed = self._with_cycle_flags(
            token, self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        )
        stored = StoredResponse(
            status_code=200,
            body={"id": refreshed.id, "status_id": refreshed.status_id},
        )
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def reject_solution(
        self,
        subject: str,
        ticket_id: int,
        *,
        content: str = "",
        viewer_email: str = "",
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        operation = f"reject_solution:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        if not detail.requester_mine:
            raise GlpiForbidden("Só o solicitante pode recusar a solução.")
        if detail.status_id not in {5, 6}:
            raise GlpiValidation("Só é possível recusar/reabrir em solucionado ou fechado.")
        message = (content or "").strip() or "Solução recusada."
        self._glpi.reject_ticket_solution(token, ticket_id, message)
        refreshed = self._with_cycle_flags(
            token, self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        )
        stored = StoredResponse(
            status_code=200,
            body={"id": refreshed.id, "status_id": refreshed.status_id},
        )
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def satisfaction(self, subject: str, ticket_id: int, viewer_email: str = "") -> dict:
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        if not detail.requester_mine:
            raise GlpiForbidden("Só o solicitante pode ver a pesquisa de satisfação.")
        row = self._glpi.get_ticket_satisfaction(token, ticket_id)
        if row is None:
            raise GlpiNotFound("Pesquisa de satisfação não encontrada.")
        score, comment = row
        return {"satisfaction": score, "comment": comment}

    def submit_satisfaction(
        self,
        subject: str,
        ticket_id: int,
        *,
        satisfaction: int,
        comment: str = "",
        viewer_email: str = "",
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        operation = f"submit_satisfaction:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        if satisfaction not in {1, 2, 3, 4, 5}:
            raise GlpiValidation("satisfaction inválida.")
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        if not detail.requester_mine:
            raise GlpiForbidden("Só o solicitante pode responder a pesquisa.")
        if detail.status_id != 6:
            raise GlpiValidation("Pesquisa só é disponível em chamado fechado.")
        existing_sat = self._glpi.get_ticket_satisfaction(token, ticket_id)
        if existing_sat is not None:
            raise GlpiValidation("Pesquisa de satisfação já registrada.")
        self._glpi.submit_ticket_satisfaction(
            token,
            ticket_id,
            satisfaction=satisfaction,
            comment=(comment or "").strip(),
        )
        stored = StoredResponse(
            status_code=201,
            body={"satisfaction": satisfaction, "comment": (comment or "").strip()},
        )
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def decide_validation(
        self,
        subject: str,
        ticket_id: int,
        validation_id: int,
        *,
        accept: bool,
        comment: str = "",
        viewer_email: str = "",
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        action = "accept" if accept else "reject"
        operation = f"validation_{action}:{ticket_id}:{validation_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        match = next((item for item in detail.validations if item.id == validation_id), None)
        if match is None:
            raise GlpiNotFound("Aprovação não encontrada.")
        if not match.mine_to_decide:
            raise GlpiForbidden("Só o aprovador designado pode decidir esta validação.")
        self._glpi.decide_ticket_validation(
            token,
            ticket_id,
            validation_id,
            accept=accept,
            comment=(comment or "").strip(),
        )
        refreshed = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        stored = StoredResponse(
            status_code=200,
            body={
                "id": validation_id,
                "status": 3 if accept else 4,
                "can_decide_validation": refreshed.can_decide_validation,
            },
        )
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def _viewer_is_technician(self, token: str, viewer_email: str) -> bool:
        """True when GLPI session (or email catalog) maps to a technician-profile user.

        Prefer OAuth session ``user_id`` — same identity used for validation mine_to_decide.
        Keycloak email → catalog is fallback only (emails can diverge from GLPI).
        Distinct from ``can_assign`` (Administration/User list readability).
        """
        try:
            tech_ids = set(self._glpi.list_technician_user_ids(token))
        except Exception:
            logger.info("helpdesk_technician_catalog_unavailable")
            return False
        if not tech_ids:
            return False

        session_uid = None
        try:
            session_uid = self._glpi.session_user_id(token)
        except Exception:
            session_uid = None
        try:
            if session_uid and int(session_uid) in tech_ids:
                logger.info("helpdesk_technician_ops_gate match=session")
                return True
        except (TypeError, ValueError):
            pass

        email = (viewer_email or "").strip().lower()
        if "@" not in email:
            logger.info("helpdesk_technician_ops_gate match=none reason=no_email")
            return False
        try:
            user = self._glpi.find_user_by_email(token, email)
        except Exception:
            return False
        if user is None:
            logger.info("helpdesk_technician_ops_gate match=none reason=email_not_in_catalog")
            return False
        try:
            matched = int(user.id) in tech_ids
        except (TypeError, ValueError):
            return False
        if matched:
            logger.info("helpdesk_technician_ops_gate match=email")
        else:
            logger.info("helpdesk_technician_ops_gate match=none reason=not_in_technician_profiles")
        return matched

    def _require_technician_ops(
        self,
        token: str,
        detail: TicketDetail,
        *,
        viewer_email: str,
        action: str,
    ) -> None:
        if not ticket_allows_technician_ops(detail.status_id):
            raise GlpiValidation(f"Não é possível adicionar {action} em chamado fechado.")
        if not self._viewer_is_technician(token, viewer_email):
            raise GlpiForbidden(f"Sem permissão para adicionar {action}.")

    def _with_technician_ops_flags(
        self,
        token: str,
        detail: TicketDetail,
        *,
        viewer_email: str,
    ) -> TicketDetail:
        allowed = ticket_allows_technician_ops(detail.status_id) and self._viewer_is_technician(
            token, viewer_email
        )
        return replace(
            detail,
            can_create_solution=allowed,
            can_create_task=allowed,
            can_request_approval=allowed,
        )

    def _with_cycle_flags(self, token: str, detail: TicketDetail) -> TicketDetail:
        legacy_on = True
        enabled_fn = getattr(self._glpi, "legacy_cycle_enabled", None)
        if callable(enabled_fn):
            legacy_on = bool(enabled_fn())
        score: int | None = None
        comment = ""
        submitted = False
        if legacy_on and detail.requester_mine and detail.status_id == 6:
            try:
                row = self._glpi.get_ticket_satisfaction(token, detail.id)
            except GlpiFeatureDisabled:
                legacy_on = False
                row = None
            if row is not None:
                score, comment = row
                submitted = True
        can_accept, can_reject, can_sat = solicitante_cycle_flags(
            requester_mine=detail.requester_mine,
            status_id=detail.status_id,
            satisfaction_submitted=submitted,
            legacy_enabled=legacy_on,
        )
        return replace(
            detail,
            can_accept_solution=can_accept,
            can_reject_solution=can_reject,
            can_submit_satisfaction=can_sat,
            satisfaction=score,
            satisfaction_comment=comment,
        )

    def _token(self, subject: str) -> str:
        try:
            return self._oauth.access_token_for(subject)
        except GlpiUnauthorized as exc:
            raise LinkRequired("A sessão do GLPI expirou. Autorize de novo.") from exc


def _require_key(value: str | None) -> str:
    if value is None or not value.strip():
        raise MissingIdempotencyKey("Informe Idempotency-Key.")
    return value.strip()


def _validate_text(value: str, field: str) -> None:
    if not value or not value.strip():
        raise GlpiValidation(f"{field} é obrigatório.")


def _prepare_message_html(
    value: str,
    field: str,
    *,
    ticket_id: int = 0,
    allowed_document_ids: set[int] | frozenset[int] | None = None,
) -> str:
    if value is None:
        raise GlpiValidation(f"{field} é obrigatório.")
    if len(value) > MAX_MESSAGE_HTML_CHARS:
        raise GlpiValidation(f"{field} excede o tamanho máximo permitido.")
    cleaned = prepare_outbound_message_html(
        value,
        ticket_id=ticket_id,
        allowed_document_ids=allowed_document_ids or (),
    )
    if not cleaned:
        raise GlpiValidation(f"{field} é obrigatório.")
    return cleaned
