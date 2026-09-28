#!/usr/bin/env python3
"""IDENTITY-002 — one-shot GLPI firstname/realname repair against Keycloak canonical identity.

Bounded administrative migration, NOT a runtime capability:

- NEW users keep SAML JIT parity (untouched by this script).
- LEGACY users get one controlled repair pass.

Default is DRY-RUN — writes only happen with ``--apply``.

Mapping evidence hierarchy:
    A. helpdesk.oauth_sessions subject → live GLPI session → user_id (strong)
    B. exact unique email match (Keycloak email ↔ GLPI useremails/name) — only
       when unique on BOTH sides and unambiguous.
Never name-similarity matching. Ambiguous → MANUAL_REVIEW, never written.

Canonical fields (Keycloak wins when mapping is confident):
    firstName → glpi_users.firstname
    lastName  → glpi_users.realname

Apply flow per candidate:
    reread GLPI → recompute diff → write ONLY divergent allowed fields
    → authoritative reread → verify exact parity → audit record.

Usage (inside delpi-helpdesk-api container or with PYTHONPATH=/app):
    python scripts/repair_glpi_user_names.py --dry-run --report /tmp/report.json
    python scripts/repair_glpi_user_names.py --apply --only-glpi-user-id 80
    python scripts/repair_glpi_user_names.py --apply --report /tmp/apply.json

Required env:
    KEYCLOAK_ADMIN_BASE_URL     e.g. https://minhadelpi.com.br/auth
    KEYCLOAK_ADMIN_REALM        default: delpi
    KEYCLOAK_ADMIN / KEYCLOAK_ADMIN_PASSWORD  (master-realm admin-cli user)
    GLPI_REPAIR_BASE_URL        e.g. https://helpdesk.centraldelpi.com.br
    GLPI_REPAIR_APP_TOKEN       legacy apirest App-Token (bounded exec only)
    GLPI_REPAIR_USER_TOKEN      api_token of an admin GLPI user, OR:
    GLPI_REPAIR_BASIC_USER / GLPI_REPAIR_BASIC_PASSWORD
                                login/password of a bounded migration principal
    PLUGINS_DB_* + HELPDESK_TOKEN_ENCRYPTION_KEY  (oauth_sessions, mapping A)
    GLPI_OAUTH_CLIENT_ID / GLPI_OAUTH_CLIENT_SECRET (token refresh for mapping A)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger("helpdesk.repair_glpi_user_names")

WRITABLE_FIELDS = ("firstname", "realname")

# ---------------------------------------------------------------------------
# Status vocabulary
# ---------------------------------------------------------------------------
IN_SYNC = "IN_SYNC"
DRIFT_FIRSTNAME = "DRIFT_FIRSTNAME"
DRIFT_REALNAME = "DRIFT_REALNAME"
DRIFT_BOTH = "DRIFT_BOTH"
MISSING_CANONICAL = "MISSING_CANONICAL"
AMBIGUOUS_MAPPING = "AMBIGUOUS_MAPPING"
UNRESOLVED = "UNRESOLVED"  # KC user with no confident GLPI mapping at all
OUT_OF_SCOPE = "OUT_OF_SCOPE"  # GLPI user not reachable by any KC identity
AUTHORITY_REQUIRED = "AUTHORITY_REQUIRED"  # entity-0-only target (flag on record)
NOOP = "NOOP"
UPDATED = "UPDATED"
FAILED_FORBIDDEN = "FAILED_FORBIDDEN"
FAILED_UNAVAILABLE = "FAILED_UNAVAILABLE"
FAILED_VERIFICATION = "FAILED_VERIFICATION"
FAILED_WRITE = "FAILED_WRITE"


# ---------------------------------------------------------------------------
# Thin provider clients (urllib; probe-script convention)
# ---------------------------------------------------------------------------
def _request(
    method: str,
    url: str,
    *,
    headers: dict | None = None,
    form: dict | None = None,
    json_body: dict | None = None,
    timeout: float = 30.0,
) -> tuple[int, object]:
    data = None
    hdrs = {
        "Accept": "application/json",
        "User-Agent": "delpi-helpdesk-repair/1.0",
    }
    if headers:
        hdrs.update(headers)
    if form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    elif json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8") or "null"
            try:
                return int(resp.status), json.loads(raw)
            except json.JSONDecodeError:
                return int(resp.status), raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = raw[:500]
        return int(exc.code), body
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, None


def kc_admin_token(base: str, user: str, password: str) -> str | None:
    code, body = _request(
        "POST",
        f"{base}/realms/master/protocol/openid-connect/token",
        form={
            "client_id": "admin-cli",
            "username": user,
            "password": password,
            "grant_type": "password",
        },
    )
    if code == 200 and isinstance(body, dict):
        return body.get("access_token")
    return None


def kc_list_users(base: str, realm: str, token: str, page_size: int = 500) -> list[dict]:
    users: list[dict] = []
    first = 0
    while True:
        code, body = _request(
            "GET",
            f"{base}/admin/realms/{realm}/users?first={first}&max={page_size}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if code != 200 or not isinstance(body, list):
            break
        users.extend(body)
        if len(body) < page_size:
            break
        first += page_size
    return users


def glpi_init_session(
    base: str,
    app_token: str,
    user_token: str = "",
    *,
    basic_user: str = "",
    basic_password: str = "",
) -> str | None:
    """Legacy apirest session via user_token OR login/password (Basic)."""
    headers = {"App-Token": app_token}
    if user_token:
        headers["Authorization"] = f"user_token {user_token}"
    elif basic_user and basic_password:
        import base64

        cred = base64.b64encode(f"{basic_user}:{basic_password}".encode()).decode()
        headers["Authorization"] = f"Basic {cred}"
    else:
        return None
    code, body = _request(
        "GET",
        f"{base}/apirest.php/initSession?get_full_session=true",
        headers=headers,
    )
    if code == 200 and isinstance(body, dict):
        return body.get("session_token")
    return None


def glpi_kill_session(base: str, app_token: str, session_token: str) -> None:
    _request(
        "GET",
        f"{base}/apirest.php/killSession",
        headers={"App-Token": app_token, "Session-Token": session_token},
    )


def glpi_get(base: str, app_token: str, session_token: str, path: str) -> tuple[int, object]:
    return _request(
        "GET",
        f"{base}/apirest.php{path}",
        headers={"App-Token": app_token, "Session-Token": session_token},
    )


def glpi_put_user(
    base: str, app_token: str, session_token: str, user_id: int, fields: dict
) -> tuple[int, object]:
    """PUT /User/{id} with a body restricted to the writable allowlist."""
    bad = set(fields) - set(WRITABLE_FIELDS)
    if bad:
        raise ValueError(f"non-writable fields rejected: {sorted(bad)}")
    return _request(
        "PUT",
        f"{base}/apirest.php/User/{int(user_id)}",
        headers={"App-Token": app_token, "Session-Token": session_token},
        json_body={"input": fields},
    )


def glpi_refresh_access_token(
    base: str, client_id: str, client_secret: str, refresh_token: str
) -> str | None:
    code, body = _request(
        "POST",
        f"{base}/api.php/token",
        form={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        },
    )
    if code == 200 and isinstance(body, dict):
        return body.get("access_token")
    return None


def glpi_session_user_id(base: str, access_token: str) -> int | None:
    code, body = _request(
        "GET",
        f"{base}/api.php/v2.2/session",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if code == 200 and isinstance(body, dict):
        user = body.get("user") or {}
        try:
            return int(user.get("id"))
        except (TypeError, ValueError):
            return None
    return None


# ---------------------------------------------------------------------------
# Mapping + classification (pure — unit-testable)
# ---------------------------------------------------------------------------
def _norm(value) -> str:
    return " ".join(str(value or "").split()).strip()


def _norm_email(value) -> str:
    return _norm(value).lower()


def glpi_user_emails(base: str, app_token: str, session_token: str) -> dict[int, set[str]]:
    """users_id → {emails}. Tries the UserEmail collection first."""
    out: dict[int, set[str]] = {}
    code, body = glpi_get(base, app_token, session_token, "/UserEmail?range=0-9999")
    if code == 200 and isinstance(body, list):
        for row in body:
            if isinstance(row, dict) and row.get("users_id") and row.get("email"):
                out.setdefault(int(row["users_id"]), set()).add(
                    _norm_email(row["email"])
                )
        return out
    return out


def build_mappings(
    kc_users: list[dict],
    glpi_users: list[dict],
    linked: dict[str, int],
    glpi_emails: dict[int, set[str]],
) -> dict:
    """Return {subject: {"glpi_id": int|None, "via": "session"|"email"|None,
    "ambiguous": bool}}.

    A = proven oauth-session linkage (authoritative).
    B = exact unique email, only when unique on both sides.
    """
    kc_by_id = {u["id"]: u for u in kc_users}
    glpi_by_id = {int(u["id"]): u for u in glpi_users if u.get("id")}

    # Email indexes (confident side-conditions only)
    kc_email_owners: dict[str, list[str]] = {}
    for u in kc_users:
        em = _norm_email(u.get("email"))
        if em:
            kc_email_owners.setdefault(em, []).append(u["id"])
    glpi_email_owners: dict[str, set[int]] = {}
    for uid, emails in glpi_emails.items():
        for em in emails:
            glpi_email_owners.setdefault(em, set()).add(uid)
    # JIT users have name == email — treat as email evidence too
    for u in glpi_users:
        em = _norm_email(u.get("name"))
        if em and "@" in em:
            glpi_email_owners.setdefault(em, set()).add(int(u["id"]))

    mappings: dict[str, dict] = {}
    for sub, kc in kc_by_id.items():
        if sub in linked and linked[sub] in glpi_by_id:
            mappings[sub] = {"glpi_id": int(linked[sub]), "via": "session", "ambiguous": False}
            continue
        em = _norm_email(kc.get("email"))
        if not em:
            mappings[sub] = {"glpi_id": None, "via": None, "ambiguous": False}
            continue
        kc_owners = kc_email_owners.get(em, [])
        g_owners = glpi_email_owners.get(em, set())
        if len(kc_owners) > 1 or len(g_owners) > 1:
            mappings[sub] = {"glpi_id": None, "via": None, "ambiguous": True}
        elif len(kc_owners) == 1 and len(g_owners) == 1:
            mappings[sub] = {"glpi_id": next(iter(g_owners)), "via": "email", "ambiguous": False}
        else:
            mappings[sub] = {"glpi_id": None, "via": None, "ambiguous": False}
    return mappings


def diff_user(kc_user: dict, glpi_user: dict) -> dict:
    """Return {"firstname": canonical, "realname": canonical} for divergent
    fields only — canonical blank never produces a write candidate."""
    diff: dict = {}
    cf = _norm(kc_user.get("firstName"))
    cl = _norm(kc_user.get("lastName"))
    if cf and cf != _norm(glpi_user.get("firstname")):
        diff["firstname"] = cf
    if cl and cl != _norm(glpi_user.get("realname")):
        diff["realname"] = cl
    return diff


def classify(kc_user: dict | None, glpi_user: dict | None, mapping: dict | None,
             *, entity_0_only: bool = False) -> tuple[str, dict]:
    """(status, diff). Pure classification for a KC→GLPI candidate."""
    if kc_user is None:
        return OUT_OF_SCOPE, {}
    if mapping is None or mapping.get("glpi_id") is None:
        if mapping and mapping.get("ambiguous"):
            return AMBIGUOUS_MAPPING, {}
        return UNRESOLVED, {}
    if glpi_user is None:
        return UNRESOLVED, {}
    if not _norm(kc_user.get("firstName")) and not _norm(kc_user.get("lastName")):
        return MISSING_CANONICAL, {}
    diff = diff_user(kc_user, glpi_user)
    if not diff:
        return IN_SYNC, {}
    if entity_0_only:
        return AUTHORITY_REQUIRED, diff
    if set(diff) == {"firstname"}:
        return DRIFT_FIRSTNAME, diff
    if set(diff) == {"realname"}:
        return DRIFT_REALNAME, diff
    return DRIFT_BOTH, diff


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
@dataclass
class RepairPlan:
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    candidates: list[dict] = field(default_factory=list)
    counts: dict = field(default_factory=dict)


def build_plan(
    kc_users: list[dict],
    glpi_users: list[dict],
    mappings: dict[str, dict],
    glpi_entities: dict[int, set[int]],
) -> RepairPlan:
    plan = RepairPlan()
    glpi_by_id = {int(u["id"]): u for u in glpi_users if u.get("id")}
    mapped_glpi: set[int] = set()
    counts: dict[str, int] = {
        "keycloak_users": len(kc_users),
        "glpi_users": len(glpi_users),
        "confidently_mapped": 0,
        "in_sync": 0,
        "drift_firstname": 0,
        "drift_realname": 0,
        "drift_both": 0,
        "missing_canonical": 0,
        "ambiguous": 0,
        "unresolved": 0,
        "authority_required": 0,
    }

    for kc in kc_users:
        sub = kc["id"]
        m = mappings.get(sub)
        gid = m["glpi_id"] if m else None
        g_user = glpi_by_id.get(gid) if gid else None
        entities = glpi_entities.get(gid, set()) if gid else set()
        entity_0_only = bool(entities) and entities == {0}
        status, diff = classify(kc, g_user, m, entity_0_only=entity_0_only)
        if gid:
            mapped_glpi.add(gid)
        key = {
            IN_SYNC: "in_sync",
            DRIFT_FIRSTNAME: "drift_firstname",
            DRIFT_REALNAME: "drift_realname",
            DRIFT_BOTH: "drift_both",
            MISSING_CANONICAL: "missing_canonical",
            AMBIGUOUS_MAPPING: "ambiguous",
            UNRESOLVED: "unresolved",
            AUTHORITY_REQUIRED: "authority_required",
        }.get(status)
        if key:
            counts[key] += 1
        if gid and status not in (UNRESOLVED, AMBIGUOUS_MAPPING):
            counts["confidently_mapped"] += 1
        plan.candidates.append(
            {
                "subject": sub,
                "kc_username": kc.get("username"),
                "glpi_id": gid,
                "glpi_login": (g_user or {}).get("name"),
                "via": (m or {}).get("via"),
                "entities": sorted(entities),
                "status": status,
                "diff_fields": sorted(diff),
                "new_values": diff,  # operator-review artifact only
            }
        )

    # GLPI users with no confident KC identity — informational
    out_of_scope = [int(u["id"]) for u in glpi_users if u.get("id") and int(u["id"]) not in mapped_glpi]
    counts["glpi_unmapped"] = len(out_of_scope)
    plan.counts = counts
    return plan


def apply_candidate(
    base: str, app_token: str, session_token: str, cand: dict
) -> dict:
    """Write divergent allowed fields for one approved candidate, then verify
    by authoritative reread. Returns an audit record (no name values)."""
    gid = int(cand["glpi_id"])
    record = {
        "run_id": cand.get("run_id"),
        "glpi_id": gid,
        "subject": cand["subject"],
        "fields": [],
        "outcome": FAILED_WRITE,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    code, body = glpi_get(base, app_token, session_token, f"/User/{gid}")
    if code == 403:
        record["outcome"] = FAILED_FORBIDDEN
        return record
    if code != 200 or not isinstance(body, dict):
        record["outcome"] = FAILED_UNAVAILABLE
        return record
    # Recompute diff against fresh provider state — never trust plan snapshot.
    fresh_diff = {
        f: v
        for f, v in (cand.get("new_values") or {}).items()
        if f in WRITABLE_FIELDS and _norm(body.get(f)) != v
    }
    if not fresh_diff:
        record["outcome"] = NOOP
        return record
    try:
        w_code, _w_body = glpi_put_user(base, app_token, session_token, gid, fresh_diff)
    except ValueError:
        record["outcome"] = FAILED_WRITE
        return record
    if w_code == 403:
        record["outcome"] = FAILED_FORBIDDEN
        return record
    if w_code == 0:
        record["outcome"] = FAILED_UNAVAILABLE
        return record
    if w_code >= 400:
        record["outcome"] = FAILED_WRITE
        return record
    # Authoritative reread — HTTP 2xx alone is never PASS.
    code, body = glpi_get(base, app_token, session_token, f"/User/{gid}")
    if code != 200 or not isinstance(body, dict):
        record["outcome"] = FAILED_VERIFICATION
        return record
    if all(_norm(body.get(f)) == v for f, v in fresh_diff.items()):
        record["fields"] = sorted(fresh_diff)
        record["outcome"] = UPDATED
    else:
        record["outcome"] = FAILED_VERIFICATION
    return record


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def _dsn() -> str:
    host = os.environ.get("PLUGINS_DB_HOST", "")
    port = os.environ.get("PLUGINS_DB_PORT", "5432")
    db = os.environ.get("PLUGINS_DB_NAME", "")
    user = os.environ.get("PLUGINS_DB_USER", "")
    pw = os.environ.get("PLUGINS_DB_PASSWORD", "")
    return f"host={host} port={port} dbname={db} user={user} password={pw}"


def load_linked_sessions() -> dict[str, dict]:
    """subject → decrypted token pair (mapping A input). Soft-fail empty."""
    try:
        import psycopg
        from psycopg.rows import dict_row

        from helpdesk_app.infrastructure.crypto import TokenCipher
    except ImportError:
        logger.warning("oauth_sessions unavailable (deps missing) — mapping A skipped")
        return {}
    key = os.environ.get("HELPDESK_TOKEN_ENCRYPTION_KEY", "")
    if not key:
        logger.warning("HELPDESK_TOKEN_ENCRYPTION_KEY absent — mapping A skipped")
        return {}
    try:
        cipher = TokenCipher(key)
        with psycopg.connect(_dsn(), row_factory=dict_row) as conn:
            rows = conn.execute(
                "SELECT subject, access_token_ciphertext, refresh_token_ciphertext "
                "FROM helpdesk.oauth_sessions"
            ).fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.warning("oauth_sessions read failed (%s) — mapping A skipped", type(exc).__name__)
        return {}
    out: dict[str, dict] = {}
    for r in rows:
        try:
            out[r["subject"]] = {
                "access_token": cipher.decrypt(r["access_token_ciphertext"]),
                "refresh_token": cipher.decrypt(r["refresh_token_ciphertext"]),
            }
        except Exception:  # noqa: BLE001
            continue
    return out


def resolve_linked_ids(
    glpi_base: str,
    client_id: str,
    client_secret: str,
    sessions: dict[str, dict],
) -> dict[str, int]:
    """subject → live GLPI user_id via the user's own OAuth session."""
    out: dict[str, int] = {}
    for sub, toks in sessions.items():
        token = toks.get("access_token") or ""
        uid = glpi_session_user_id(glpi_base, token) if token else None
        if uid is None:
            new_tok = glpi_refresh_access_token(
                glpi_base, client_id, client_secret, toks.get("refresh_token") or ""
            )
            if new_tok:
                uid = glpi_session_user_id(glpi_base, new_tok)
        if uid:
            out[sub] = uid
    return out


