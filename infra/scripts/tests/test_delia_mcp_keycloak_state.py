"""Provisioner safety tests — PROD-MCP-RUNTIME-ALIGNMENT-01.

In-memory fake of the Keycloak Admin REST surface consumed by
infra/scripts/delia_mcp_keycloak_state.py. No real Keycloak, no network,
no secrets — every mutation lands on a dict.

Run:  python3 -m pytest infra/scripts/tests/ -q
"""

from __future__ import annotations

import os
import re
import sys
import urllib.parse

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

import delia_mcp_keycloak_state as mod  # noqa: E402


# ---------------------------------------------------------------------
# Fake Keycloak Admin REST
# ---------------------------------------------------------------------

class FakeKcAdmin(mod.KcAdmin):
    """In-memory KcAdmin: same call() contract, state in dicts."""

    def __init__(self) -> None:
        super().__init__("https://kc.example/auth", "fake-admin-token")
        self.realms = {"delpi": {"enabled": True}}
        self.clients: dict[str, dict] = {}
        self.client_scopes: dict[str, dict] = {}
        self.scope_mappers: dict[str, list] = {}
        self.default_scopes: dict[str, set] = {}
        self.client_mappers: dict[str, list] = {}
        self.policies: dict[str, dict] = {}
        self.mgmt_enabled: dict[str, bool] = {}
        self.permissions: dict[str, dict] = {}
        self._seq = 0
        self.calls: list[tuple[str, str]] = []

    def _id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}-{self._seq:04d}"

    # -- seeds --------------------------------------------------------

    def add_client(self, client_id: str, **flags) -> str:
        uuid_ = self._id("client")
        self.clients[uuid_] = {
            "id": uuid_, "clientId": client_id, "enabled": True,
            "protocol": "openid-connect",
            "publicClient": True, "standardFlowEnabled": True,
            "implicitFlowEnabled": False,
            "directAccessGrantsEnabled": True,
            "serviceAccountsEnabled": False,
            "attributes": {},
            **flags,
        }
        return uuid_

    def add_scope(self, name: str) -> str:
        sid = self._id("scope")
        self.client_scopes[sid] = {"id": sid, "name": name,
                                   "protocol": "openid-connect"}
        return sid

    def seed_builtins(self) -> None:
        for name in ("openid", "profile", "email"):
            self.add_scope(name)

    def seed_portal(self) -> None:
        self.add_client("delpi-central", publicClient=True,
                        directAccessGrantsEnabled=True)
        self.add_client("realm-management")

    # -- dispatch -----------------------------------------------------

    def call(self, method, path, body=None, tolerate=()):
        self.calls.append((method, path))
        if method not in ("GET", "HEAD"):
            self.writes.append((method, path))
        try:
            return self._dispatch(method, path, body)
        except _Http as exc:
            if exc.code in tolerate:
                return exc.code, None
            raise

    def _dispatch(self, method, path, body):
        m = re.match(r"/realms/([^/]+)(/.*)?$", path)
        if not m:
            raise _Http(404)
        realm, rest = m.group(1), m.group(2) or ""
        if realm not in self.realms:
            raise _Http(404)

        if rest == "" and method == "GET":
            return 200, self.realms[realm]

        m2 = re.match(r"/clients\?clientId=(.+)$", rest)
        if m2 and method == "GET":
            cid = urllib.parse.unquote(m2.group(1))
            rows = [c for c in self.clients.values()
                    if c["clientId"] == cid]
            return 200, rows

        if rest == "/clients" and method == "POST":
            cid = body["clientId"]
            if any(c["clientId"] == cid for c in self.clients.values()):
                raise _Http(409)
            uuid_ = self.add_client(cid)
            self.clients[uuid_].update(
                {k: v for k, v in body.items() if k != "id"})
            self.clients[uuid_]["id"] = uuid_
            self.clients[uuid_]["clientId"] = cid
            return 201, None

        m3 = re.match(r"/clients/([^/?]+)(/.*)?$", rest)
        if not m3:
            raise _Http(404)
        uuid_, sub = m3.group(1), m3.group(2) or ""
        if uuid_ not in self.clients:
            raise _Http(404)

        if sub == "" and method == "GET":
            return 200, dict(self.clients[uuid_])
        if sub == "" and method == "PUT":
            self.clients[uuid_].update(body)
            self.clients[uuid_]["id"] = uuid_
            return 200, None

        if sub == "/protocol-mappers/models":
            if method == "GET":
                return 200, self.client_mappers.get(uuid_, [])
            if method == "POST":
                self.client_mappers.setdefault(uuid_, []).append(body)
                return 201, None

        if sub == "/default-client-scopes" and method == "GET":
            return 200, [{"id": sid} for sid
                         in self.default_scopes.get(uuid_, set())]
        m4 = re.match(r"/default-client-scopes/(.+)$", sub)
        if m4 and method == "PUT":
            self.default_scopes.setdefault(uuid_, set()).add(m4.group(1))
            return 204, None

        if sub == "/client-secret" and method == "GET":
            return 200, {"value": "fake-secret-never-printed"}

        if sub == "/management/permissions":
            if method == "PUT":
                self.mgmt_enabled[uuid_] = True
                self.permissions.setdefault(uuid_, {
                    "enabled": True,
                    "resource": self._id("res"),
                    "scopePermissions": {"token-exchange":
                                         self._id("perm")}})
                return 200, self.permissions[uuid_]
            if method == "GET":
                # real KC26 returns {"enabled": false} (HTTP 200) on a
                # fresh client — not a 404.
                if not self.mgmt_enabled.get(uuid_):
                    return 200, {"enabled": False}
                return 200, self.permissions[uuid_]

        m5 = re.match(
            r"/authz/resource-server/policy\?name=(.+)$", sub)
        if m5 and method == "GET":
            name = urllib.parse.unquote(m5.group(1))
            return 200, [p for p in self.policies.values()
                         if p["name"] == name]
        if sub == "/authz/resource-server/policy/client" \
                and method == "POST":
            pid = self._id("policy")
            self.policies[pid] = {**body, "id": pid}
            return 201, self.policies[pid]
        m6 = re.match(
            r"/authz/resource-server/policy/client/(.+)$", sub)
        if m6 and method == "DELETE":
            self.policies.pop(m6.group(1), None)
            return 204, None

        m7 = re.match(
            r"/authz/resource-server/permission/scope/([^/]+)(/.*)?$",
            sub)
        if m7:
            perm_id, tail = m7.group(1), m7.group(2) or ""
            if tail == "/associatedPolicies" and method == "GET":
                pols = [self.policies[pid] for pid in self.policies
                        if perm_id in self.policies[pid].get("on", set())]
                return 200, pols
            if tail == "/scopes" and method == "GET":
                return 200, [{"id": self._id("psc"),
                              "name": "token-exchange"}]
            if tail == "" and method == "PUT":
                for pid in self.policies:          # stale binding cleanup
                    self.policies[pid].get("on", set()).discard(perm_id)
                for pid in body.get("policies") or []:
                    self.policies[pid].setdefault("on", set()).add(perm_id)
                return 200, None

        raise _Http(404)

    # client-scopes live at realm level, not under a client uuid —
    # handled before the client uuid match:
    def _dispatch_scopes(self, method, rest, body):
        return None


