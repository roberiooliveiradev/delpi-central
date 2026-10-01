"""Gateway S2S → diretório de colaboradores do Portal RH (C2).

Contrato: GET {base}/api/v1/integrations/collaborators/{registration}/
com X-Delpi-Service-Token: <PORTAL_RH_API_SERVICE_TOKEN> — credencial
própria do Portal RH, distinta do token da api-delpi. A matrícula é texto
opaco: só faz strip e URL-encoding — nunca int(), nunca lstrip("0").

Mapeamento: 404 → OperatorNotFound; 401/403 → OperatorDirectoryUnauthorized;
rede/timeout/5xx → OperatorDirectoryUnavailable; 200 fora do contrato →
OperatorDirectoryContractError. Token nunca vai para log.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import httpx

from production_control_app.config import settings
from production_control_app.domain.errors import (
    OperatorDirectoryContractError,
    OperatorDirectoryUnauthorized,
    OperatorDirectoryUnavailable,
    OperatorNotFound,
)
from production_control_app.domain.operator_identity import OperatorIdentity

logger = logging.getLogger(__name__)

_ENDPOINT = "/api/v1/integrations/collaborators"


class PortalRhOperatorDirectoryGateway:
    """Implementa OperatorDirectoryPort sobre HTTP S2S."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        service_token: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = (base_url or settings.PORTAL_RH_API_URL or "").rstrip("/")
        self._timeout = (
            timeout if timeout is not None else float(settings.PORTAL_RH_API_TIMEOUT)
        )
        self._service_token = (
            service_token
            if service_token is not None
            else (settings.PORTAL_RH_API_SERVICE_TOKEN or "")
        ).strip()
        self._client = client or httpx.Client(timeout=self._timeout)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def find_by_registration(self, registration: str) -> OperatorIdentity:
        reg = (registration or "").strip()
        if not self._base_url or not self._service_token:
            raise OperatorDirectoryUnavailable(
                "Diretório de colaboradores não configurado."
            )
        url = self._base_url + _ENDPOINT + "/" + quote(reg, safe="") + "/"
        try:
            response = self._client.get(
                url,
                headers={
                    "Accept": "application/json",
                    "X-Delpi-Service-Token": self._service_token,
                },
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.warning(
                "operator_directory_lookup_failed registration=%s error=%s",
                reg,
                type(exc).__name__,
            )
            raise OperatorDirectoryUnavailable(
                "Diretório de colaboradores indisponível."
            ) from exc

        status = response.status_code
        if status == 404:
            raise OperatorNotFound("Colaborador não encontrado.")
        if status in (401, 403):
            logger.error(
                "operator_directory_unauthorized registration=%s status=%s",
                reg,
                status,
            )
            raise OperatorDirectoryUnauthorized(
                "Integração com o diretório de colaboradores não autorizada.",
                status_code=status,
            )
        if status >= 400:
            logger.warning(
                "operator_directory_lookup_failed registration=%s status=%s",
                reg,
                status,
            )
            raise OperatorDirectoryUnavailable(
                "Diretório de colaboradores indisponível.",
                status_code=status,
            )
        return self._map_payload(reg, response)

    def _map_payload(self, reg: str, response: httpx.Response) -> OperatorIdentity:
        try:
            payload: Any = response.json()
        except ValueError as exc:
            raise OperatorDirectoryContractError(
                "Resposta do diretório não é JSON válido."
            ) from exc
        if not isinstance(payload, dict):
            raise OperatorDirectoryContractError(
                "Resposta do diretório fora do contrato."
            )
        # Campos extras do upstream são ignorados — só os 5 campos do contrato.
        external_id = payload.get("id")
        returned_reg = payload.get("registration")
        full_name = payload.get("full_name")
        branch_code = payload.get("branch_code")
        active = payload.get("active")
        valid = (
            isinstance(external_id, int)
            and not isinstance(external_id, bool)
            and isinstance(returned_reg, str)
            and returned_reg.strip() == reg
            and isinstance(full_name, str)
            and bool(full_name.strip())
            and isinstance(branch_code, str)
            and bool(branch_code.strip())
            and isinstance(active, bool)
        )
        if not valid:
            logger.warning(
                "operator_directory_contract_invalid registration=%s",
                reg,
            )
            raise OperatorDirectoryContractError(
                "Resposta do diretório fora do contrato."
            )
        return OperatorIdentity(
            external_id=external_id,
            registration=returned_reg.strip(),
            full_name=full_name.strip(),
            branch_code=branch_code.strip(),
            active=active,
        )
