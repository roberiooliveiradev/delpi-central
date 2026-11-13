"""G1-OWNER: resolve usuario ativo no diretorio Core usando o JWT do operador.

O Core e a unica autoridade sobre identidade de usuarios; sem acesso ao Core,
nao se cria ou transfere titularidade de um computador. Nunca registrar tokens.
"""
from __future__ import annotations

import httpx

from it_portal_app.config import settings
from it_portal_app.domain.errors import PersistenceUnavailableError, ValidationError


class CoreDirectoryOwnerResolver:
    """Consulta POST /me/directory/users/lookup, que retorna somente usuarios ativos."""

    def resolve(self, user_id: str, access_token: str) -> str:
        base = (settings.CORE_API_URL or "").strip().rstrip("/")
        if not base or not access_token:
            raise PersistenceUnavailableError(
                "owner_directory_unavailable", "Diretorio de colaboradores indisponivel."
            )
        try:
            response = httpx.post(
                f"{base}/me/directory/users/lookup",
                json={"ids": [user_id]},
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                timeout=5.0,
                follow_redirects=False,
            )
            if response.status_code != 200:
                raise PersistenceUnavailableError(
                    "owner_directory_unavailable", "Nao foi possivel validar o colaborador no Core."
                )
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise PersistenceUnavailableError(
                "owner_directory_unavailable", "Nao foi possivel consultar o diretorio do Core."
            ) from None

        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise PersistenceUnavailableError(
                "owner_directory_unavailable", "O diretorio do Core retornou dados inesperados."
            )
        for item in data["items"]:
            if not isinstance(item, dict):
                continue
            if item.get("id") != user_id:
                continue
            name = item.get("name")
            if isinstance(name, str) and 0 < len(name.strip()) <= 160:
                return name.strip()
            raise PersistenceUnavailableError(
                "owner_directory_unavailable", "O diretorio retornou um usuario sem nome valido."
            )
        raise ValidationError(
            "invalid_responsible_user",
            "O colaborador selecionado nao existe ou nao esta ativo no Core.",
            {"fields": {"responsible_user_id": "Selecione um colaborador ativo da plataforma."}},
        )