def glpi_inventory(base: str, app_token: str, session_token: str) -> tuple[list[dict], dict[int, set[int]], dict[int, set[int]]]:
    """(users, users_id→entities, users_id→emails)"""
    code, body = glpi_get(base, app_token, session_token, "/User?range=0-9999&expand_dropdowns=false")
    users = [u for u in body if isinstance(u, dict)] if code == 200 and isinstance(body, list) else []
    entities: dict[int, set[int]] = {}
    code, body = glpi_get(base, app_token, session_token, "/Profile_User?range=0-9999")
    if code == 200 and isinstance(body, list):
        for r in body:
            if isinstance(r, dict) and r.get("users_id"):
                entities.setdefault(int(r["users_id"]), set()).add(int(r.get("entities_id") or 0))
    emails = glpi_user_emails(base, app_token, session_token)
    return users, entities, emails


def glpi_inventory_from_json(path: str) -> tuple[list[dict], dict[int, set[int]], dict[int, set[int]]]:
    """Read-only inventory exported from the GLPI DB (dry-run without API creds).

    Expected shape:
        {"users": [{"id","name","firstname","realname","is_active","authtype"}],
         "entities": {"<users_id>": [entities_id,...]},
         "emails":   {"<users_id>": ["a@b.c",...]}}
    """
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    users = [u for u in data.get("users", []) if isinstance(u, dict)]
    entities = {
        int(k): {int(e) for e in v} for k, v in (data.get("entities") or {}).items()
    }
    emails = {
        int(k): {_norm_email(e) for e in v} for k, v in (data.get("emails") or {}).items()
    }
    return users, entities, emails


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="IDENTITY-002 one-shot GLPI name repair")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", default=True)
    mode.add_argument("--apply", action="store_true")
    ap.add_argument("--only-glpi-user-id", type=int, default=None, action="append",
                    help="restrict apply/dry-run to an explicit approved candidate "
                         "allowlist; may be repeated (canary / frozen batch)")
    ap.add_argument("--include-authority-required", action="store_true",
                    help="also apply AUTHORITY_REQUIRED candidates — only valid when the "
                         "operator-provided credential actually covers their entities")
    ap.add_argument("--glpi-inventory-json", default=None,
                    help="read GLPI inventory from DB-exported JSON instead of apirest "
                         "(dry-run without provider credential)")
    ap.add_argument("--report", default=None, help="JSON report path (protected artifact)")
    args = ap.parse_args(argv)
    apply_mode = bool(args.apply)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    run_id = uuid.uuid4().hex[:12]

    kc_base = (os.environ.get("KEYCLOAK_ADMIN_BASE_URL") or "").rstrip("/")
    realm = os.environ.get("KEYCLOAK_ADMIN_REALM", "delpi")
    kc_user = os.environ.get("KEYCLOAK_ADMIN", "")
    kc_pass = os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "")
    g_base = (os.environ.get("GLPI_REPAIR_BASE_URL") or "").rstrip("/")
    app_tok = os.environ.get("GLPI_REPAIR_APP_TOKEN", "")
    user_tok = os.environ.get("GLPI_REPAIR_USER_TOKEN", "")
    basic_user = os.environ.get("GLPI_REPAIR_BASIC_USER", "")
    basic_pass = os.environ.get("GLPI_REPAIR_BASIC_PASSWORD", "")
    has_glpi_auth = bool(user_tok or (basic_user and basic_pass))
    g_client_id = os.environ.get("GLPI_OAUTH_CLIENT_ID", "")
    g_client_secret = os.environ.get("GLPI_OAUTH_CLIENT_SECRET", "")

    if not (kc_base and kc_user and kc_pass):
        logger.error("Keycloak admin env incomplete")
        return 2
    if apply_mode and not (g_base and app_tok and has_glpi_auth):
        logger.error("GLPI repair env incomplete (required for --apply)")
        return 2
    if not apply_mode and not args.glpi_inventory_json and not (g_base and app_tok and has_glpi_auth):
        logger.error("dry-run needs --glpi-inventory-json or GLPI_REPAIR_* env")
        return 2

    kc_tok = kc_admin_token(kc_base, kc_user, kc_pass)
    if not kc_tok:
        logger.error("Keycloak admin token failed")
        return 2
    sess = None
    if g_base and app_tok and has_glpi_auth:
        sess = glpi_init_session(
            g_base, app_tok, user_tok,
            basic_user=basic_user, basic_password=basic_pass,
        )
        if not sess:
            logger.error("GLPI legacy session failed")
            return 2
    elif apply_mode:
        logger.error("--apply requires a GLPI legacy session")
        return 2

    try:
        kc_users = kc_list_users(kc_base, realm, kc_tok)
        if args.glpi_inventory_json:
            g_users, g_entities, g_emails = glpi_inventory_from_json(args.glpi_inventory_json)
        else:
            g_users, g_entities, g_emails = glpi_inventory(g_base, app_tok, sess or "")
        if not g_base:
            g_base = "https://helpdesk.centraldelpi.com.br"
        linked = resolve_linked_ids(g_base, g_client_id, g_client_secret, load_linked_sessions())
        mappings = build_mappings(kc_users, g_users, linked, g_emails)
        plan = build_plan(kc_users, g_users, mappings, g_entities)

        if args.only_glpi_user_id is not None:
            allowed = set(args.only_glpi_user_id)
            plan.candidates = [
                c for c in plan.candidates if c["glpi_id"] in allowed
            ]

        drift_statuses = {DRIFT_FIRSTNAME, DRIFT_REALNAME, DRIFT_BOTH, AUTHORITY_REQUIRED}
        writable = [c for c in plan.candidates if c["status"] in drift_statuses]

        report = {
            "run_id": run_id,
            "mode": "apply" if apply_mode else "dry-run",
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "counts": plan.counts,
            "mapping": {
                "linked_session": len(linked),
                "email_fallback": sum(1 for m in mappings.values() if m.get("via") == "email"),
                "ambiguities": sum(1 for m in mappings.values() if m.get("ambiguous")),
            },
            "candidates": plan.candidates,
            "apply": [],
        }

        if apply_mode:
            for cand in writable:
                if cand["status"] == AUTHORITY_REQUIRED and not args.include_authority_required:
                    logger.warning(
                        "repair_skip glpi_id=%s reason=authority_required", cand["glpi_id"]
                    )
                    continue
                cand["run_id"] = run_id
                rec = apply_candidate(g_base, app_tok, sess, cand)
                report["apply"].append(rec)
                logger.info(
                    "repair_audit run=%s glpi_id=%s subject=%s fields=%s outcome=%s",
                    run_id, rec["glpi_id"], rec["subject"], rec["fields"], rec["outcome"],
                )
                time.sleep(0.2)  # bounded, sequential
        else:
            for cand in writable:
                logger.info(
                    "dry_run_drift glpi_id=%s via=%s status=%s fields=%s",
                    cand["glpi_id"], cand["via"], cand["status"], cand["diff_fields"],
                )

        print(json.dumps({"counts": plan.counts, "mapping": report["mapping"],
                          "writes_planned": len(writable) if apply_mode else 0,
                          "apply_records": len(report["apply"])}, indent=2))
        if args.report:
            with open(args.report, "w", encoding="utf-8", errors="replace") as fh:
                json.dump(report, fh, indent=2, ensure_ascii=False)
            os.chmod(args.report, 0o600)
            logger.info("report written %s (mode 600, contains identity details)", args.report)

        if apply_mode:
            failed = [r for r in report["apply"] if r["outcome"] not in (UPDATED, NOOP)]
            return 1 if failed else 0
        return 0
    finally:
        if sess:
            glpi_kill_session(g_base, app_tok, sess)


if __name__ == "__main__":
    sys.exit(main())
