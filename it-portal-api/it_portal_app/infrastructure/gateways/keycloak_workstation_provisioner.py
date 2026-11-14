"""Keycloak Admin REST adapter for G2-S4; creates a DISABLED S2S client only.

Only a backend-only, narrowly delegated service principal may be configured.
No admin token/client secret is logged, stored in database or returned to browser.
Requires verified HTTPS and a dedicated (non-Core-admin) provisioner identity.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

import httpx

from it_portal_app.config import settings

CLIENT_RE = re.compile(r"^itp-ws-[0-9a-f]{32}$")
REALM_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,80}$")


class KeycloakWorkstationProvisioner:
    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        self.transport = transport

    @staticmethod
    def _config() -> tuple[str, str, str, str]:
        base = str(settings.WORKSTATION_KC_ADMIN_URL or "").rstrip("/")
        realm = str(settings.WORKSTATION_KC_REALM or "")
        admin_client = str(settings.WORKSTATION_KC_PROVISIONER_CLIENT_ID or "")
        admin_secret = str(settings.WORKSTATION_KC_PROVISIONER_CLIENT_SECRET or "")
        url = urlsplit(base)
        if (url.scheme != "https" or not url.hostname or url.username or url.password
                or url.query or url.fragment or not REALM_RE.fullmatch(realm)
                or not admin_client or not admin_secret
                or admin_client in ("admin-cli", "delpi-core-admin")):
            raise RuntimeError("G2-S4 Keycloak administrativo HTTPS nao configurado.")
        return base, realm, admin_client, admin_secret

    def create_disabled(self, client_id: str, workstation_id: str) -> str:
        if not CLIENT_RE.fullmatch(client_id):
            raise ValueError("Identidade de computador invalida.")
        base, realm, admin_client, admin_secret = self._config()
        endpoint = f"{base}/admin/realms/{realm}/clients"
        token_url = f"{base}/realms/{realm}/protocol/openid-connect/token"
        attrs = {
            "delpi.owner": "it-portal-workstation-v1",
            "delpi.workstation_id": workstation_id,
        }
        representation = {
            "clientId": client_id,
            "name": "IT Portal workstation inventory (disabled)",
            "description": "G2-S4: identity reserved, no active agent or remote access",
            "protocol": "openid-connect",
            "enabled": False,
            "publicClient": False,
            "clientAuthenticatorType": "client-secret",
            "serviceAccountsEnabled": True,
            "standardFlowEnabled": False,
            "implicitFlowEnabled": False,
            "directAccessGrantsEnabled": False,
            "authorizationServicesEnabled": False,
            "fullScopeAllowed": False,
            "redirectUris": [],
            "webOrigins": [],
            "defaultClientScopes": [],
            "optionalClientScopes": [],
            "protocolMappers": [],
            "attributes": attrs,
        }
        with httpx.Client(
            transport=self.transport, timeout=5.0, follow_redirects=False, verify=True,
            headers={"Accept": "application/json"},
        ) as client:
            token = client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": admin_client,
                    "client_secret": admin_secret,
                },
            )
            if token.status_code != 200:
                raise RuntimeError("Autenticacao do provisionador Keycloak falhou.")
            value = token.json()
            access = value.get("access_token") if isinstance(value, dict) else None
            if not isinstance(access, str) or not access:
                raise RuntimeError("Token administrativo ausente.")
            headers = {"Authorization": f"Bearer {access}"}
            created = client.post(endpoint, json=representation, headers=headers)
            if created.status_code != 201:
                # 409 exige reconciliacao, nunca adocao automatica do client existente.
                raise RuntimeError("Client Keycloak nao criado; revisar estado do provisionamento.")
            lookup = client.get(
                endpoint, params={"clientId": client_id, "search": "false"}, headers=headers
            )
            if lookup.status_code != 200:
                raise RuntimeError("Client criado mas nao foi possivel verificar seu estado.")
            records = lookup.json()
            if not isinstance(records, list):
                raise RuntimeError("Resposta Keycloak inesperada.")
            exact = [r for r in records if isinstance(r, dict) and r.get("clientId") == client_id]
            if len(exact) != 1:
                raise RuntimeError("Client Keycloak nao e unico.")
            info = exact[0]
            keycloak_id = info.get("id")
            if not isinstance(keycloak_id, str) or not re.fullmatch(
                r"[a-fA-F0-9-]{36}", keycloak_id
            ):
                raise RuntimeError("UUID Keycloak invalido.")
            # Read-back after create: fail closed if Keycloak applies unexpected defaults.
            detail = client.get(f"{endpoint}/{keycloak_id}", headers=headers)
            if detail.status_code != 200:
                raise RuntimeError("Client Keycloak sem leitura de verificacao.")
            observed = detail.json()
            if (not isinstance(observed, dict)
                    or observed.get("enabled") is not False
                    or observed.get("publicClient") is not False
                    or observed.get("fullScopeAllowed") is not False
                    or observed.get("serviceAccountsEnabled") is not True
                    or observed.get("standardFlowEnabled") is not False
                    or observed.get("directAccessGrantsEnabled") is not False
                    or observed.get("implicitFlowEnabled") is not False
                    or observed.get("attributes", {}).get("delpi.workstation_id") != workstation_id
                    or observed.get("attributes", {}).get("delpi.owner") != attrs["delpi.owner"]):
                raise RuntimeError("Client Keycloak nao atende o contrato de seguranca.")
            # Keycloak realms may add default/optional scopes automatically.
            # Remove them from this still DISABLED client, then verify no grants.
            for collection in ("default-client-scopes", "optional-client-scopes"):
                scopes_url = f"{endpoint}/{keycloak_id}/{collection}"
                scopes = client.get(scopes_url, headers=headers)
                if scopes.status_code != 200 or not isinstance(scopes.json(), list):
                    raise RuntimeError("Scopes Keycloak nao puderam ser verificados.")
                for scope in scopes.json():
                    scope_id = scope.get("id") if isinstance(scope, dict) else None
                    if not isinstance(scope_id, str) or not re.fullmatch(r"[a-fA-F0-9-]{36}", scope_id):
                        raise RuntimeError("Scope Keycloak nao verificavel.")
                    removed = client.delete(f"{scopes_url}/{scope_id}", headers=headers)
                    if removed.status_code not in (200, 204):
                        raise RuntimeError("Nao foi possivel remover scope padrao.")
                after = client.get(scopes_url, headers=headers)
                if after.status_code != 200 or after.json() != []:
                    raise RuntimeError("Client ainda possui scopes inesperados.")
            return keycloak_id