class _Http(Exception):
    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


# patch: client-scopes endpoints are realm-level — FakeKcAdmin.call must
# route them before the /clients/{uuid} branch. Easiest: wrap dispatch.
_orig = FakeKcAdmin._dispatch


def _dispatch_with_scopes(self, method, path, body):
    m = re.match(r"/realms/([^/]+)(/.*)?$", path)
    if m and m.group(1) in self.realms:
        rest = m.group(2) or ""
        if rest == "/client-scopes":
            if method == "GET":
                return 200, list(self.client_scopes.values())
            if method == "POST":
                if any(s["name"] == body["name"]
                       for s in self.client_scopes.values()):
                    raise _Http(409)
                sid = self.add_scope(body["name"])
                self.client_scopes[sid].update(body)
                self.client_scopes[sid]["id"] = sid
                return 201, None
        mm = re.match(
            r"/client-scopes/([^/]+)/protocol-mappers/models$", rest)
        if mm:
            sid = mm.group(1)
            if method == "GET":
                return 200, self.scope_mappers.get(sid, [])
            if method == "POST":
                self.scope_mappers.setdefault(sid, []).append(body)
                return 201, None
    return _orig(self, method, path, body)


FakeKcAdmin._dispatch = _dispatch_with_scopes


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

PUB = "https://minhadelpi.com.br"


def make_provisioner(fake: FakeKcAdmin, apply_: bool,
                     strategy: str = "KC24_LEGACY") -> mod.Provisioner:
    return mod.Provisioner(fake, realm="delpi",
                           portal_client_id="delpi-central",
                           public_base_url=PUB, apply=apply_,
                           strategy=strategy)


