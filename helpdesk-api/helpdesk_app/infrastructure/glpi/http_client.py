import json
import logging
import re
from dataclasses import replace
from urllib.parse import quote

import httpx

from helpdesk_app.domain.errors import (
    GlpiForbidden,
    GlpiNotFound,
    GlpiUnauthorized,
    GlpiUnavailable,
    GlpiValidation,
    GlpiFeatureDisabled,
)
from helpdesk_app.domain.models import (
    Attachment,
    CatalogUser,
    Category,
    PersonIdentity,
    TicketDetail,
    TicketListPage,
    TicketListQuery,
    TicketValidation,
    TokenSet,
)
from helpdesk_app.infrastructure.glpi.mapping import (
    URGENCIES,
    TASK_STATUSES,
    apply_viewer_identity,
    apply_validation_viewer,
    attachment_filename,
    build_user_search_filter,
    create_ticket_body,
    display_text,
    parse_categories,
    parse_catalog_users,
    parse_created_id,
    parse_followup_templates,
    parse_named_catalog,
    parse_profile_user_ids,
    parse_solution_templates,
    parse_task_templates,
    payload_row_count,
    parse_ticket_detail,
    parse_ticket_list,
    parse_ticket_page,
    parse_ticket_validations,
    parse_token_set,
    parse_viewer_identity,
    team_member_assigned_body,
    team_member_observer_body,
)

logger = logging.getLogger("helpdesk.glpi")

_GET_ATTEMPTS = 3
_MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
_CATEGORY_PAGE = 50
_CATEGORY_CAP = 500
_HELPDESK_CATEGORY_FILTER = "is_helpdesk_visible==true"
_SAFE_UPLOAD_NAME = re.compile(r"[^\w.\- ()\[\]]+", re.UNICODE)


def _saml_idp_query(saml_idp_id: str) -> str:
    if not saml_idp_id:
        return ""
    if not saml_idp_id.isdigit() or len(saml_idp_id) >= 3:
        raise ValueError("GLPI_SAML_IDP_ID must be a numeric IdP id below 100")
    return f"samlIdpId={saml_idp_id}&"


