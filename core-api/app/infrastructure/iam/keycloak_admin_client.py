# app/infrastructure/iam/keycloak_admin_client.py

import requests
import os


class KeycloakAdminClient:
    def __init__(self):
        self.base_url = os.getenv("KEYCLOAK_ADMIN_URL", "http://keycloak:8080")
        self.realm = os.getenv("KEYCLOAK_ADMIN_REALM")
        self.client_id = os.getenv("KEYCLOAK_ADMIN_CLIENT_ID")
        self.client_secret = os.getenv("KEYCLOAK_ADMIN_CLIENT_SECRET")

        self._admin_token = None

    # =========================================================
    # AUTH
    # =========================================================

    def _get_admin_token(self):
        if self._admin_token:
            return self._admin_token

        url = f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"

        response = requests.post(
            url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )

        response.raise_for_status()
        self._admin_token = response.json()["access_token"]
        return self._admin_token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._get_admin_token()}",
            "Content-Type": "application/json",
        }

    # =========================================================
    # USERS
    # =========================================================

    def get_user_by_id(self, user_id: str):
        url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    # =========================================================
    # REALM ROLES
    # =========================================================

    def get_realm_role(self, role_name: str):
        url = f"{self.base_url}/admin/realms/{self.realm}/roles/{role_name}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def add_realm_roles_to_user(self, user_id: str, role_names: list[str]):
        roles = [self.get_realm_role(name) for name in role_names]

        url = (
            f"{self.base_url}/admin/realms/{self.realm}"
            f"/users/{user_id}/role-mappings/realm"
        )

        response = requests.post(url, headers=self._headers(), json=roles)
        response.raise_for_status()

    def remove_realm_roles_from_user(self, user_id: str, role_names: list[str]):
        roles = [self.get_realm_role(name) for name in role_names]

        url = (
            f"{self.base_url}/admin/realms/{self.realm}"
            f"/users/{user_id}/role-mappings/realm"
        )

        response = requests.delete(url, headers=self._headers(), json=roles)
        response.raise_for_status()

    # =========================================================
    # GROUPS
    # =========================================================

    def add_user_to_group(self, user_id: str, group_id: str):
        url = (
            f"{self.base_url}/admin/realms/{self.realm}"
            f"/users/{user_id}/groups/{group_id}"
        )

        response = requests.put(url, headers=self._headers())
        response.raise_for_status()

    def remove_user_from_group(self, user_id: str, group_id: str):
        url = (
            f"{self.base_url}/admin/realms/{self.realm}"
            f"/users/{user_id}/groups/{group_id}"
        )

        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()

    # =========================================================
    # REALMS
    # =========================================================
    def get_user_realm_roles(self, user_id: str):
        url = (
            f"{self.base_url}/admin/realms/{self.realm}"
            f"/users/{user_id}/role-mappings/realm"
        )
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()