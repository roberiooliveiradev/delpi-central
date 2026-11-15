"""No-network checks for bounded mcp-linux-ops Keycloak registration."""
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("keycloak_linux_ops_client", SCRIPTS / "keycloak_linux_ops_client.py")
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

RESOURCE = "https://minhadelpi.com.br/apps/linux-ops-mcp/mcp"
CALLBACK = "https://chatgpt.com/connector_platform_oauth_redirect"


class MockAdmin:
    def __init__(self):
        self.calls = []
        self.client = None
        self.scope = None
        self.mapper = None
        self.shared_audience_mapper = {
            "protocolMapper": "oidc-audience-mapper",
            "config": {
                "included.custom.audience": "delpi-central",
                "access.token.claim": "true",
            },
        }
        self.defaults = []
        self.base_scopes = [
            {"name": name, "id": "id-" + name}
            for name in m.DEFAULT_SCOPE_NAMES
        ]

    def call(self, method, path, body=None, tolerate=()):
        self.calls.append((method, path))
        if method not in {"GET", "POST", "PUT"}:
            raise AssertionError("unexpected method")
        if method == "GET":
            if path == "/realms/delpi":
                return 200, {"realm": "delpi"}
            if path == "/realms/delpi/client-scopes":
                return 200, self.base_scopes + (
                    [{"id": "scope-linux", "name": m.DEDICATED_SCOPE}] if self.scope else []
                )
            if path.startswith("/realms/delpi/clients?clientId="):
                return 200, [{"id": "client-uuid", "clientId": m.CLIENT}] if self.client else []
            if path == "/realms/delpi/clients/client-uuid":
                return 200, self.client
            if path == "/realms/delpi/clients/client-uuid/default-client-scopes":
                return 200, [{"id": v} for v in self.defaults]
            if path == "/realms/delpi/client-scopes/scope-linux/protocol-mappers/models":
                return 200, [self.mapper] if self.mapper else []
            if path == "/realms/delpi/client-scopes/id-audience-delpi/protocol-mappers/models":
                return 200, [self.shared_audience_mapper] if self.shared_audience_mapper else []
            raise AssertionError(path)
        if method == "POST":
            if path == "/realms/delpi/clients":
                self.client = dict(body)
            elif path == "/realms/delpi/client-scopes":
                self.scope = True
            elif path == "/realms/delpi/client-scopes/scope-linux/protocol-mappers/models":
                self.mapper = dict(body)
            else:
                raise AssertionError(path)
        if method == "PUT":
            prefix = "/realms/delpi/clients/client-uuid/default-client-scopes/"
            assert path.startswith(prefix)
            self.defaults.append(path.removeprefix(prefix))
        return 201, None


def config(callback=CALLBACK):
    return m.Config("https://minhadelpi.com.br/auth", "delpi", RESOURCE, callback)


def test_check_has_no_writes_even_with_missing_client():
    a = MockAdmin()
    issues = m.Provisioner(a, config()).audit()
    assert "dedicated OAuth client absent" in issues
    assert all(method == "GET" for method, _ in a.calls)


def test_apply_without_exact_callback_fails_before_writes():
    a = MockAdmin()
    with pytest.raises(m.ContractError):
        m.Provisioner(a, config("")).apply()
    assert not a.calls


def test_apply_creates_only_target_client_and_dedicated_scope():
    a = MockAdmin()
    p = m.Provisioner(a, config())
    p.apply()
    assert p.audit() == []
    paths = [path for method, path in a.calls if method in {"POST", "PUT"}]
    assert paths.count("/realms/delpi/clients") == 1
    assert paths.count("/realms/delpi/client-scopes") == 1
    assert paths.count("/realms/delpi/client-scopes/scope-linux/protocol-mappers/models") == 1
    assert all(path.startswith("/realms/delpi/clients/client-uuid/default-client-scopes/")
               for path in paths[3:])
    a.calls.clear()
    p.apply()
    assert all(method == "GET" for method, _ in a.calls)


def test_unknown_preexisting_client_fails_closed():
    a = MockAdmin()
    a.client = {**m.CLIENT_FLAGS,
                "attributes": {"pkce.code.challenge.method": "S256"},
                "redirectUris": ["https://chatgpt.com/unexpected"],
                "webOrigins": []}
    with pytest.raises(m.ContractError, match="callback drift"):
        m.Provisioner(a, config()).apply()
    assert all(method == "GET" for method, _ in a.calls)


@pytest.mark.parametrize("uri", [
    "http://chatgpt.com/callback",
    "https://chatgpt.com/",
    "https://evil.example/callback",
    "https://chatgpt.com.evil.example/callback",
    "https://chatgpt.com/callback*",
    "https://chatgpt.com/callback?token=foo",
    "https://chatgpt.com/callback#fragment",
    "https://chatgpt.com:444/callback",
    "",
])
def test_callback_rejects_untrusted_variants(uri):
    assert not m.valid_callback(uri)


def test_callback_accepts_exact_platform_host():
    assert m.valid_callback(CALLBACK)


def test_resource_requires_expected_origin_and_path():
    assert m.strict_resource("https://minhadelpi.com.br", RESOURCE) == RESOURCE
    with pytest.raises(m.ContractError):
        m.strict_resource("https://minhadelpi.com.br",
                          "https://evil.example/apps/linux-ops-mcp/mcp")


def test_shared_platform_audience_wrong_prevents_all_writes():
    a = MockAdmin()
    a.shared_audience_mapper["config"]["included.custom.audience"] = "wrong-audience"
    assert "shared platform audience mapper missing or invalid" in m.Provisioner(a, config()).audit()
    with pytest.raises(m.ContractError, match="shared platform audience mapper"):
        m.Provisioner(a, config()).apply()
    assert all(method == "GET" for method, _ in a.calls)
    assert a.client is None


def test_existing_dedicated_scope_mismatch_blocks_client_creation():
    a = MockAdmin()
    a.scope = True
    a.mapper = {
        "protocolMapper": "oidc-audience-mapper",
        "config": {
            "included.custom.audience": "https://evil.example/mcp",
            "access.token.claim": "true",
        },
    }
    assert "dedicated scope audience mapper differs" in m.Provisioner(a, config()).audit()
    with pytest.raises(m.ContractError, match="unexpected mapper in dedicated scope"):
        m.Provisioner(a, config()).apply()
    assert all(method == "GET" for method, _ in a.calls)
    assert a.client is None
