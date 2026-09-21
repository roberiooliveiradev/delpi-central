import logging
from urllib.parse import quote

import httpx

from helpdesk_app.domain.errors import (
    GlpiForbidden,
    GlpiNotFound,
    GlpiUnauthorized,
    GlpiUnavailable,
    GlpiValidation,
)
from helpdesk_app.domain.models import Category, TicketDetail, TicketSummary, TokenSet
from helpdesk_app.infrastructure.glpi.mapping import (
    URGENCIES,
    create_ticket_body,
    parse_categories,
    parse_created_id,
    parse_ticket_detail,
    parse_ticket_list,
    parse_token_set,
)

logger = logging.getLogger("helpdesk.glpi")

_GET_ATTEMPTS = 3


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
        transport: httpx.BaseTransport | None = None,
    ):
        self._base = base_url.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._saml_idp_id = saml_idp_id.strip()
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
        payload = self._json("GET", "/api.php/v2.2/Dropdowns/ITILCategory", token=access_token)
        return parse_categories(payload)

    def list_urgencies(self):
        return list(URGENCIES)

    def list_tickets(self, access_token: str) -> list[TicketSummary]:
        payload = self._json("GET", "/api.php/v2.2/Assistance/Ticket", token=access_token)
        return parse_ticket_list(payload)

    def get_ticket(self, access_token: str, ticket_id: int) -> TicketDetail:
        ticket = self._json(
            "GET", f"/api.php/v2.2/Assistance/Ticket/{ticket_id}", token=access_token
        )
        timeline = self._json(
            "GET",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/Timeline",
            token=access_token,
        )
        return parse_ticket_detail(ticket, timeline)

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

    def add_followup(self, access_token: str, ticket_id: int, content: str) -> int:
        payload = self._json(
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/Timeline/Followup",
            token=access_token,
            json_body={"content": content},
        )
        return parse_created_id(payload)

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
    ) -> dict:
        headers = {"Accept": "application/json", "GLPI-API-Version": "2.2.0"}
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
            return _interpret(response, method, path)
        logger.info("glpi_unavailable method=%s path=%s", method, path)
        raise GlpiUnavailable("GLPI indisponível.") from last_error


def _interpret(response: httpx.Response, method: str, path: str) -> dict:
    logger.info("glpi_response method=%s path=%s status=%s", method, path, response.status_code)
    if response.status_code == 401:
        raise GlpiUnauthorized("Sessão do GLPI recusada.")
    if response.status_code == 403:
        raise GlpiForbidden("O perfil no GLPI não permite esta ação.")
    if response.status_code == 404:
        raise GlpiNotFound("Chamado não encontrado.")
    if response.status_code in {400, 422}:
        raise GlpiValidation("O GLPI recusou os dados enviados.")
    if response.status_code >= 500:
        raise GlpiUnavailable("GLPI indisponível.")
    if response.status_code >= 400:
        raise GlpiUnavailable("GLPI indisponível.")
    if not response.content:
        return {}
    data = response.json()
    if not isinstance(data, dict):
        return {"results": data}
    return data
