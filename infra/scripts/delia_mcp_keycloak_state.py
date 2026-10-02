#!/usr/bin/env python3
"""DÉLIA MCP Keycloak desired-state engine — shared DEV/PROD.

Single source for the bounded DÉLIA MCP IAM contract (approved at
C3-MCP-INTEROP-01R1A..R1C; see doc 60 and ledger §6.95..§6.99):

  * generic client scope ``mcp:tools``;
  * one confidential resource client + one resource-audience client
    scope per approved specialist (mcp-api-delpi / mcp-transformometro /
    mcp-tv-dashboard) carrying the MCP resource audience;
  * ONE confidential requester client ``delia-api``
    (``standard.token.exchange.enabled``, NO service account, NO
    direct access grants, NO standard/implicit flows);
  * requester audience ``delia-api`` on the Portal client so Portal
    subject tokens are eligible for exchange (NOT an MCP audience);
  * per-target ``token-exchange`` scope permission bound to the
    ``delia-exchange-requester`` client policy (delia-api only).

Hard boundaries (both modes):

  * realm ``delpi`` and the Portal client must ALREADY exist —
    they are preconditions, never created here;
  * no user is created/updated; no password touched; no SQL/DB access;
  * unknown/unrelated Keycloak resources are never deleted or modified;
  * nothing secret is ever printed.

Modes:

  * ``--check`` (default): read-only. Reports OK/DRIFT per element,
    exits 0 when converged, 2 when drift is detected, 1 on hard
    failure. Never writes.
  * ``--apply``: converges the bounded contract idempotently.

Two explicit infrastructure strategies exist because there are two
proven physical contracts (selected via ``--strategy`` or
``DELIA_KC_STRATEGY``, pinned by the DEV/PROD wrappers):

* ``KC24_LEGACY`` — production baseline: Keycloak 24.x with
  ``KC_FEATURES=token-exchange,admin-fine-grained-authz`` (both
  PREVIEW). Legacy internal→internal token exchange; the requester
  client does NOT carry ``standard.token.exchange.enabled`` (KC26-only
  attribute, never written in this mode).
* ``KC26_STANDARD`` — DEV: Keycloak 26.x with the
  ``standard.token.exchange.enabled`` requester attribute and the same
  fine-grained permission endpoints.

The strategy is validated against the actual server major version and
fails closed on mismatch or unknown versions. The desired semantic
state (scopes, resource clients, requester, exchange policy,
permissions, portal audience) is identical; only the version-specific
mechanics differ.

Secret installation is opt-in and explicit: ``--install-secret-to
PATH`` (apply mode only) upserts ``DELIA_EXCHANGE_CLIENT_SECRET`` into
a gitignored env file (verified via ``git check-ignore``), written
atomically with 0600 permissions. Without the flag no secret is read
or stored by this tool.

Usage::

    KC_BASE=... KC_ADMIN_TOKEN=... REALM=delpi \
        python3 delia_mcp_keycloak_state.py --check
    KC_BASE=... KC_ADMIN_TOKEN=... REALM=delpi \
        python3 delia_mcp_keycloak_state.py --apply \
        [--install-secret-to infra/.env]

Transport is injectable for tests: instantiate ``Provisioner`` with a
``KcAdmin`` whose ``call`` method is stubbed, or pass a custom
``opener``.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

# strategy name → accepted server major versions
STRATEGY_MAJORS = {
    "KC24_LEGACY": (24,),
    "KC26_STANDARD": (26,),
}
DEFAULT_STRATEGY = "KC24_LEGACY"

SPECIALISTS = (
    # (resource client_id, audience scope name, public path suffix)
    ("mcp-api-delpi", "mcp-audience-api-delpi", "apps/api-delpi/mcp"),
    ("mcp-transformometro", "mcp-audience-transformometro",
     "apps/transformometro-api/mcp"),
    ("mcp-tv-dashboard", "mcp-audience-tv-dashboard",
     "apps/tv-dashboard-api/mcp"),
)

REQUESTER_CLIENT_ID = "delia-api"
GENERIC_SCOPE_NAME = "mcp:tools"
DELPI_AUDIENCE_SCOPE = "audience-delpi"
EXCHANGE_POLICY_NAME = "delia-exchange-requester"
# R1A prototype (per-target policy name) — converge permissions to the
# canonical policy, then remove ONLY this exact legacy name. Unknown
# policies are never deleted.
LEGACY_POLICY_NAME = "delia-exchange-requester-mcp-api-delpi"
# Built-in OIDC scopes the specialist MCP transport requires on Bearer
# (openid profile email mcp:tools per the RFC 9728 challenge). Realm
# built-ins — looked up only, never created here.
BUILTIN_SCOPE_NAMES = ("openid", "profile", "email")

RESOURCE_CLIENT_DESIRED_FLAGS = {
    "publicClient": False,
    "standardFlowEnabled": True,      # external connector contract;
    "implicitFlowEnabled": False,     # DÉLIA itself only exchanges.
    "directAccessGrantsEnabled": False,
    "serviceAccountsEnabled": False,
}
RESOURCE_CLIENT_PKCE = "S256"

REQUESTER_DESIRED_FLAGS = {
    "publicClient": False,
    "standardFlowEnabled": False,
    "implicitFlowEnabled": False,
    "directAccessGrantsEnabled": False,
    "serviceAccountsEnabled": False,
}

SECRET_KEY = "DELIA_EXCHANGE_CLIENT_SECRET"


class ProvisioningError(Exception):
    """Hard fail-closed error (preconditions, auth, version)."""


class DriftReport:
    """Collects per-element drift observations."""

    def __init__(self) -> None:
        self.items: list[tuple[str, str, str]] = []  # (element, status, note)

    def ok(self, element: str, note: str = "") -> None:
        self.items.append((element, "OK", note))

    def drift(self, element: str, note: str) -> None:
        self.items.append((element, "DRIFT", note))

    def missing(self, element: str, note: str = "") -> None:
        self.items.append((element, "MISSING", note))

    @property
    def converged(self) -> bool:
        return all(status == "OK" for _e, status, _n in self.items)


class KcAdmin:
    """Minimal Keycloak Admin REST client (transport injectable)."""

    def __init__(self, kc_base: str, admin_token: str) -> None:
        self.kc_base = kc_base.rstrip("/")
        self._token = admin_token
        self.writes: list[tuple[str, str]] = []  # audit: mutating calls

    def call(self, method: str, path: str, body: object = None,
             tolerate: tuple[int, ...] = ()):
        url = self.kc_base + "/admin" + path
        req = urllib.request.Request(url, method=method)
        req.add_header("Authorization", "Bearer " + self._token)
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            req.add_header("Content-Type", "application/json")
        if method not in ("GET", "HEAD"):
            self.writes.append((method, path))
        try:
            resp = urllib.request.urlopen(req, data=data, timeout=30)
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            if exc.code in tolerate:
                exc.read()
                return exc.code, None
            detail = (exc.read() or b"")[:200].decode("utf-8", "replace")
            raise ProvisioningError(
                f"admin REST {method} {path} -> {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise ProvisioningError(
                f"admin REST {method} {path} unreachable: {exc.reason}"
            ) from exc


def mint_admin_token(kc_base: str, admin_user: str,
                     admin_pass: str) -> str:
    """Password-grant an admin token against realm master."""
    req = urllib.request.Request(
        kc_base.rstrip("/")
        + "/realms/master/protocol/openid-connect/token",
        data=urllib.parse.urlencode({
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": admin_user,
            "password": admin_pass,
        }).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())["access_token"]
    except Exception as exc:  # noqa: BLE001 — fail closed, no detail leak
        raise ProvisioningError(
            f"admin login failed at realm master: {type(exc).__name__}"
        ) from exc


def server_version(kc_base: str, admin_token: str) -> str:
    """Read the running Keycloak version via /admin/serverinfo."""
    req = urllib.request.Request(
        kc_base.rstrip("/") + "/admin/serverinfo")
    req.add_header("Authorization", "Bearer " + admin_token)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        info = json.loads(resp.read())
        return str(info.get("systemInfo", {}).get("version", ""))
    except Exception as exc:  # noqa: BLE001
        raise ProvisioningError(
            f"cannot read serverinfo (admin rights?): {type(exc).__name__}"
        ) from exc


def _major(version: str) -> int:
    try:
        return int(str(version).split(".", 1)[0])
    except (TypeError, ValueError):
        return 0


class Provisioner:
    """Converges/inspects the bounded DÉLIA MCP IAM contract."""

    def __init__(self, admin: KcAdmin, realm: str, portal_client_id: str,
                 public_base_url: str, apply: bool = False,
                 strategy: str = DEFAULT_STRATEGY) -> None:
        if strategy not in STRATEGY_MAJORS:
            raise ProvisioningError(
                f"unknown strategy {strategy!r} — supported: "
                + ", ".join(sorted(STRATEGY_MAJORS)))
        self.admin = admin
        self.realm = realm
        self.portal_client_id = portal_client_id
        self.public_base_url = public_base_url.rstrip("/")
        self.apply = apply
        self.strategy = strategy
        # KC26-only client attribute; never written on the KC24 legacy
        # contract where the preview exchange needs no client flag.
        self._needs_std_exchange_attr = strategy == "KC26_STANDARD"
        self.report = DriftReport()
        self._client_uuid_cache: dict[str, str] = {}

    # ---------------- preconditions ----------------

    def preflight(self) -> None:
        """Fail-closed precondition gate — runs in BOTH modes."""
        st, _body = self.admin.call(
            "GET", f"/realms/{self.realm}", tolerate=(404,))
        if st == 404:
            raise ProvisioningError(
                f"realm '{self.realm}' does not exist — corporate realm "
                "creation is out of scope; provision it first")
        if not self.portal_uuid():
            raise ProvisioningError(
                f"portal client '{self.portal_client_id}' missing in realm "
                f"'{self.realm}' — Portal client creation is out of scope")

    # ---------------- read helpers ----------------

    def client_uuid(self, client_id: str) -> str:
        if client_id not in self._client_uuid_cache:
            _st, rows = self.admin.call(
                "GET",
                f"/realms/{self.realm}/clients"
                f"?clientId={urllib.parse.quote(client_id)}")
            self._client_uuid_cache[client_id] = (
                rows[0]["id"] if rows else "")
        return self._client_uuid_cache[client_id]

    def portal_uuid(self) -> str:
        return self.client_uuid(self.portal_client_id)

    def _scopes(self) -> list[dict]:
        _st, scopes = self.admin.call(
            "GET", f"/realms/{self.realm}/client-scopes")
        return scopes or []

    def _find_scope(self, name: str) -> dict | None:
        return next((s for s in self._scopes() if s.get("name") == name),
                    None)

    # ---------------- write helper ----------------

    def _mutate(self, element: str, method: str, path: str,
                body: object = None, note: str = "") -> None:
        """Apply-or-report: single mutation funnel.

        check mode  -> record DRIFT, never call.
        apply mode  -> call, record OK(applied).
        """
        if not self.apply:
            self.report.drift(element, note or f"would {method} {path}")
            return
        self.admin.call(method, path, body, tolerate=(409,))
        self.report.ok(element, note or f"{method} {path} applied")

    # ---------------- desired state ----------------

    def resource_audience(self, path_suffix: str) -> str:
        """MCP resource audience for a specialist.

        Derived from ``DELIA_MCP_AUDIENCE_BASE`` (explicit override used
        by DEV to pin the canonical public audiences regardless of the
        local base URL) or ``PUBLIC_BASE_URL`` — never a hardcoded
        domain. May be overridden per specialist via
        ``DELIA_MCP_<ID>_RESOURCE_AUDIENCE`` in the DÉLIA runtime config.
        """
        base = (os.environ.get("DELIA_MCP_AUDIENCE_BASE") or
                self.public_base_url).rstrip("/")
        if not base:
            raise ProvisioningError(
                "audience base missing — set PUBLIC_BASE_URL or "
                "DELIA_MCP_AUDIENCE_BASE so resource audiences are "
                "derived, not hardcoded")
        return f"{base}/{path_suffix}"

    def ensure_scope(self, name: str, element: str) -> str | None:
        scope = self._find_scope(name)
        if scope is None:
            self._mutate(element, "POST",
                         f"/realms/{self.realm}/client-scopes",
                         {"name": name, "protocol": "openid-connect",
                          "attributes": {"include.in.token.scope": "true",
                                         "display.on.consent.screen":
                                             "false"}},
                         f"create client scope {name}")
            scope = self._find_scope(name)
        else:
            self.report.ok(element, f"scope {name} present")
        return scope["id"] if scope else None

    def ensure_audience_mapper(self, scope_id: str, audience: str,
                               element: str) -> None:
        _st, mappers = self.admin.call(
            "GET",
            f"/realms/{self.realm}/client-scopes/{scope_id}"
            "/protocol-mappers/models")
        for m in mappers or []:
            if (m.get("protocolMapper") == "oidc-audience-mapper"
                    and m.get("config", {}).get("included.custom.audience")
                    == audience):
                self.report.ok(element, f"audience mapper {audience}")
                return
        self._mutate(
            element, "POST",
            f"/realms/{self.realm}/client-scopes/{scope_id}"
            "/protocol-mappers/models",
            {"name": f"{audience.rsplit('/', 1)[-2]}-resource-aud",
             "protocol": "openid-connect",
             "protocolMapper": "oidc-audience-mapper",
             "config": {"included.custom.audience": audience,
                        "id.token.claim": "false",
                        "access.token.claim": "true"}},
            f"add audience mapper {audience}")

    def ensure_default_scope(self, client_uuid_: str, scope_id: str,
                             element: str) -> None:
        _st, defaults = self.admin.call(
            "GET",
            f"/realms/{self.realm}/clients/{client_uuid_}"
            "/default-client-scopes")
        if scope_id in {s["id"] for s in defaults or []}:
            return
        self._mutate(
            element, "PUT",
            f"/realms/{self.realm}/clients/{client_uuid_}"
            f"/default-client-scopes/{scope_id}",
            note="assign default client scope")

    def ensure_resource_client(self, client_id: str) -> str:
        """Canonical mcp-* resource contract — idempotent create-or-repair."""
        element = f"resource client {client_id}"
        uuid_ = self.client_uuid(client_id)
        if not uuid_:
            self._mutate(element, "POST", f"/realms/{self.realm}/clients",
                         {"clientId": client_id, "enabled": True,
                          "protocol": "openid-connect",
                          "attributes": {"pkce.code.challenge.method":
                                         RESOURCE_CLIENT_PKCE},
                          **RESOURCE_CLIENT_DESIRED_FLAGS},
                         f"create resource client {client_id}")
            self._client_uuid_cache.pop(client_id, None)
            uuid_ = self.client_uuid(client_id)
            return uuid_
        _st, full = self.admin.call(
            "GET", f"/realms/{self.realm}/clients/{uuid_}")
        dirty = [k for k, v in RESOURCE_CLIENT_DESIRED_FLAGS.items()
                 if full.get(k) != v]
        attrs = full.get("attributes", {})
        if attrs.get("pkce.code.challenge.method") != RESOURCE_CLIENT_PKCE:
            dirty.append("pkce.code.challenge.method")
        if dirty:
            if not self.apply:
                self.report.drift(element, "config drift: "
                                  + ",".join(sorted(dirty)))
            else:
                full.update(RESOURCE_CLIENT_DESIRED_FLAGS)
                attrs["pkce.code.challenge.method"] = RESOURCE_CLIENT_PKCE
                full["attributes"] = attrs
                self.admin.call(
                    "PUT", f"/realms/{self.realm}/clients/{uuid_}", full)
                self.report.ok(element, "repaired: "
                               + ",".join(sorted(dirty)))
        else:
            self.report.ok(element)
        return uuid_

    def ensure_requester(self) -> str:
        element = f"requester client {REQUESTER_CLIENT_ID}"
        uuid_ = self.client_uuid(REQUESTER_CLIENT_ID)
        if not uuid_:
            body = {"clientId": REQUESTER_CLIENT_ID, "enabled": True,
                    "protocol": "openid-connect",
                    **REQUESTER_DESIRED_FLAGS}
            if self._needs_std_exchange_attr:
                body["attributes"] = \
                    {"standard.token.exchange.enabled": "true"}
            self._mutate(element, "POST", f"/realms/{self.realm}/clients",
                         body,
                         f"create requester client {REQUESTER_CLIENT_ID}")
            self._client_uuid_cache.pop(REQUESTER_CLIENT_ID, None)
            return self.client_uuid(REQUESTER_CLIENT_ID)
        _st, full = self.admin.call(
            "GET", f"/realms/{self.realm}/clients/{uuid_}")
        dirty = [k for k, v in REQUESTER_DESIRED_FLAGS.items()
                 if full.get(k) != v]
        attrs = full.get("attributes", {})
        if self._needs_std_exchange_attr and \
                attrs.get("standard.token.exchange.enabled") != "true":
            dirty.append("standard.token.exchange.enabled")
        if dirty:
            if not self.apply:
                self.report.drift(element, "config drift: "
                                  + ",".join(sorted(dirty)))
            else:
                full.update(REQUESTER_DESIRED_FLAGS)
                if self._needs_std_exchange_attr:
                    attrs["standard.token.exchange.enabled"] = "true"
                    full["attributes"] = attrs
                self.admin.call(
                    "PUT", f"/realms/{self.realm}/clients/{uuid_}", full)
                self.report.ok(element, "repaired: "
                               + ",".join(sorted(dirty)))
        else:
            self.report.ok(element)
        return uuid_

    def ensure_portal_audience(self) -> None:
        """delia-api requester audience on the Portal client mapper.

        The Portal subject token only gains `aud` eligibility for the
        requester — NEVER an MCP resource audience.
        """
        element = "portal requester audience"
        portal_uuid = self.portal_uuid()
        _st, mappers = self.admin.call(
            "GET",
            f"/realms/{self.realm}/clients/{portal_uuid}"
            "/protocol-mappers/models")
        if any(m.get("protocolMapper") == "oidc-audience-mapper"
               and m.get("config", {}).get("included.custom.audience")
               == REQUESTER_CLIENT_ID
               for m in mappers or []):
            self.report.ok(element, f"aud {REQUESTER_CLIENT_ID} mapped")
            return
        self._mutate(
            element, "POST",
            f"/realms/{self.realm}/clients/{portal_uuid}"
            "/protocol-mappers/models",
            {"name": "delia-requester-audience",
             "protocol": "openid-connect",
             "protocolMapper": "oidc-audience-mapper",
             "config": {"included.custom.audience": REQUESTER_CLIENT_ID,
                        "id.token.claim": "false",
                        "access.token.claim": "true"}},
            "add delia-api audience mapper on Portal client")

    def ensure_exchange_policy(self, rm_uuid: str) -> str | None:
        element = "policy delia-exchange-requester"
        # 404 here means the realm-management resource server is not
        # initialized yet (no fine-grained permission enabled anywhere)
        # — treated as missing policy, converged on --apply.
        _st, existing = self.admin.call(
            "GET",
            f"/realms/{self.realm}/clients/{rm_uuid}"
            "/authz/resource-server/policy"
            f"?name={EXCHANGE_POLICY_NAME}", tolerate=(404,))
        existing = existing or []
        if existing:
            pol = existing[0]
            clients = set(pol.get("clients") or [])
            requester = self.client_uuid(REQUESTER_CLIENT_ID)
            if clients and clients != {requester}:
                self.report.drift(
                    element,
                    f"policy bound to unexpected clients: "
                    f"{sorted(clients)}")
                return pol["id"]
            self.report.ok(element)
            return pol["id"]
        if not self.apply:
            self.report.drift(element, f"would create {EXCHANGE_POLICY_NAME}")
            return None
        _st, pol = self.admin.call(
            "POST",
            f"/realms/{self.realm}/clients/{rm_uuid}"
            "/authz/resource-server/policy/client",
            {"name": EXCHANGE_POLICY_NAME, "type": "client",
             "logic": "POSITIVE", "decisionStrategy": "UNANIMOUS",
             "clients": [self.client_uuid(REQUESTER_CLIENT_ID)]},
            tolerate=(409,))
        self.report.ok(element, "created")
        _st, existing = self.admin.call(
            "GET",
            f"/realms/{self.realm}/clients/{rm_uuid}"
            "/authz/resource-server/policy"
            f"?name={EXCHANGE_POLICY_NAME}")
        return existing[0]["id"] if existing else None

    def ensure_mgmt_permissions(self, client_id: str, cuuid: str) -> None:
        """Enable per-client fine-grained management permissions.

        Must run BEFORE the realm-management resource-server is queried:
        enabling the first management permission in a realm lazily
        initializes that resource server.
        """
        element = f"mgmt permissions {client_id}"
        _st, mgmt = self.admin.call(
            "GET",
            f"/realms/{self.realm}/clients/{cuuid}"
            "/management/permissions", tolerate=(404, 400))
        if mgmt and mgmt.get("enabled"):
            self.report.ok(element)
            return
        if not self.apply:
            self.report.drift(
                element, "fine-grained permissions disabled "
                         "(feature flag/admin-fine-grained-authz?)")
            return
        self.admin.call(
            "PUT",
            f"/realms/{self.realm}/clients/{cuuid}"
            "/management/permissions",
            {"enabled": True})
        self.report.ok(element, "enabled")

    def ensure_exchange_permission(self, client_id: str, cuuid: str,
                                   rm_uuid: str, policy_id: str | None,
                                   legacy_id: str | None) -> None:
        element = f"token-exchange permission {client_id}"
        _st, mgmt = self.admin.call(
            "GET",
            f"/realms/{self.realm}/clients/{cuuid}"
            "/management/permissions", tolerate=(404, 400))
        scope_perms = (mgmt or {}).get("scopePermissions") or {}
        if not mgmt or not mgmt.get("enabled") or \
                "token-exchange" not in scope_perms:
            if self.apply:
                raise ProvisioningError(
                    f"{client_id}: management/permissions unavailable — "
                    "admin-fine-grained-authz not enabled or Keycloak "
                    "version unsupported")
            self.report.drift(
                element, "fine-grained permissions disabled "
                         "(feature flag/admin-fine-grained-authz?)")
            return
        perm_id = scope_perms["token-exchange"]
        resource_id = mgmt["resource"]
        _st, assoc = self.admin.call(
            "GET",
            f"/realms/{self.realm}/clients/{rm_uuid}"
            "/authz/resource-server"
            f"/permission/scope/{perm_id}/associatedPolicies")
        assoc_ids = [p["id"] for p in (assoc or [])]
        desired = [p for p in assoc_ids if p != legacy_id]
        if policy_id and policy_id not in desired:
            desired.append(policy_id)
        if sorted(desired) == sorted(assoc_ids) and policy_id in desired:
            self.report.ok(element)
            return
        if not self.apply:
            self.report.drift(
                element, "permission not bound to "
                f"{EXCHANGE_POLICY_NAME}")
            return
        _st, scopes = self.admin.call(
            "GET",
            f"/realms/{self.realm}/clients/{rm_uuid}"
            "/authz/resource-server"
            f"/permission/scope/{perm_id}/scopes")
        self.admin.call(
            "PUT",
            f"/realms/{self.realm}/clients/{rm_uuid}"
            f"/authz/resource-server/permission/scope/{perm_id}",
            {"id": perm_id,
             "name": f"token-exchange.permission.client.{cuuid}",
             "type": "scope", "logic": "POSITIVE",
             "decisionStrategy": "UNANIMOUS",
             "policies": desired,
             "resources": [resource_id],
             "scopes": [s["id"] for s in (scopes or [])]})
        self.report.ok(element, "bound to delia-api requester")

    def remove_legacy_policy(self, rm_uuid: str, legacy_id: str | None) -> None:
        if not legacy_id:
            return
        element = f"legacy policy {LEGACY_POLICY_NAME}"
        self._mutate(
            element, "DELETE",
            f"/realms/{self.realm}/clients/{rm_uuid}"
            f"/authz/resource-server/policy/client/{legacy_id}",
            note="remove superseded R1A prototype policy")

    # ---------------- orchestration ----------------

    def converge(self) -> DriftReport:
        self.preflight()

        builtin_ids = {s["name"]: s["id"] for s in self._scopes()
                       if s["name"] in BUILTIN_SCOPE_NAMES}
        mcp_tools_id = self.ensure_scope(
            GENERIC_SCOPE_NAME, f"scope {GENERIC_SCOPE_NAME}")
        delpi_aud_id = self.ensure_scope(
            DELPI_AUDIENCE_SCOPE, f"scope {DELPI_AUDIENCE_SCOPE}")

        for client_id, scope_name, suffix in SPECIALISTS:
            element = f"specialist {client_id}"
            scope_id = self.ensure_scope(scope_name, element)
            if scope_id:
                self.ensure_audience_mapper(
                    scope_id, self.resource_audience(suffix), element)
            cuuid = self.ensure_resource_client(client_id)
            if cuuid:
                for builtin in BUILTIN_SCOPE_NAMES:
                    if builtin in builtin_ids:
                        self.ensure_default_scope(
                            cuuid, builtin_ids[builtin], element)
                if mcp_tools_id:
                    self.ensure_default_scope(cuuid, mcp_tools_id, element)
                if delpi_aud_id:
                    self.ensure_default_scope(cuuid, delpi_aud_id, element)
                if scope_id:
                    self.ensure_default_scope(cuuid, scope_id, element)
                self.report.ok(element, f"resource client {client_id}")

        requester_uuid = self.ensure_requester()
        # KC24 legacy V1 does not require subject-token eligibility for the
        # requester (proven on isolated 24.0.5: a subject token minted by a
        # client without delia-api in aud still exchanges; the gate is the
        # target-client token-exchange permission). Only the KC26 standard
        # contract needs the Portal audience mapper — skipping it on KC24
        # keeps the production Portal client completely untouched.
        if self._needs_std_exchange_attr:
            self.ensure_portal_audience()

        rm_uuid = self.client_uuid("realm-management")
        if not rm_uuid:
            raise ProvisioningError(
                "realm-management client missing — broken realm")

        # Enabling fine-grained management permissions on the resource
        # clients lazily initializes the realm-management authz resource
        # server — must precede any policy/permission endpoint access.
        for client_id, _scope, _suffix in SPECIALISTS:
            cuuid = self.client_uuid(client_id)
            if cuuid:
                self.ensure_mgmt_permissions(client_id, cuuid)

        policy_id = self.ensure_exchange_policy(rm_uuid)

        _st, legacy = self.admin.call(
            "GET",
            f"/realms/{self.realm}/clients/{rm_uuid}"
            "/authz/resource-server/policy"
            f"?name={LEGACY_POLICY_NAME}", tolerate=(404,))
        legacy_id = legacy[0]["id"] if legacy else None

        for client_id, _scope, _suffix in SPECIALISTS:
            cuuid = self.client_uuid(client_id)
            if not cuuid:
                self.report.missing(
                    f"token-exchange permission {client_id}",
                    "resource client absent")
                continue
            self.ensure_exchange_permission(
                client_id, cuuid, rm_uuid, policy_id, legacy_id)

        self.remove_legacy_policy(rm_uuid, legacy_id)
        return self.report

    # ---------------- secret installation (explicit opt-in) ---------

    def install_secret(self, env_path: str) -> None:
        """Upsert DELIA_EXCHANGE_CLIENT_SECRET into a gitignored env file.

        Explicit, apply-mode-only operation. The value is never printed
        or logged; the target file must be gitignored and is rewritten
        atomically with 0600 permissions.
        """
        if not self.apply:
            raise ProvisioningError(
                "--install-secret-to requires --apply")
        path = os.path.abspath(env_path)
        repo_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", ".."))
        try:
            subprocess.run(["git", "check-ignore", "-q", path],
                           check=True, capture_output=True, cwd=repo_root)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise ProvisioningError(
                f"refusing to write secret: {path} is not gitignored "
                "(git check-ignore failed)") from exc

        requester_uuid = self.client_uuid(REQUESTER_CLIENT_ID)
        if not requester_uuid:
            raise ProvisioningError(
                f"requester client {REQUESTER_CLIENT_ID} missing")
        _st, sec = self.admin.call(
            "GET",
            f"/realms/{self.realm}/clients/{requester_uuid}/client-secret")
        secret = sec["value"]

        try:
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except FileNotFoundError:
            lines = []
        out, replaced = [], False
        for line in lines:
            if line.startswith(SECRET_KEY + "="):
                out.append(f"{SECRET_KEY}={secret}")
                replaced = True
            else:
                out.append(line)
        if not replaced:
            out.append(f"{SECRET_KEY}={secret}")
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write("\n".join(out) + "\n")
            os.chmod(tmp, 0o600)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


# ---------------- CLI ----------------


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="delia-mcp-keycloak-state",
        description="DÉLIA MCP Keycloak desired-state engine "
                    "(read-only --check is the default).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                      help="read-only drift report (default)")
    mode.add_argument("--apply", action="store_true",
                      help="converge the bounded DÉLIA MCP IAM contract")
    parser.add_argument("--install-secret-to", metavar="PATH",
                        help="upsert DELIA_EXCHANGE_CLIENT_SECRET into a "
                             "gitignored env file (apply mode only)")
    parser.add_argument("--strategy", choices=sorted(STRATEGY_MAJORS),
                        default=_env("DELIA_KC_STRATEGY")
                        or DEFAULT_STRATEGY,
                        help="infrastructure strategy matching the target "
                             "Keycloak line (pinned by the DEV/PROD "
                             "wrappers; validated against the actual "
                             "server version — fail-closed on mismatch)")
    args = parser.parse_args(argv)

    kc_base = _env("KC_BASE") or _env("KC_BASE_URL") or _env("KEYCLOAK_URL")
    if kc_base and "/auth" not in kc_base:
        kc_base = kc_base.rstrip("/") + "/auth"
    realm = _env("REALM") or _env("KEYCLOAK_REALM") or "delpi"
    portal = _env("PORTAL_CLIENT_ID") or "delpi-central"
    public_base = _env("PUBLIC_BASE_URL")
    admin_token = _env("KC_ADMIN_TOKEN")
    admin_user = _env("KEYCLOAK_ADMIN")
    admin_pass = _env("KEYCLOAK_ADMIN_PASSWORD")

    if not kc_base:
        print("[delia-mcp-provision] ERROR: KC_BASE/KEYCLOAK_URL missing",
              file=sys.stderr)
        return 1

    try:
        if not admin_token:
            if not admin_user or not admin_pass:
                raise ProvisioningError(
                    "admin credentials missing — set KC_ADMIN_TOKEN or "
                    "KEYCLOAK_ADMIN + KEYCLOAK_ADMIN_PASSWORD")
            admin_token = mint_admin_token(kc_base, admin_user, admin_pass)

        version = server_version(kc_base, admin_token)
        print(f"[delia-mcp-provision] keycloak {version} at {kc_base} "
              f"(strategy {args.strategy})")
        major = _major(version)
        if major not in STRATEGY_MAJORS[args.strategy]:
            raise ProvisioningError(
                f"strategy {args.strategy} does not match server "
                f"Keycloak {version or 'unknown'} — expected major "
                f"{STRATEGY_MAJORS[args.strategy]}; fail closed instead "
                "of emulating a different contract")

        admin = KcAdmin(kc_base, admin_token)
        provisioner = Provisioner(
            admin, realm=realm, portal_client_id=portal,
            public_base_url=public_base, apply=args.apply,
            strategy=args.strategy)
        report = provisioner.converge()

        for element, status, note in report.items:
            line = f"[{status:7}] {element}"
            if note:
                line += f" — {note}"
            print(line)

        if args.install_secret_to:
            provisioner.install_secret(args.install_secret_to)
            print("[     OK] secret installation — value never printed")

        if not args.apply:
            if report.converged:
                print("[delia-mcp-provision] NO_DRIFT")
                return 0
            print("[delia-mcp-provision] DRIFT_DETECTED")
            return 2
        print("[delia-mcp-provision] APPLIED")
        return 0
    except ProvisioningError as exc:
        print(f"[delia-mcp-provision] FAIL_CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
