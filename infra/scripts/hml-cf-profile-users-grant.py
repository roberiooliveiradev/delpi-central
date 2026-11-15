#!/usr/bin/env python3
"""Grant Core roles to CF HML profile users (U9 R2).

Creates/updates Keycloak-synced Core users via /me, ensures dedicated roles
with the intended permission sets, and assigns them. Passwords stay in
infra/.env.hml — never printed.

Run on the HML host (or any host with Docker + delpi-hml-network):
  python3 infra/scripts/hml-cf-profile-users-grant.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / ".env.hml"
NETWORK = "delpi-hml-network"
KC_CONTAINER = "delpi-hml-keycloak"
REALM = "delpi"
DIRECT_CLIENT = "hml-test-direct"

PROFILES = (
    ("HML_CF_ACCESS", "cf-access", ["controllership-finance.access"]),
    (
        "HML_CF_MANAGE",
        "cf-manage",
        ["controllership-finance.access", "controllership-finance.manage"],
    ),
    (
        "HML_CF_LNF",
        "cf-lnf",
        ["controllership-finance.access", "lancamento-notas-fiscais.access"],
    ),
    ("HML_CF_DRE", "cf-dre", ["controllership-finance.access.dre"]),
)


def load_env() -> dict[str, str]:
    if not ENV.is_file():
        raise SystemExit(f"MISSING {ENV}")
    vals: dict[str, str] = {}
    for line in ENV.read_text().splitlines():
        if "=" not in line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        vals[key.strip()] = value.strip().strip('"').strip("'")
    return vals


def kcadm(admin_user: str, admin_pass: str, args: str) -> str:
    inner = (
        "set -eu; /opt/keycloak/bin/kcadm.sh config credentials "
        "--server http://127.0.0.1:8080/auth --realm master "
        "--user \"$KC_USER\" --password \"$KC_PASS\" >/tmp/kc-login.out 2>&1; "
        f"/opt/keycloak/bin/kcadm.sh {args}"
    )
    proc = subprocess.run(
        [
            "docker",
            "exec",
            "-e",
            f"KC_USER={admin_user}",
            "-e",
            f"KC_PASS={admin_pass}",
            KC_CONTAINER,
            "sh",
            "-c",
            inner,
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"kcadm_fail {args.split()[0]}: {proc.stderr[-400:]}")
    return proc.stdout


def ensure_direct_client(admin_user: str, admin_pass: str) -> None:
    clients = json.loads(
        kcadm(
            admin_user,
            admin_pass,
            f"get clients -r {REALM} -q clientId={DIRECT_CLIENT} --fields id,clientId",
        )
        or "[]"
    )
    if clients:
        print("CLIENT_EXISTS", DIRECT_CLIENT)
        return
    kcadm(
        admin_user,
        admin_pass,
        "create clients -r delpi "
        f"-s clientId={DIRECT_CLIENT} -s enabled=true -s publicClient=true "
        "-s standardFlowEnabled=false -s directAccessGrantsEnabled=true "
        "-s serviceAccountsEnabled=false -s implicitFlowEnabled=false",
    )
    print("CLIENT_CREATED", DIRECT_CLIENT)


def password_token(username: str, password: str) -> str:
    data = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": DIRECT_CLIENT,
            "username": username,
            "password": password,
        }
    ).encode()
    proc = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-i",
            "--network",
            NETWORK,
            "curlimages/curl:8.5.0",
            "--silent",
            "-X",
            "POST",
            "http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/token",
            "-H",
            "Content-Type: application/x-www-form-urlencoded",
            "--data-binary",
            "@-",
        ],
        input=data,
        capture_output=True,
    )
    payload = json.loads(proc.stdout or b"{}")
    token = payload.get("access_token")
    if not token:
        print("TOKEN_FAIL", username, list(payload.keys()))
        raise SystemExit(1)
    return token


def core(method: str, path: str, token: str, body=None):
    cmd = [
        "docker",
        "run",
        "--rm",
        "--network",
        NETWORK,
        "curlimages/curl:8.5.0",
        "--silent",
        "-w",
        "\nHTTP %{http_code}\n",
        "-X",
        method,
        "-H",
        f"Authorization: Bearer {token}",
        "-H",
        "Content-Type: application/json",
        f"http://core-api:8000{path}",
    ]
    if body is not None:
        cmd.extend(["-d", json.dumps(body)])
    proc = subprocess.run(cmd, capture_output=True)
    out = proc.stdout.decode()
    status = next(
        (ln for ln in out.splitlines() if ln.startswith("HTTP ")), "HTTP ?"
    )
    raw = "\n".join(ln for ln in out.splitlines() if not ln.startswith("HTTP "))
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        parsed = {"_raw": raw[:500]}
    return status, parsed


def main() -> int:
    vals = load_env()
    admin_user = vals.get("KEYCLOAK_ADMIN", "admin")
    admin_pass = vals.get("KEYCLOAK_ADMIN_PASSWORD", "")
    if not admin_pass:
        raise SystemExit("KEYCLOAK_ADMIN_PASSWORD ausente em .env.hml")

    tester = vals.get("HML_TEST_USERNAME", "hml-tester")
    tester_pass = vals.get("HML_TEST_PASSWORD", "")
    if not tester_pass or tester_pass.startswith("CHANGE_ME_"):
        raise SystemExit("HML_TEST_PASSWORD inválido em .env.hml")

    ensure_direct_client(admin_user, admin_pass)
    tester_token = password_token(tester, tester_pass)
    status, me = core("GET", "/me", tester_token)
    perms = me.get("permissions") or []
    print(
        "TESTER",
        status,
        "super",
        me.get("is_superadmin"),
        "rbac_manage",
        "rbac.manage" in perms,
    )
    if "rbac.manage" not in perms and not me.get("is_superadmin"):
        raise SystemExit("TESTER_SEM_RBAC_MANAGE")

    status, roles_payload = core("GET", "/admin/rbac/roles", tester_token)
    if not status.endswith("200"):
        raise SystemExit(f"ROLES_LIST_FAIL {status}")
    roles = roles_payload.get("data") or roles_payload.get("roles") or []
    if isinstance(roles_payload, list):
        roles = roles_payload
    role_by_name = {
        str(r.get("name") or ""): r for r in roles if isinstance(r, dict)
    }

    status, perms_payload = core(
        "GET", "/admin/rbac/permissions?page_size=500", tester_token
    )
    if not status.endswith("200"):
        # fallback path used by some Core builds
        status, perms_payload = core("GET", "/admin/rbac/permissions", tester_token)
    perm_rows = (
        perms_payload.get("data")
        or perms_payload.get("permissions")
        or (perms_payload if isinstance(perms_payload, list) else [])
    )
    perm_id_by_code = {
        str(p.get("code") or ""): str(p.get("id") or "")
        for p in perm_rows
        if isinstance(p, dict)
    }

    for env_prefix, default_user, codes in PROFILES:
        username = vals.get(f"{env_prefix}_USERNAME", default_user)
        password = vals.get(f"{env_prefix}_PASSWORD", "")
        if not password or password.startswith("CHANGE_ME_"):
            print("SKIP_PASSWORD", username)
            continue
        role_name = f"hml-cf-profile-{default_user}"
        role = role_by_name.get(role_name)
        if not role:
            st, created = core(
                "POST",
                "/admin/rbac/roles",
                tester_token,
                {"name": role_name, "description": f"U9 HML profile {default_user}"},
            )
            if not (st.endswith("200") or st.endswith("201")):
                print("ROLE_CREATE_FAIL", role_name, st, created)
                continue
            role = created.get("data") or created
            role_by_name[role_name] = role
            print("ROLE_CREATED", role_name)
        else:
            print("ROLE_EXISTS", role_name)

        role_id = str(role.get("id") or "")
        missing = [c for c in codes if c not in perm_id_by_code]
        if missing:
            print("PERM_CODES_MISSING", role_name, missing)
            print(
                "BLOCKER: permissões ausentes no Core HML — importe o manifesto "
                "do plugin ou cadastre os códigos antes de conceder."
            )
            continue
        st, _ = core(
            "PUT",
            f"/admin/rbac/roles/{role_id}/permissions",
            tester_token,
            {"permission_ids": [perm_id_by_code[c] for c in codes]},
        )
        print("ROLE_PERMS", role_name, st, ",".join(codes))

        user_token = password_token(username, password)
        st, user_me = core("GET", "/me", user_token)
        user_id = str(user_me.get("id") or user_me.get("user_id") or "")
        if not user_id:
            print("USER_SYNC_FAIL", username, st)
            continue
        print("USER_SYNCED", username, user_id[:8])

        st, _ = core(
            "PUT",
            f"/admin/rbac/users/{user_id}/roles",
            tester_token,
            {"role_ids": [role_id]},
        )
        print("USER_ROLES", username, st)

        st, check = core("GET", "/me", user_token)
        got = set(check.get("permissions") or [])
        ok = all(c in got for c in codes)
        print("VERIFY", username, "PASS" if ok else "FAIL", sorted(got & set(codes)))

    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
