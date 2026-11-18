"""Read-only S2S Portal RH hierarchy gateway; RH remains the sole authority.

Uses PORTAL_RH_API_URL and PORTAL_RH_API_SERVICE_TOKEN (the same secret
as PORTAL_RH_INTEGRATION_SERVICE_TOKEN on the RH host). No direct RH DB access.
"""

from __future__ import annotations

import os
from urllib.parse import quote

import httpx


class PortalRhOrganizationError(RuntimeError):
    """Sanitized upstream failure; never contains the service token."""


class PortalRhManagerNotFound(PortalRhOrganizationError):
    pass


class PortalRhOrganizationUnauthorized(PortalRhOrganizationError):
    pass


class PortalRhOrganizationUnavailable(PortalRhOrganizationError):
    pass


class PortalRhOrganizationContractError(PortalRhOrganizationError):
    pass


class PortalRhOrganizationGateway:
    _MAX_PAGES = 20
    _PAGE_SIZE = 500

    def __init__(
        self,
        *,
        base_url: str | None = None,
        service_token: str | None = None,
        timeout: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (
            base_url if base_url is not None else os.getenv("PORTAL_RH_API_URL", "")
        ).strip().rstrip("/")
        self.service_token = (
            service_token if service_token is not None
            else os.getenv("PORTAL_RH_API_SERVICE_TOKEN", "")
        ).strip()
        self.timeout = float(
            timeout if timeout is not None else os.getenv("PORTAL_RH_API_TIMEOUT", "5")
        )
        self.client = client

    @staticmethod
    def validate_registration(value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Matrícula deve ser texto.")
        registration = value.strip()
        if (
            not registration
            or len(registration) > 30
            or any(ch in registration for ch in "/?#\\\r\n\x00")
        ):
            raise ValueError("Matrícula inválida.")
        return registration

    def _get(self, path: str, *, params: dict | None = None) -> dict:
        if not self.base_url or not self.service_token:
            raise PortalRhOrganizationUnavailable("Integração Portal RH não configurada.")
        # Fail closed if an accidentally malformed URL would make httpx send the
        # S2S token to a non-HTTP endpoint.
        if not self.base_url.startswith(("https://", "http://")):
            raise PortalRhOrganizationUnavailable("URL do Portal RH inválida.")
        headers = {
            "X-Delpi-Service-Token": self.service_token,
            "Accept": "application/json",
        }
        try:
            if self.client is None:
                with httpx.Client(timeout=self.timeout, follow_redirects=False) as client:
                    response = client.get(self.base_url + path, headers=headers, params=params)
            else:
                response = self.client.get(
                    self.base_url + path, headers=headers, params=params
                )
        except httpx.HTTPError as exc:
            raise PortalRhOrganizationUnavailable("Portal RH indisponível.") from exc

        if response.status_code == 404:
            raise PortalRhManagerNotFound("Matrícula não encontrada no Portal RH.")
        if response.status_code in (401, 403):
            raise PortalRhOrganizationUnauthorized("Credencial Portal RH recusada.")
        if response.status_code != 200:
            raise PortalRhOrganizationUnavailable("Portal RH indisponível.")
        try:
            payload = response.json()
        except ValueError as exc:
            raise PortalRhOrganizationContractError("Resposta não é JSON válido.") from exc
        if not isinstance(payload, dict):
            raise PortalRhOrganizationContractError("Contrato Portal RH inválido.")
        return payload

    @staticmethod
    def _check_identity(row: object, expected_registration: str | None = None) -> dict:
        if not isinstance(row, dict):
            raise PortalRhOrganizationContractError("Identidade RH inválida.")
        registration = row.get("registration")
        if (
            not isinstance(row.get("id"), int)
            or isinstance(row.get("id"), bool)
            or not isinstance(registration, str)
            or not registration.strip()
            or not isinstance(row.get("full_name"), str)
            or not isinstance(row.get("branch_code"), str)
            or not isinstance(row.get("active"), bool)
        ):
            raise PortalRhOrganizationContractError("Identidade RH inválida.")
        if expected_registration is not None and registration != expected_registration:
            raise PortalRhOrganizationContractError("Matrícula RH divergente.")
        return row

    def get_collaborator(self, registration: str) -> dict:
        reg = self.validate_registration(registration)
        payload = self._get(
            "/api/v1/integrations/collaborators/" + quote(reg, safe="") + "/"
        )
        return self._check_identity(payload, reg)

    def get_team(
        self,
        manager_registration: str,
        *,
        include_indirect: bool = False,
        include_inactive: bool = False,
    ) -> dict:
        reg = self.validate_registration(manager_registration)
        members: list[dict] = []
        manager: dict | None = None
        seen_registrations: set[str] = set()

        for page in range(1, self._MAX_PAGES + 1):
            payload = self._get(
                "/api/v1/integrations/managers/" + quote(reg, safe="") + "/team/",
                params={
                    "include_indirect": str(bool(include_indirect)).lower(),
                    "include_inactive": str(bool(include_inactive)).lower(),
                    "page": page,
                    "page_size": self._PAGE_SIZE,
                },
            )
            current_manager = self._check_identity(payload.get("manager"), reg)
            if manager is None:
                manager = current_manager
            elif current_manager != manager:
                raise PortalRhOrganizationContractError("Gestor mudou durante a paginação.")
            rows = payload.get("members")
            has_next = payload.get("has_next")
            if not isinstance(rows, list) or not isinstance(has_next, bool):
                raise PortalRhOrganizationContractError("Paginação RH inválida.")
            for raw in rows:
                member = self._check_identity(raw)
                member_reg = member["registration"]
                if (
                    member_reg in seen_registrations
                    or member_reg == reg
                    or member.get("relationship") not in ("direct", "indirect")
                    or not isinstance(member.get("manager_registration"), str)
                ):
                    raise PortalRhOrganizationContractError("Hierarquia RH inválida.")
                seen_registrations.add(member_reg)
                members.append(member)
            if not has_next:
                return {
                    "manager": manager,
                    "members": members,
                    "includeIndirect": bool(include_indirect),
                    "includeInactive": bool(include_inactive),
                }
        raise PortalRhOrganizationContractError(
            "Equipe excede o limite seguro de paginação (10.000 colaboradores)."
        )