class HttpxGlpiClient:
    def __init__(
        self,
        *,
        base_url: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        saml_idp_id: str = "1",
        connect_timeout: float = 5,
        read_timeout: float = 20,
        legacy_upload_enabled: bool = False,
        legacy_app_token: str = "",
        legacy_user_token: str = "",
        legacy_max_upload_bytes: int = _MAX_ATTACHMENT_BYTES,
        assignee_profile_ids: tuple[int, ...] | list[int] | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        self._base = base_url.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._saml_idp_id = saml_idp_id.strip()
        self._legacy_upload_enabled = bool(legacy_upload_enabled)
        self._legacy_app_token = (legacy_app_token or "").strip()
        self._legacy_user_token = (legacy_user_token or "").strip()
        self._legacy_max_upload_bytes = max(1, int(legacy_max_upload_bytes))
        if assignee_profile_ids is None:
            from helpdesk_app.config import parse_assignee_profile_ids

            self._assignee_profile_ids = parse_assignee_profile_ids()
        else:
            self._assignee_profile_ids = tuple(
                int(item) for item in assignee_profile_ids if int(item) > 0
            ) or (6,)
        self._technician_ids_cache: set[int] | None = None
        self._http = httpx.Client(
            timeout=httpx.Timeout(read_timeout, connect=connect_timeout),
            transport=transport,
        )
        self.post_calls = 0

    def authorization_url(self, *, state: str, code_challenge: str) -> str:
        params = httpx.QueryParams(
            {
                "response_type": "code",
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "scope": "api",
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        )
        authorize = f"{self._base}/api.php/authorize?{params}&accept=1"
        # GLPI 11.0.5 recria /authorize sem state nem PKCE quando a sessão
        # ainda não existe. Com IdP, o samlsso guarda $_GET['redirect'] já
        # decodificado e depois concatena sem escapar: duas codificações
        # mantêm state e PKCE dentro do valor até o retorno do Keycloak.
        saml = _saml_idp_query(self._saml_idp_id)
        encoded = quote(authorize, safe="")
        if saml:
            encoded = quote(encoded, safe="")
        return f"{self._base}/?{saml}redirect={encoded}"

    def exchange_code(self, *, code: str, code_verifier: str) -> TokenSet:
        payload = self._form(
            "/api.php/token",
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._redirect_uri,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "code_verifier": code_verifier,
            },
        )
        return parse_token_set(payload)

    def refresh(self, refresh_token: str) -> TokenSet:
        try:
            payload = self._form(
                "/api.php/token",
                {
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )
            return parse_token_set(payload)
        except GlpiValidation as exc:
            # GLPI returns 400 invalid_grant for expired/rotated refresh — not a form bug.
            raise GlpiUnauthorized("Refresh token do GLPI recusado.") from exc

    def list_categories(self, access_token: str) -> list[Category]:
        collected: list[Category] = []
        start = 0
        while start < _CATEGORY_CAP:
            payload = self._json(
                "GET",
                "/api.php/v2.2/Dropdowns/ITILCategory",
                token=access_token,
                params={
                    "start": start,
                    "limit": _CATEGORY_PAGE,
                    "filter": _HELPDESK_CATEGORY_FILTER,
                },
            )
            collected.extend(parse_categories(payload))
            if payload_row_count(payload) < _CATEGORY_PAGE:
                break
            start += _CATEGORY_PAGE
        return collected

    def _list_dropdown_pages(
        self,
        access_token: str,
        path: str,
        *,
        filter_expr: str | None = None,
        require_helpdesk_visible: bool = False,
        require_active: bool = False,
    ) -> list[Category]:
        collected: list[Category] = []
        start = 0
        while start < _CATEGORY_CAP:
            params: dict[str, str | int] = {"start": start, "limit": _CATEGORY_PAGE}
            if filter_expr:
                params["filter"] = filter_expr
            payload = self._json("GET", path, token=access_token, params=params)
            collected.extend(
                parse_named_catalog(
                    payload,
                    require_helpdesk_visible=require_helpdesk_visible,
                    require_active=require_active,
                )
            )
            if payload_row_count(payload) < _CATEGORY_PAGE:
                break
            start += _CATEGORY_PAGE
        return collected

    def list_request_types(self, access_token: str) -> list[Category]:
        # Prefer followup-visible when the filter is accepted; fall back without filter.
        try:
            return self._list_dropdown_pages(
                access_token,
                "/api.php/v2.2/Dropdowns/RequestType",
                filter_expr="is_visible_followup==true",
                require_active=True,
            )
        except GlpiValidation:
            return self._list_dropdown_pages(
                access_token,
                "/api.php/v2.2/Dropdowns/RequestType",
                require_active=True,
            )

    def list_followup_templates(self, access_token: str):
        collected = []
        start = 0
        while start < _CATEGORY_CAP:
            payload = self._json(
                "GET",
                "/api.php/v2.2/Dropdowns/FollowupTemplate",
                token=access_token,
                params={"start": start, "limit": _CATEGORY_PAGE},
            )
            collected.extend(parse_followup_templates(payload))
            if payload_row_count(payload) < _CATEGORY_PAGE:
                break
            start += _CATEGORY_PAGE
        return collected

    def list_solution_types(self, access_token: str) -> list[Category]:
        return self._list_dropdown_pages(access_token, "/api.php/v2.2/Dropdowns/SolutionType")

    def list_solution_templates(self, access_token: str):
        collected = []
        start = 0
        while start < _CATEGORY_CAP:
            payload = self._json(
                "GET",
                "/api.php/v2.2/Dropdowns/SolutionTemplate",
                token=access_token,
                params={"start": start, "limit": _CATEGORY_PAGE},
            )
            collected.extend(parse_solution_templates(payload))
            if payload_row_count(payload) < _CATEGORY_PAGE:
                break
            start += _CATEGORY_PAGE
        return collected

    def list_task_categories(self, access_token: str) -> list[Category]:
        try:
            return self._list_dropdown_pages(
                access_token,
                "/api.php/v2.2/Dropdowns/TaskCategory",
                filter_expr="is_helpdesk_visible==true",
                require_helpdesk_visible=True,
                require_active=True,
            )
        except GlpiValidation:
            return self._list_dropdown_pages(
                access_token,
                "/api.php/v2.2/Dropdowns/TaskCategory",
                require_helpdesk_visible=True,
                require_active=True,
            )

    def list_task_templates(self, access_token: str):
        collected = []
        start = 0
        while start < _CATEGORY_CAP:
            payload = self._json(
                "GET",
                "/api.php/v2.2/Dropdowns/TaskTemplate",
                token=access_token,
                params={"start": start, "limit": _CATEGORY_PAGE},
            )
            collected.extend(parse_task_templates(payload))
            if payload_row_count(payload) < _CATEGORY_PAGE:
                break
            start += _CATEGORY_PAGE
        return collected

    def list_task_statuses(self):
        return [Category(item_id, name) for item_id, name in TASK_STATUSES]

    def list_groups(self, access_token: str) -> list[Category]:
        return self._list_dropdown_pages(access_token, "/api.php/v2.2/Administration/Group")

    def list_validation_templates(self, access_token: str):
        from helpdesk_app.domain.models import TemplateCatalogItem
        from helpdesk_app.infrastructure.glpi.mapping import _results

        collected: list[TemplateCatalogItem] = []
        start = 0
        while start < _CATEGORY_CAP:
            payload = self._json(
                "GET",
                "/api.php/v2.2/Dropdowns/ValidationTemplate",
                token=access_token,
                params={"start": start, "limit": _CATEGORY_PAGE},
            )
            for row in _results(payload):
                if not isinstance(row, dict) or "id" not in row:
                    continue
                name = display_text(row.get("name"))
                if not name:
                    continue
                collected.append(
                    TemplateCatalogItem(
                        id=int(row["id"]),
                        name=name,
                        content=str(row.get("content") or ""),
                    )
                )
            if payload_row_count(payload) < _CATEGORY_PAGE:
                break
            start += _CATEGORY_PAGE
        return collected

    def list_approval_steps(self, access_token: str) -> list[Category]:
        return self._list_dropdown_pages(access_token, "/api.php/v2.2/Dropdowns/ApprovalStep")

    def list_urgencies(self):
        return list(URGENCIES)

    def list_tickets(self, access_token: str, query: TicketListQuery) -> TicketListPage:
        from helpdesk_app.infrastructure.glpi.legacy_ticket_search import (
            ticket_list_needs_legacy_actor_search,
        )

        if ticket_list_needs_legacy_actor_search(query):
            return self._list_tickets_via_legacy_search(access_token, query)
        params: dict[str, str | int] = {
            "start": query.start,
            "limit": query.limit,
            "sort": query.sort,
        }
        if query.filter:
            params["filter"] = query.filter
        payload = self._json(
            "GET",
            "/api.php/v2.2/Assistance/Ticket",
            token=access_token,
            params=params,
        )
        return parse_ticket_page(payload, query)

    def _list_tickets_via_legacy_search(
        self, access_token: str, query: TicketListQuery
    ) -> TicketListPage:
        """Discover ticket ids via classic Search; hydrate+ACL via OAuth HLAPI."""
        from helpdesk_app.infrastructure.glpi.legacy_ticket_search import (
            build_legacy_ticket_search_path_from_parts,
            parse_legacy_ticket_search,
        )

        self._legacy_require_ready()
        path = build_legacy_ticket_search_path_from_parts(
            q=query.q,
            status=query.status,
            urgency_id=query.urgency_id,
            category_id=query.category_id,
            updated_from=query.updated_from,
            updated_to=query.updated_to,
            created_from=query.created_from,
            created_to=query.created_to,
            assignee_id=query.assignee_id,
            sort=query.client_sort,
            page=query.page,
            page_size=query.page_size,
        )
        session_token = self._legacy_init_session()
        try:
            payload = self._legacy_get_json(session_token, path)
        finally:
            self._legacy_kill_session(session_token)

        searched = parse_legacy_ticket_search(
            payload if isinstance(payload, (dict, list)) else {},
            page=query.page,
            page_size=query.page_size,
        )
        if not searched.ticket_ids:
            return TicketListPage(
                items=(),
                page=query.page,
                page_size=query.page_size,
                has_more=False,
            )

        joined = ",".join(str(item) for item in searched.ticket_ids)
        hydrate = self._json(
            "GET",
            "/api.php/v2.2/Assistance/Ticket",
            token=access_token,
            params={
                "start": 0,
                "limit": len(searched.ticket_ids),
                "filter": f"is_deleted==false;id=in=({joined})",
                "sort": "id:asc",
            },
        )
        by_id = {row.id: row for row in parse_ticket_list(hydrate)}
        ordered = tuple(
            by_id[ticket_id]
            for ticket_id in searched.ticket_ids
            if ticket_id in by_id
        )
        return TicketListPage(
            items=ordered,
            page=query.page,
            page_size=query.page_size,
            has_more=searched.has_more,
        )

    def get_ticket(self, access_token: str, ticket_id: int, viewer_email: str = "") -> TicketDetail:
        ticket = self._json(
            "GET", f"/api.php/v2.2/Assistance/Ticket/{ticket_id}", token=access_token
        )
        timeline = self._json(
            "GET",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/Timeline",
            token=access_token,
        )
        validations_payload: dict | list = []
        try:
            validations_payload = self._json(
                "GET",
                f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/Timeline/Validation",
                token=access_token,
            )
        except (GlpiForbidden, GlpiNotFound, GlpiUnavailable, GlpiValidation):
            logger.info("glpi_ticket_validations_unavailable ticket_id=%s", ticket_id)
            validations_payload = []
        viewer = self._viewer_identity(access_token, viewer_email)
        detail = apply_viewer_identity(
            parse_ticket_detail(ticket, timeline),
            viewer,
        )
        validations = apply_validation_viewer(
            parse_ticket_validations(validations_payload),
            viewer,
        )
        named = tuple(self._named_attachment(access_token, item) for item in detail.attachments)
        return replace(
            detail,
            attachments=named,
            validations=validations,
            can_decide_validation=any(item.mine_to_decide for item in validations),
        )

    def decide_ticket_validation(
        self,
        access_token: str,
        ticket_id: int,
        validation_id: int,
        *,
        accept: bool,
        comment: str = "",
    ) -> None:
        """Approve or refuse a waiting TicketValidation via HLAPI PATCH."""
        ticket_id = int(ticket_id)
        validation_id = int(validation_id)
        if ticket_id <= 0 or validation_id <= 0:
            raise GlpiValidation("validation_id inválido.")
        status = 3 if accept else 4
        self._json(
            "PATCH",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/Timeline/Validation/{validation_id}",
            token=access_token,
            json_body={
                "status": status,
                "approval_comment": str(comment or ""),
            },
        )

    def _viewer_identity(self, access_token: str, viewer_email: str) -> PersonIdentity:
        try:
            session = self._json("GET", "/api.php/v2.2/session", token=access_token)
        except (GlpiForbidden, GlpiNotFound, GlpiUnavailable):
            logger.info("glpi_session_identity_unavailable")
            session = {}
        return parse_viewer_identity(session if isinstance(session, dict) else {}, viewer_email)

    def session_user_id(self, access_token: str) -> int | None:
        """GLPI OAuth session user id — authoritative viewer identity for this link."""
        identity = self._viewer_identity(access_token, "")
        user_id = int(identity.user_id or 0)
        return user_id if user_id > 0 else None

    def download_attachment(self, access_token: str, document_id: int) -> tuple[bytes, str]:
        response = self._request(
            "GET",
            f"/api.php/v2.2/Management/Document/{document_id}/Download",
            token=access_token,
            accept="application/octet-stream",
        )
        if len(response.content) > _MAX_ATTACHMENT_BYTES:
            raise GlpiValidation("O anexo excede o limite.")
        media = response.headers.get("content-type", "application/octet-stream").split(";")[0].strip()
        return response.content, media or "application/octet-stream"

    def create_ticket(
        self,
        access_token: str,
        *,
        title: str,
        description: str,
        category_id: int,
        urgency_id: int,
    ) -> int:
        body = create_ticket_body(
            title=title,
            description=description,
            category_id=category_id,
            urgency_id=urgency_id,
        )
        payload = self._json(
            "POST",
            "/api.php/v2.2/Assistance/Ticket",
            token=access_token,
            json_body=body,
        )
        return parse_created_id(payload)

    def add_ticket_observer(self, access_token: str, ticket_id: int, user_id: int) -> None:
        body = team_member_observer_body(user_id)
        self._json(
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{int(ticket_id)}/TeamMember",
            token=access_token,
            json_body=body,
        )

    def add_ticket_assignee(self, access_token: str, ticket_id: int, user_id: int) -> None:
        body = team_member_assigned_body(user_id)
        self._json(
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{int(ticket_id)}/TeamMember",
            token=access_token,
            json_body=body,
        )

    def remove_ticket_assignee(self, access_token: str, ticket_id: int, user_id: int) -> None:
        body = team_member_assigned_body(user_id)
        self._json(
            "DELETE",
            f"/api.php/v2.2/Assistance/Ticket/{int(ticket_id)}/TeamMember",
            token=access_token,
            json_body=body,
        )

    def list_users(self, access_token: str, *, q: str = "", limit: int = 20) -> list[CatalogUser]:
        safe_limit = max(1, min(int(limit or 20), 50))
        payload = self._json(
            "GET",
            "/api.php/v2.2/Administration/User",
            token=access_token,
            params={
                "start": 0,
                "limit": safe_limit,
                "filter": build_user_search_filter(q),
                "sort": "id:asc",
            },
        )
        return parse_catalog_users(payload)

    def list_technician_user_ids(self, access_token: str) -> set[int]:
        """GLPI user ids with an assignee profile (Technician by default).

        Prefer HLAPI Profile→User; fall back to legacy Profile_User when enabled.
        """
        _ = access_token
        if self._technician_ids_cache is not None:
            return set(self._technician_ids_cache)

        ids: set[int] = set()
        for profile_id in self._assignee_profile_ids:
            ids.update(self._list_user_ids_for_profile(access_token, int(profile_id)))

        self._technician_ids_cache = set(ids)
        logger.info(
            "glpi_technician_ids_resolved count=%s profiles=%s",
            len(ids),
            list(self._assignee_profile_ids),
        )
        return set(ids)

    def _list_user_ids_for_profile(self, access_token: str, profile_id: int) -> set[int]:
        # 1) HLAPI nested relation (when available on this GLPI build).
        try:
            payload = self._json(
                "GET",
                f"/api.php/v2.2/Administration/Profile/{int(profile_id)}/User",
                token=access_token,
                params={"start": 0, "limit": 500, "filter": "is_active==true", "sort": "id:asc"},
            )
            found = parse_profile_user_ids(payload)
            if found:
                return found
        except (GlpiValidation, GlpiNotFound, GlpiForbidden, GlpiUnavailable, GlpiUnauthorized):
            pass
        except Exception:
            logger.exception("glpi_hlapi_profile_users_failed profile_id=%s", profile_id)

        # 2) Legacy apirest — Technician token often lacks Profile_User nested read (403).
        # Prefer search/User (profiles_id field 20), proven on GLPI 11 prod.
        if not self._legacy_ready():
            return set()
        session_token = self._legacy_init_session()
        try:
            try:
                rows = self._legacy_get_json(
                    session_token,
                    f"/apirest.php/Profile/{int(profile_id)}/Profile_User?range=0-999",
                )
                found = parse_profile_user_ids(rows if isinstance(rows, (list, dict)) else [])
                if found:
                    return found
            except (GlpiForbidden, GlpiNotFound, GlpiValidation, GlpiUnavailable, GlpiUnauthorized):
                pass

            try:
                # search/Profile_User: field 3 = profiles_id, forcedisplay 2 = users_id
                search = self._legacy_get_json(
                    session_token,
                    (
                        "/apirest.php/search/Profile_User?"
                        f"criteria[0][field]=3&criteria[0][searchtype]=equals"
                        f"&criteria[0][value]={int(profile_id)}"
                        "&forcedisplay[0]=2&range=0-999"
                    ),
                )
                found = parse_profile_user_ids(search if isinstance(search, (list, dict)) else [])
                if found:
                    return found
            except (GlpiForbidden, GlpiNotFound, GlpiValidation, GlpiUnavailable, GlpiUnauthorized):
                pass

            # search/User: field 20 = profiles_id (name shown; equals by id works)
            search_users = self._legacy_get_json(
                session_token,
                (
                    "/apirest.php/search/User?"
                    f"criteria[0][field]=20&criteria[0][searchtype]=equals"
                    f"&criteria[0][value]={int(profile_id)}"
                    "&forcedisplay[0]=2&range=0-999"
                ),
            )
            return parse_profile_user_ids(
                search_users if isinstance(search_users, (list, dict)) else []
            )
        finally:
            self._legacy_kill_session(session_token)

    def find_user_by_email(self, access_token: str, email: str) -> CatalogUser | None:
        """Match GLPI user by emails[] in list payload (email is not an RSQL property)."""
        from helpdesk_app.infrastructure.glpi.mapping import _emails, _results

        normalized = str(email or "").strip().lower()
        if "@" not in normalized:
            return None
        local = normalized.split("@", 1)[0]
        # Local-part as name/username hint (ex.: michael@…); mailbox aliases (ti@) need name search.
        for query in (local,):
            try:
                payload = self._json(
                    "GET",
                    "/api.php/v2.2/Administration/User",
                    token=access_token,
                    params={
                        "start": 0,
                        "limit": 50,
                        "filter": build_user_search_filter(query),
                        "sort": "id:asc",
                    },
                )
            except (GlpiValidation, GlpiNotFound, GlpiForbidden, GlpiUnavailable, GlpiUnauthorized):
                continue
            matched_rows: list[dict] = []
            for row in _results(payload):
                if not isinstance(row, dict):
                    continue
                emails = {item.lower() for item in _emails(row)}
                if normalized in emails:
                    matched_rows.append(row)
            if matched_rows:
                users = parse_catalog_users(matched_rows)
                if users:
                    return replace(users[0], email=normalized)
        return None

    def can_assign_tickets(self, access_token: str) -> bool:
        """Backend-first capability: catalog-by-id must be readable (E0 G-A4)."""
        try:
            self.list_users(access_token, q="", limit=1)
            return True
        except GlpiForbidden:
            return False

    def add_followup(
        self,
        access_token: str,
        ticket_id: int,
        content: str,
        *,
        request_type_id: int | None = None,
    ) -> int:
        body: dict = {"content": content}
        if request_type_id is not None and int(request_type_id) > 0:
            body["request_type"] = {"id": int(request_type_id)}
        payload = self._json(
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/Timeline/Followup",
            token=access_token,
            json_body=body,
        )
        return parse_created_id(payload)

    def add_ticket_solution(
        self,
        access_token: str,
        ticket_id: int,
        content: str,
        *,
        solution_type_id: int | None = None,
    ) -> int:
        """Create ITILSolution via HLAPI Timeline/Solution (content required).

        Force public (``is_private=0``) so the BFF timeline and MFE conversation
        can confirm and display the entry — private solutions are stripped on read.
        ``solution_type_id`` maps to HLAPI ``type.id`` (SolutionType).
        """
        ticket_id = int(ticket_id)
        if ticket_id <= 0:
            raise GlpiValidation("ticket_id inválido.")
        body: dict = {"content": content, "is_private": 0}
        if solution_type_id is not None and int(solution_type_id) > 0:
            body["type"] = {"id": int(solution_type_id)}
        payload = self._json(
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/Timeline/Solution",
            token=access_token,
            json_body=body,
        )
        return parse_created_id(payload)

    def add_ticket_task(
        self,
        access_token: str,
        ticket_id: int,
        content: str,
        *,
        state: int | None = None,
        duration_seconds: int | None = None,
        category_id: int | None = None,
        user_tech_id: int | None = None,
        group_tech_id: int | None = None,
        planned_begin: str | None = None,
        planned_end: str | None = None,
    ) -> int:
        """Create TicketTask via HLAPI Timeline/Task (content required).

        Force public (``is_private=0``): GLPI often defaults tasks to private; private
        entries are omitted from Helpdesk timeline, which would break create-task
        confirmation and hide the task from the workspace conversation.

        ``duration_seconds`` maps to HLAPI ``duration`` (integer; unit matches provider).
        """
        ticket_id = int(ticket_id)
        if ticket_id <= 0:
            raise GlpiValidation("ticket_id inválido.")
        body: dict = {"content": content, "is_private": 0}
        if state is not None:
            state_i = int(state)
            if state_i not in {0, 1, 2}:
                raise GlpiValidation("state inválido.")
            body["state"] = state_i
        if duration_seconds is not None:
            duration_i = int(duration_seconds)
            if duration_i < 0:
                raise GlpiValidation("duration_seconds inválido.")
            body["duration"] = duration_i
        if category_id is not None and int(category_id) > 0:
            body["category"] = {"id": int(category_id)}
        if user_tech_id is not None and int(user_tech_id) > 0:
            body["user_tech"] = {"id": int(user_tech_id)}
        if group_tech_id is not None and int(group_tech_id) > 0:
            body["group_tech"] = {"id": int(group_tech_id)}
        if planned_begin:
            body["planned_begin"] = str(planned_begin).strip()
        if planned_end:
            body["planned_end"] = str(planned_end).strip()
        payload = self._json(
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/Timeline/Task",
            token=access_token,
            json_body=body,
        )
        return parse_created_id(payload)

    def create_ticket_validation(
        self,
        access_token: str,
        ticket_id: int,
        *,
        approver_user_id: int | None = None,
        approver_type: str = "User",
        approver_id: int | None = None,
        comment: str = "",
    ) -> int:
        """Request TicketValidation via HLAPI Timeline/Validation POST.

        Live-proven payload shape uses ``itemtype_target`` + ``items_id_target``
        (User). Group uses the same shape with ``itemtype_target=Group``.
        """
        ticket_id = int(ticket_id)
        if ticket_id <= 0:
            raise GlpiValidation("ticket_id inválido.")
        target_type = "Group" if str(approver_type).lower() == "group" else "User"
        target_id = approver_id if approver_id is not None else approver_user_id
        try:
            target_id = int(target_id) if target_id is not None else 0
        except (TypeError, ValueError) as exc:
            raise GlpiValidation("approver_id inválido.") from exc
        if target_id <= 0:
            raise GlpiValidation("approver_id inválido.")
        payload = self._json(
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/Timeline/Validation",
            token=access_token,
            json_body={
                "itemtype_target": target_type,
                "items_id_target": target_id,
                "comment_submission": str(comment or ""),
            },
        )
        return parse_created_id(payload)

    def upload_ticket_document(
        self,
        access_token: str,
        *,
        ticket_id: int,
        filename: str,
        content: bytes,
        mime: str,
        title: str | None = None,
    ) -> Attachment:
        """Upload via legacy apirest Document (HLAPI has no multipart). Product-authorized H12."""
        self._legacy_require_ready()
        if not content:
            raise GlpiValidation("Arquivo vazio.")
        if len(content) > self._legacy_max_upload_bytes:
            raise GlpiValidation("O anexo excede o limite.")
        safe_name = _safe_upload_filename(filename)
        display_title = (title or "").strip() or safe_name
        display_title = display_title[:180]
        ticket_id = int(ticket_id)
        if ticket_id <= 0:
            raise GlpiValidation("ticket_id inválido.")
        # Ensure the ticket is visible to this OAuth subject before legacy write.
        self._json("GET", f"/api.php/v2.2/Assistance/Ticket/{ticket_id}", token=access_token)
        session_token = self._legacy_init_session()
        try:
            document_id = self._legacy_post_document(
                session_token=session_token,
                ticket_id=ticket_id,
                filename=safe_name,
                content=content,
                mime=(mime or "application/octet-stream").split(";")[0].strip()
                or "application/octet-stream",
                title=display_title,
            )
            # UploadManifest items_id is not always enough for Timeline visibility.
            self._legacy_ensure_document_item(
                session_token=session_token,
                document_id=document_id,
                ticket_id=ticket_id,
            )
        finally:
            self._legacy_kill_session(session_token)
        return Attachment(document_id=document_id, filename=safe_name, mime=mime or "")

    def ticket_owns_document(self, access_token: str, ticket_id: int, document_id: int) -> bool:
        """True when Document_Item links document_id to this Ticket (legacy check).

        Caller must already have proven ticket ACL (get_ticket / GET Ticket).
        """
        ticket_id = int(ticket_id)
        document_id = int(document_id)
        if ticket_id <= 0 or document_id <= 0:
            return False
        # OAuth subject can see the ticket before we open the technical session.
        self._json("GET", f"/api.php/v2.2/Assistance/Ticket/{ticket_id}", token=access_token)
        if not self._legacy_ready():
            return False
        session_token = self._legacy_init_session()
        try:
            return self._legacy_document_linked_to_ticket(
                session_token=session_token,
                document_id=document_id,
                ticket_id=ticket_id,
            )
        finally:
            self._legacy_kill_session(session_token)

    def accept_ticket_solution(self, access_token: str, ticket_id: int, content: str = "") -> None:
        """Close solved ticket via legacy ITILFollowup add_close (H10 Branch B)."""
        self._legacy_cycle_write(
            access_token,
            ticket_id,
            content=content or "Solução aceita.",
            add_close=True,
            add_reopen=False,
        )

    def reject_ticket_solution(self, access_token: str, ticket_id: int, content: str = "") -> None:
        """Reopen solved/closed ticket via legacy ITILFollowup add_reopen (H10 Branch B)."""
        self._legacy_cycle_write(
            access_token,
            ticket_id,
            content=content or "Solução recusada.",
            add_close=False,
            add_reopen=True,
        )

    def get_ticket_satisfaction(
        self, access_token: str, ticket_id: int
    ) -> tuple[int, str] | None:
        """Return (score, comment) when TicketSatisfaction exists; else None."""
        ticket_id = int(ticket_id)
        if ticket_id <= 0:
            raise GlpiValidation("ticket_id inválido.")
        self._json("GET", f"/api.php/v2.2/Assistance/Ticket/{ticket_id}", token=access_token)
        if not self._legacy_ready():
            raise GlpiFeatureDisabled("Ciclo legado desligado neste ambiente.")
        session_token = self._legacy_init_session()
        try:
            rows = self._legacy_get_json(
                session_token, f"/apirest.php/Ticket/{ticket_id}/TicketSatisfaction"
            )
        finally:
            self._legacy_kill_session(session_token)
        if not isinstance(rows, list) or not rows:
            return None
        row = rows[0] if isinstance(rows[0], dict) else {}
        raw = row.get("satisfaction")
        if raw in (None, ""):
            return None
        try:
            score = int(raw)
        except (TypeError, ValueError):
            return None
        return score, str(row.get("comment") or "")

    def submit_ticket_satisfaction(
        self,
        access_token: str,
        ticket_id: int,
        *,
        satisfaction: int,
        comment: str = "",
    ) -> None:
        ticket_id = int(ticket_id)
        if ticket_id <= 0:
            raise GlpiValidation("ticket_id inválido.")
        if satisfaction not in {1, 2, 3, 4, 5}:
            raise GlpiValidation("satisfaction inválida.")
        self._legacy_require_ready()
        self._json("GET", f"/api.php/v2.2/Assistance/Ticket/{ticket_id}", token=access_token)
        session_token = self._legacy_init_session()
        try:
            self._legacy_post_json(
                session_token,
                "/apirest.php/TicketSatisfaction",
                {
                    "input": {
                        "tickets_id": ticket_id,
                        "satisfaction": int(satisfaction),
                        "comment": str(comment or ""),
                    }
                },
            )
        finally:
            self._legacy_kill_session(session_token)

    def legacy_cycle_enabled(self) -> bool:
        return self._legacy_ready()

    def _legacy_cycle_write(
        self,
        access_token: str,
        ticket_id: int,
        *,
        content: str,
        add_close: bool,
        add_reopen: bool,
    ) -> None:
        ticket_id = int(ticket_id)
        if ticket_id <= 0:
            raise GlpiValidation("ticket_id inválido.")
        self._legacy_require_ready()
        self._json("GET", f"/api.php/v2.2/Assistance/Ticket/{ticket_id}", token=access_token)
        body: dict = {
            "input": {
                "itemtype": "Ticket",
                "items_id": ticket_id,
                "content": content,
            }
        }
        if add_close:
            body["input"]["add_close"] = 1
        if add_reopen:
            body["input"]["add_reopen"] = 1
        session_token = self._legacy_init_session()
        try:
            self._legacy_post_json(session_token, "/apirest.php/ITILFollowup", body)
        finally:
            self._legacy_kill_session(session_token)

    def _legacy_ready(self) -> bool:
        return bool(
            self._legacy_upload_enabled and self._legacy_app_token and self._legacy_user_token
        )

    def _legacy_require_ready(self) -> None:
        if not self._legacy_upload_enabled:
            raise GlpiFeatureDisabled("Operação legada desligada neste ambiente.")
        if not self._legacy_app_token:
            raise GlpiFeatureDisabled("App-Token da API legada não configurado.")
        if not self._legacy_user_token:
            raise GlpiFeatureDisabled("User-Token da API legada não configurado.")

    def _legacy_get_json(self, session_token: str, path: str):
        try:
            response = self._http.request(
                "GET",
                f"{self._base}{path}",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "App-Token": self._legacy_app_token,
                    "Session-Token": session_token,
                },
            )
        except httpx.TimeoutException as exc:
            raise GlpiUnavailable("GLPI indisponível.") from exc
        logger.info("glpi_legacy_get path=%s status=%s", path, response.status_code)
        if response.status_code == 200:
            if not response.content:
                return []
            data = response.json()
            return data
        if response.status_code == 404:
            return []
        _raise_for_status(response, "GET", path)
        return []

    def _legacy_post_json(self, session_token: str, path: str, body: dict) -> dict:
        try:
            response = self._http.request(
                "POST",
                f"{self._base}{path}",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "App-Token": self._legacy_app_token,
                    "Session-Token": session_token,
                },
                json=body,
            )
        except httpx.TimeoutException as exc:
            raise GlpiUnavailable("GLPI indisponível.") from exc
        logger.info("glpi_legacy_post path=%s status=%s", path, response.status_code)
        if response.status_code in {200, 201}:
            data = response.json() if response.content else {}
            return data if isinstance(data, dict) else {"results": data}
        body_text = (response.text or "")[:300]
        if response.status_code == 400 and "Duplicate" in body_text:
            raise GlpiValidation("Pesquisa de satisfação já registrada.")
        _raise_for_status(response, "POST", path)
        return {}

    def _legacy_init_session(self) -> str:
        """Open apirest session with App-Token + dedicated user_token (H12/H10).

        OAuth Bearer is HLAPI-only. Legacy writes run as technical user after HLAPI ACL check.
        """
        try:
            response = self._http.request(
                "GET",
                f"{self._base}/apirest.php/initSession",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "App-Token": self._legacy_app_token,
                    "Authorization": f"user_token {self._legacy_user_token}",
                },
            )
        except httpx.TimeoutException as exc:
            raise GlpiUnavailable("GLPI indisponível.") from exc
        logger.info("glpi_legacy_init status=%s", response.status_code)
        if response.status_code == 200:
            data = response.json() if response.content else {}
            token = data.get("session_token") if isinstance(data, dict) else None
            if token:
                return str(token)
            raise GlpiUnavailable("API legada não devolveu session_token.")
        body = (response.text or "")[:240]
        logger.info("glpi_legacy_init_failed status=%s body=%s", response.status_code, body)
        raise GlpiUnavailable(
            "API legada recusou a sessão. Confira enable_api, App-Token cifrado e User-Token."
        )

    def _legacy_kill_session(self, session_token: str) -> None:
        try:
            self._http.request(
                "GET",
                f"{self._base}/apirest.php/killSession",
                headers={
                    "Accept": "application/json",
                    "App-Token": self._legacy_app_token,
                    "Session-Token": session_token,
                },
            )
        except httpx.HTTPError:
            logger.info("glpi_legacy_kill_failed")

    def _legacy_ensure_document_item(
        self,
        *,
        session_token: str,
        document_id: int,
        ticket_id: int,
    ) -> None:
        """POST Document_Item so Timeline/membership can see the upload (H12)."""
        if self._legacy_document_linked_to_ticket(
            session_token=session_token,
            document_id=document_id,
            ticket_id=ticket_id,
        ):
            return
        self.post_calls += 1
        try:
            response = self._http.post(
                f"{self._base}/apirest.php/Document_Item",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "App-Token": self._legacy_app_token,
                    "Session-Token": session_token,
                },
                json={
                    "input": {
                        "documents_id": int(document_id),
                        "itemtype": "Ticket",
                        "items_id": int(ticket_id),
                    }
                },
            )
        except httpx.TimeoutException as exc:
            raise GlpiUnavailable("GLPI indisponível.") from exc
        logger.info(
            "glpi_legacy_document_item status=%s document_id=%s ticket_id=%s",
            response.status_code,
            document_id,
            ticket_id,
        )
        if response.status_code in {200, 201}:
            return
        # Already linked / duplicate — treat as success for membership.
        if response.status_code in {400, 422}:
            body = (response.text or "")[:240]
            logger.info("glpi_legacy_document_item_dup_or_reject body=%s", body)
            if self._legacy_document_linked_to_ticket(
                session_token=session_token,
                document_id=document_id,
                ticket_id=ticket_id,
            ):
                return
            raise GlpiValidation("O GLPI não ligou o documento ao chamado.")
        if response.status_code == 401:
            raise GlpiUnauthorized("Sessão do GLPI recusada.")
        if response.status_code == 403:
            raise GlpiForbidden("O perfil no GLPI não permite esta ação.")
        raise GlpiUnavailable("GLPI indisponível.")

    def _legacy_document_linked_to_ticket(
        self,
        *,
        session_token: str,
        document_id: int,
        ticket_id: int,
    ) -> bool:
        try:
            response = self._http.request(
                "GET",
                f"{self._base}/apirest.php/Document/{int(document_id)}/Document_Item",
                headers={
                    "Accept": "application/json",
                    "App-Token": self._legacy_app_token,
                    "Session-Token": session_token,
                },
            )
        except httpx.TimeoutException:
            return False
        except httpx.HTTPError:
            return False
        if response.status_code != 200 or not response.content:
            return False
        try:
            data = response.json()
        except ValueError:
            return False
        rows = data if isinstance(data, list) else data.get("data") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            # Single object form
            if isinstance(data, dict) and data.get("itemtype"):
                rows = [data]
            else:
                return False
        for row in rows:
            if not isinstance(row, dict):
                continue
            itemtype = str(row.get("itemtype") or "")
            items_id = row.get("items_id")
            if isinstance(items_id, dict):
                items_id = items_id.get("id")
            try:
                linked = int(items_id)
            except (TypeError, ValueError):
                continue
            if itemtype == "Ticket" and linked == int(ticket_id):
                return True
        return False

    def _legacy_post_document(
        self,
        *,
        session_token: str,
        ticket_id: int,
        filename: str,
        content: bytes,
        mime: str,
        title: str | None = None,
    ) -> int:
        document_name = (title or "").strip() or filename
        manifest = {
            "input": {
                "name": document_name,
                "_filename": [filename],
                "itemtype": "Ticket",
                "items_id": ticket_id,
            }
        }
        self.post_calls += 1
        try:
            response = self._http.post(
                f"{self._base}/apirest.php/Document",
                headers={
                    "Accept": "application/json",
                    "App-Token": self._legacy_app_token,
                    "Session-Token": session_token,
                },
                files={
                    "uploadManifest": (None, json.dumps(manifest), "application/json"),
                    "filename[]": (filename, content, mime),
                },
            )
        except httpx.TimeoutException as exc:
            raise GlpiUnavailable("GLPI indisponível.") from exc
        logger.info("glpi_legacy_document status=%s", response.status_code)
        if response.status_code in {200, 201}:
            data = response.json() if response.content else {}
            if isinstance(data, dict):
                raw = data.get("id")
                if isinstance(raw, dict):
                    raw = raw.get("id")
                if raw is not None:
                    return int(raw)
            raise GlpiValidation("O GLPI não devolveu o id do documento.")
        if response.status_code == 401:
            raise GlpiUnauthorized("Sessão do GLPI recusada.")
        if response.status_code == 403:
            raise GlpiForbidden("O perfil no GLPI não permite esta ação.")
        if response.status_code in {400, 422}:
            body = (response.text or "")[:300]
            logger.info("glpi_legacy_document_rejected body=%s", body)
            raise GlpiValidation("O GLPI recusou o arquivo enviado.")
        raise GlpiUnavailable("GLPI indisponível.")

    def _named_attachment(self, access_token: str, item: Attachment) -> Attachment:
        if item.filename:
            return item
        payload = self._json(
            "GET",
            f"/api.php/v2.2/Management/Document/{item.document_id}",
            token=access_token,
        )
        return Attachment(
            document_id=item.document_id,
            filename=display_text(payload.get("filename") or payload.get("name")),
            mime=str(payload.get("mime") or item.mime),
        )

    def _form(self, path: str, data: dict) -> dict:
        return self._json("POST", path, form=data)

    def _json(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json_body: dict | None = None,
        form: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        response = self._request(method, path, token=token, json_body=json_body, form=form, params=params)
        if not response.content:
            return {}
        data = response.json()
        if not isinstance(data, dict):
            return {"results": data}
        return data

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json_body: dict | None = None,
        form: dict | None = None,
        params: dict | None = None,
        accept: str = "application/json",
    ) -> httpx.Response:
        headers = {"Accept": accept, "GLPI-API-Version": "2.2.0"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        attempts = _GET_ATTEMPTS if method == "GET" else 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            if method == "POST":
                self.post_calls += 1
            try:
                response = self._http.request(
                    method,
                    f"{self._base}{path}",
                    headers=headers,
                    params=params,
                    json=json_body,
                    data=form,
                )
            except httpx.TimeoutException as exc:
                last_error = exc
                if method != "GET" or attempt == attempts - 1:
                    logger.info("glpi_timeout method=%s path=%s", method, path)
                    raise GlpiUnavailable("GLPI indisponível.") from exc
                continue
            if response.status_code in {502, 503, 504} and method == "GET" and attempt < attempts - 1:
                continue
            _raise_for_status(response, method, path)
            return response
        logger.info("glpi_unavailable method=%s path=%s", method, path)
        raise GlpiUnavailable("GLPI indisponível.") from last_error


def _raise_for_status(response: httpx.Response, method: str, path: str) -> None:
    logger.info("glpi_response method=%s path=%s status=%s", method, path, response.status_code)
    if response.status_code == 401:
        raise GlpiUnauthorized("Sessão do GLPI recusada.")
    if response.status_code == 403:
        raise GlpiForbidden("O perfil no GLPI não permite esta ação.")
    if response.status_code == 404:
        raise GlpiNotFound("Chamado não encontrado.")
    if response.status_code in {400, 422}:
        raise GlpiValidation("O GLPI recusou os dados enviados.")
    if response.status_code >= 400:
        raise GlpiUnavailable("GLPI indisponível.")


def _safe_upload_filename(value: str) -> str:
    name = attachment_filename(value)
    cleaned = _SAFE_UPLOAD_NAME.sub("_", name).strip(" ._")
    return (cleaned or "anexo")[:180]