@pytest.fixture()
def fake() -> FakeKcAdmin:
    f = FakeKcAdmin()
    f.seed_builtins()
    f.seed_portal()
    return f


@pytest.fixture()
def converged(fake: FakeKcAdmin) -> FakeKcAdmin:
    """Fully applied state — returned after a clean --apply."""
    p = make_provisioner(fake, apply_=True)
    p.converge()
    return fake


def mutate_writes(fake: FakeKcAdmin) -> list[tuple[str, str]]:
    return [w for w in fake.calls if w[0] in ("POST", "PUT", "DELETE")]


# ---------------------------------------------------------------------
# AC tests
# ---------------------------------------------------------------------

def test_check_mode_writes_nothing_on_empty_state(fake):
    p = make_provisioner(fake, apply_=False)
    report = p.converge()
    assert not report.converged          # drift expected on empty state
    assert mutate_writes(fake) == []     # zero writes in check mode


def test_check_mode_is_readonly_even_when_converged(converged):
    converged.calls.clear()
    p = make_provisioner(converged, apply_=False)
    report = p.converge()
    assert report.converged
    assert mutate_writes(converged) == []


def test_apply_creates_bounded_scope(fake):
    p = make_provisioner(fake, apply_=True)
    p.converge()
    client_ids = {c["clientId"] for c in fake.clients.values()}
    assert {"mcp-api-delpi", "mcp-transformometro",
            "mcp-tv-dashboard", "delia-api"} <= client_ids
    # scope surface
    scope_names = {s["name"] for s in fake.client_scopes.values()}
    assert {"mcp:tools", "mcp-audience-api-delpi",
            "mcp-audience-transformometro",
            "mcp-audience-tv-dashboard",
            "audience-delpi"} <= scope_names


def test_apply_is_idempotent(fake):
    p1 = make_provisioner(fake, apply_=True)
    p1.converge()
    fake.calls.clear()
    p2 = make_provisioner(fake, apply_=True)
    p2._client_uuid_cache.clear()
    report = p2.converge()
    assert mutate_writes(fake) == []          # second run: zero writes
    assert report.converged


def test_missing_realm_fails_closed():
    fake = FakeKcAdmin()                       # realm 'delpi' absent
    p = make_provisioner(fake, apply_=False)
    with pytest.raises(mod.ProvisioningError, match="realm"):
        p.preflight()


def test_missing_portal_client_fails_closed():
    fake = FakeKcAdmin()                       # realm exists, portal not
    p = make_provisioner(fake, apply_=False)
    with pytest.raises(mod.ProvisioningError, match="portal client"):
        p.preflight()


def test_strategy_version_matrix():
    # KC24 legacy contract only on Keycloak 24
    assert 24 in mod.STRATEGY_MAJORS["KC24_LEGACY"]
    # KC26 contract only on Keycloak 26
    assert 26 in mod.STRATEGY_MAJORS["KC26_STANDARD"]
    assert mod._major("24.0.5") in mod.STRATEGY_MAJORS["KC24_LEGACY"]
    assert mod._major("26.0.7") in mod.STRATEGY_MAJORS["KC26_STANDARD"]
    assert mod._major("26.8.0") in mod.STRATEGY_MAJORS["KC26_STANDARD"]


def test_existing_correct_resources_unchanged(converged):
    before = {u: dict(c) for u, c in converged.clients.items()}
    p = make_provisioner(converged, apply_=True)
    p._client_uuid_cache.clear()
    p.converge()
    for u, c in converged.clients.items():
        for k, v in before[u].items():
            assert c.get(k) == v or k == "attributes"


def test_incompatible_resource_config_repaired(fake):
    p0 = make_provisioner(fake, apply_=True)
    p0.converge()
    # simulate drift: DAVI client became public + direct grants on
    davi = next(c for c in fake.clients.values()
                if c["clientId"] == "mcp-api-delpi")
    davi["publicClient"] = True
    davi["directAccessGrantsEnabled"] = True
    p1 = make_provisioner(fake, apply_=True)
    p1._client_uuid_cache.clear()
    p1.converge()
    davi = next(c for c in fake.clients.values()
                if c["clientId"] == "mcp-api-delpi")
    assert davi["publicClient"] is False
    assert davi["directAccessGrantsEnabled"] is False


