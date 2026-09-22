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
    Category,
    PersonIdentity,
    TicketDetail,
    TicketListPage,
    TicketListQuery,
    TokenSet,
)
from helpdesk_app.infrastructure.glpi.mapping import (
    URGENCIES,
    apply_viewer_identity,
    create_ticket_body,
    display_text,
    parse_categories,
    parse_created_id,
    payload_row_count,
    parse_ticket_detail,
    parse_ticket_page,
    parse_token_set,
    parse_viewer_identity,
    team_member_observer_body,
    attachment_filename,
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

    def list_urgencies(self):
        return list(URGENCIES)

    def list_tickets(self, access_token: str, query: TicketListQuery) -> TicketListPage:
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

    def get_ticket(self, access_token: str, ticket_id: int, viewer_email: str = "") -> TicketDetail:
        ticket = self._json(
            "GET", f"/api.php/v2.2/Assistance/Ticket/{ticket_id}", token=access_token
        )
        timeline = self._json(
            "GET",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/Timeline",
            token=access_token,
        )
        detail = apply_viewer_identity(
            parse_ticket_detail(ticket, timeline),
            self._viewer_identity(access_token, viewer_email),
        )
        named = tuple(self._named_attachment(access_token, item) for item in detail.attachments)
        return replace(detail, attachments=named)

    def _viewer_identity(self, access_token: str, viewer_email: str) -> PersonIdentity:
        try:
            session = self._json("GET", "/api.php/v2.2/session", token=access_token)
        except (GlpiForbidden, GlpiNotFound, GlpiUnavailable):
            logger.info("glpi_session_identity_unavailable")
            session = {}
        return parse_viewer_identity(session if isinstance(session, dict) else {}, viewer_email)

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

    def add_followup(self, access_token: str, ticket_id: int, content: str) -> int:
        payload = self._json(
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/Timeline/Followup",
            token=access_token,
            json_body={"content": content},
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
    ) -> Attachment:
        """Upload via legacy apirest Document (HLAPI has no multipart). Product-authorized H12."""
        if not self._legacy_upload_enabled:
            raise GlpiFeatureDisabled("Upload de anexo desligado neste ambiente.")
        if not self._legacy_app_token:
            raise GlpiFeatureDisabled("App-Token da API legada não configurado.")
        if not self._legacy_user_token:
            raise GlpiFeatureDisabled("User-Token da API legada não configurado.")
        if not content:
            raise GlpiValidation("Arquivo vazio.")
        if len(content) > self._legacy_max_upload_bytes:
            raise GlpiValidation("O anexo excede o limite.")
        safe_name = _safe_upload_filename(filename)
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
            )
        finally:
            self._legacy_kill_session(session_token)
        return Attachment(document_id=document_id, filename=safe_name, mime=mime or "")

    def _legacy_init_session(self) -> str:
        """Open apirest session with App-Token + dedicated user_token (H12 Document only).

        OAuth Bearer is HLAPI-only. Upload runs as technical user after HLAPI ACL check.
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

    def _legacy_post_document(
        self,
        *,
        session_token: str,
        ticket_id: int,
        filename: str,
        content: bytes,
        mime: str,
    ) -> int:
        manifest = {
            "input": {
                "name": filename,
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
