"""S2S scope isolation and human read-only contract for #1576."""
import pytest

from delpi_auth.service_identity import ServiceIdentity
from delpi_auth.service_errors import ServiceScopeDeniedError
from it_portal_app.interface.http import s2s_auth
from it_portal_app.interface.http.dependencies import get_host_service_inventory
from it_portal_app.application.host_service_inventory import HostServiceInventory
from it_portal_app.main import app
from tests.conftest import server_payload
from tests.test_host_service_inventory import FakeInventory, payload

SCOPE = "it-portal.host-services.ingest"
CLIENT = "it-portal-windows-inventory-test"


@pytest.fixture
def s2s(monkeypatch):
    class Validator:
        def validate(self, token, *, required_scopes=None, allowed_clients=None):
            scopes = frozenset({SCOPE}) if token == "inventory-token" else frozenset({"it-portal.observations.ingest"})
            if not set(required_scopes or ()).issubset(scopes):
                raise ServiceScopeDeniedError("S2S_SCOPE_DENIED")
            return ServiceIdentity(
                client_id=CLIENT, subject=CLIENT, scopes=scopes,
                audience=("it-portal-api",), issuer="https://auth.example/realms/delpi",
            )
    monkeypatch.setattr(s2s_auth, "_shared_validator", Validator())


def test_ingest_requires_dedicated_scope_and_human_api_never_accepts_s2s(
    client, repository, principal, monkeypatch, s2s,
):
    host = client.post("/servers", json=server_payload()).json()["data"]
    monkeypatch.setenv("IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST", host["id"])
    monkeypatch.setenv("IT_PORTAL_WINDOWS_COLLECTOR_BINDINGS", CLIENT + "=" + host["id"])
    fake = FakeInventory()
    app.dependency_overrides[get_host_service_inventory] = lambda: HostServiceInventory(fake, repository)
    url = f"/collector/v1/servers/{host['id']}/host-services/batches"
    try:
        assert client.post(url, json=payload()).status_code == 401
        denied = client.post(url, json=payload(),
            headers={"X-Delpi-Service-Authorization": "Bearer observation-token"})
        assert denied.status_code == 403
        accepted = client.post(url, json=payload(),
            headers={"X-Delpi-Service-Authorization": "Bearer inventory-token"})
        assert accepted.status_code == 201
        assert accepted.json()["data"]["status"] == "complete"
        got = client.get(f"/servers/{host['id']}/host-services")
        assert got.status_code == 200
        assert got.json()["data"]["total"] == 1
        principal.permissions = ["it-portal.access"]
        forbidden = client.get(f"/servers/{host['id']}/host-services")
        assert forbidden.status_code == 403
    finally:
        app.dependency_overrides.pop(get_host_service_inventory, None)