def test_check_reports_drift_without_writing(fake):
    p0 = make_provisioner(fake, apply_=True)
    p0.converge()
    davi = next(c for c in fake.clients.values()
                if c["clientId"] == "mcp-api-delpi")
    davi["publicClient"] = True
    fake.calls.clear()
    p = make_provisioner(fake, apply_=False)
    p._client_uuid_cache.clear()
    report = p.converge()
    assert not report.converged
    assert mutate_writes(fake) == []
    assert davi["publicClient"] is True      # unchanged by check


def test_unrelated_resources_untouched(converged):
    foreign = converged.add_client("some-other-tool",
                                   serviceAccountsEnabled=True)
    converged.policies["x"] = {"id": "x", "name": "foreign-policy",
                               "clients": [foreign]}
    p = make_provisioner(converged, apply_=True)
    p._client_uuid_cache.clear()
    p.converge()
    assert converged.clients[foreign]["serviceAccountsEnabled"] is True
    assert "x" in converged.policies          # foreign policy not deleted


def test_requester_client_contract(converged):
    req = next(c for c in converged.clients.values()
               if c["clientId"] == "delia-api")
    assert req["publicClient"] is False
    assert req["serviceAccountsEnabled"] is False
    assert req["directAccessGrantsEnabled"] is False
    assert req["standardFlowEnabled"] is False
    assert req["implicitFlowEnabled"] is False
    # KC24_LEGACY: KC26-only attribute is never written
    assert "standard.token.exchange.enabled" not in \
        req.get("attributes", {})


def test_requester_kc26_attribute_written_only_on_kc26(fake):
    p = make_provisioner(fake, apply_=True, strategy="KC26_STANDARD")
    p.converge()
    req = next(c for c in fake.clients.values()
               if c["clientId"] == "delia-api")
    assert req["attributes"]["standard.token.exchange.enabled"] == "true"


@pytest.mark.parametrize("strategy", ["KC24_LEGACY", "KC26_STANDARD"])
def test_strategy_check_apply_idempotent(fake, strategy):
    # check → apply → check → apply for both infrastructure strategies
    chk = make_provisioner(fake, apply_=False, strategy=strategy)
    report = chk.converge()
    assert any(i[1] == "DRIFT" for i in report.items)
    ap = make_provisioner(fake, apply_=True, strategy=strategy)
    ap.converge()
    fake.calls.clear()
    chk2 = make_provisioner(fake, apply_=False, strategy=strategy)
    report2 = chk2.converge()
    assert all(i[1] == "OK" for i in report2.items)
    assert not any(c[0] in ("POST", "PUT", "DELETE")
                   for c in fake.calls)          # check = zero writes
    ap2 = make_provisioner(fake, apply_=True, strategy=strategy)
    ap2._client_uuid_cache.clear()
    ap2.converge()                               # idempotent re-apply


def test_portal_audience_is_requester_only(fake):
    # KC26 standard contract: subject token must carry delia-api aud.
    p = make_provisioner(fake, apply_=True, strategy="KC26_STANDARD")
    p.converge()
    portal = next(u for u, c in fake.clients.items()
                  if c["clientId"] == "delpi-central")
    mappers = fake.client_mappers.get(portal, [])
    auds = {m["config"]["included.custom.audience"] for m in mappers
            if m["protocolMapper"] == "oidc-audience-mapper"}
    assert auds == {"delia-api"}              # no mcp-* audience on Portal


def test_portal_untouched_on_kc24(converged):
    # KC24 legacy V1: requester eligibility is not enforced on the
    # subject token — the Portal client must never be modified.
    portal = next(u for u, c in converged.clients.items()
                  if c["clientId"] == "delpi-central")
    assert not converged.client_mappers.get(portal)


def test_resource_audiences_on_scopes(converged):
    auds = set()
    for mappers in converged.scope_mappers.values():
        for m in mappers:
            if m["protocolMapper"] == "oidc-audience-mapper":
                auds.add(m["config"]["included.custom.audience"])
    assert auds == {
        "https://minhadelpi.com.br/apps/api-delpi/mcp",
        "https://minhadelpi.com.br/apps/transformometro-api/mcp",
        "https://minhadelpi.com.br/apps/tv-dashboard-api/mcp",
    }


def test_policy_bound_to_delia_api_only(converged):
    req_uuid = next(u for u, c in converged.clients.items()
                    if c["clientId"] == "delia-api")
    pol = next(p for p in converged.policies.values()
               if p["name"] == "delia-exchange-requester")
    assert pol["clients"] == [req_uuid]


def test_all_specialists_get_exchange_permission(converged):
    for cid in ("mcp-api-delpi", "mcp-transformometro", "mcp-tv-dashboard"):
        uuid_ = next(u for u, c in converged.clients.items()
                     if c["clientId"] == cid)
        assert converged.mgmt_enabled.get(uuid_) is True


def test_no_user_endpoints_ever_touched(converged):
    assert not any("/users" in path for _m, path in converged.calls)


def test_secret_install_requires_apply(tmp_path, monkeypatch):
    fake = FakeKcAdmin()
    fake.seed_builtins()
    fake.seed_portal()
    p = make_provisioner(fake, apply_=False)
    with pytest.raises(mod.ProvisioningError, match="--apply"):
        p.install_secret(str(tmp_path / ".env"))


def test_secret_install_refuses_non_gitignored(tmp_path, converged):
    target = tmp_path / "tracked-file.env"   # outside repo → not ignored
    p = make_provisioner(converged, apply_=True)
    with pytest.raises(mod.ProvisioningError, match="gitignored"):
        p.install_secret(str(target))


def test_secret_install_gitignored_atomic(tmp_path, converged):
    # a repo-internal gitignored path (infra/.env.* matches .gitignore)
    repo = os.path.abspath(
        os.path.join(os.path.dirname(mod.__file__), "..", ".."))
    target = os.path.join(repo, "infra", ".env.test-provisioner-tmp")
    try:
        p = make_provisioner(converged, apply_=True)
        p._client_uuid_cache.clear()
        p.install_secret(target)
        with open(target, encoding="utf-8") as fh:
            content = fh.read()
        assert "DELIA_EXCHANGE_CLIENT_SECRET=fake-secret" in content
        assert os.stat(target).st_mode & 0o777 == 0o600
    finally:
        if os.path.exists(target):
            os.unlink(target)


def test_secret_never_in_stdout(capsys, fake):
    make_provisioner(fake, apply_=True).converge()
    out = capsys.readouterr()
    assert "fake-secret" not in out.out
    assert "fake-secret" not in out.err


def test_cli_check_vs_apply(monkeypatch, fake, capsys):
    monkeypatch.setenv("KC_BASE", "https://kc.example/auth")
    monkeypatch.setenv("KC_ADMIN_TOKEN", "t")
    monkeypatch.setenv("PUBLIC_BASE_URL", PUB)
    monkeypatch.setenv("DELIA_KC_STRATEGY", "KC24_LEGACY")
    monkeypatch.setattr(mod, "server_version", lambda *_: "24.0.5")
    monkeypatch.setattr(mod, "KcAdmin", lambda *_a, **_k: fake)
    assert mod.main(["--check"]) == 2        # drift on empty realm
    assert mod.main(["--apply"]) == 0
    fake.calls.clear()
    assert mod.main(["--check"]) == 0        # converged → NO_DRIFT
    out = capsys.readouterr().out
    assert "NO_DRIFT" in out


def test_cli_version_gate(monkeypatch, fake, capsys):
    monkeypatch.setenv("KC_BASE", "https://kc.example/auth")
    monkeypatch.setenv("KC_ADMIN_TOKEN", "t")
    monkeypatch.setenv("PUBLIC_BASE_URL", PUB)
    # mode/version mismatch fails closed in both directions
    monkeypatch.delenv("DELIA_KC_STRATEGY", raising=False)
    monkeypatch.setattr(mod, "server_version", lambda *_: "26.0.7")
    monkeypatch.setattr(mod, "KcAdmin", lambda *_a, **_k: fake)
    # default strategy is KC24_LEGACY: KC26 server → mismatch
    assert mod.main(["--apply"]) == 1
    assert mod.main(["--check"]) == 1        # even check fails closed
    err = capsys.readouterr().err
    assert "FAIL_CLOSED" in err and "26" in err
    # KC24 server under KC26_STANDARD → mismatch
    monkeypatch.setattr(mod, "server_version", lambda *_: "24.0.5")
    assert mod.main(["--apply", "--strategy", "KC26_STANDARD"]) == 1
    # unknown future version under KC24_LEGACY → fail closed
    monkeypatch.setattr(mod, "server_version", lambda *_: "99.0.0")
    assert mod.main(["--apply"]) == 1
