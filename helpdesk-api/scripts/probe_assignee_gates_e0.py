#!/usr/bin/env python3
"""E0.S1 live gates — OAuth via legacy user_token + HLAPI on internal GLPI."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import httpx

INTERNAL_BASE = os.environ.get("GLPI_INTERNAL_BASE", "http://inventario-ti-glpi-1")
PUBLIC_REDIR = os.environ["GLPI_OAUTH_REDIRECT_URI"]
CLIENT_ID = os.environ["GLPI_OAUTH_CLIENT_ID"]
CLIENT_SECRET = os.environ["GLPI_OAUTH_CLIENT_SECRET"]
APP_TOKEN = os.environ["GLPI_LEGACY_APP_TOKEN"]


def oauth_from_user_token(user_token: str, label: str) -> dict:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    with httpx.Client(timeout=45.0, follow_redirects=False) as c:
        r = c.get(
            f"{INTERNAL_BASE}/apirest.php/initSession",
            headers={
                "App-Token": APP_TOKEN,
                "Authorization": f"user_token {user_token}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
        )
        if r.status_code != 200:
            return {"label": label, "error": f"initSession {r.status_code}", "body": r.text[:300]}
        st = r.json()["session_token"]
        # Establish anonymous cookie name, then overwrite value with API session_token
        # (proven path: web session cookie == legacy session_token).
        c.get(f"{INTERNAL_BASE}/", headers={"User-Agent": "Mozilla/5.0"})
        cookie_name = next(iter(c.cookies.keys()), None)
        if not cookie_name:
            return {"label": label, "error": "no_glpi_cookie"}
        params = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": PUBLIC_REDIR,
            "scope": "api",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "accept": "1",
        }
        r = c.get(
            f"{INTERNAL_BASE}/api.php/authorize",
            params=params,
            headers={"User-Agent": "Mozilla/5.0", "Cookie": f"{cookie_name}={st}"},
            cookies={cookie_name: st},
        )
        loc = r.headers.get("location") or ""
        if "code=" not in loc:
            return {
                "label": label,
                "error": "no_code",
                "status": r.status_code,
                "loc": loc[:200],
                "cookie": cookie_name[:24],
            }
        code = parse_qs(urlparse(loc).query).get("code", [None])[0]
        tr = c.post(
            f"{INTERNAL_BASE}/api.php/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": PUBLIC_REDIR,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code_verifier": verifier,
            },
        )
        if tr.status_code != 200:
            return {"label": label, "error": f"token {tr.status_code}", "body": tr.text[:300]}
        tokens = tr.json()
        access = tokens["access_token"]
        # identify
        me = c.get(
            f"{INTERNAL_BASE}/api.php/v2.2/Administration/User/Me",
            headers={"Authorization": f"Bearer {access}", "Accept": "application/json", "User-Agent": "Mozilla/5.0"},
        )
        me_body = me.json() if me.status_code < 400 else {"status": me.status_code, "body": me.text[:200]}
        return {
            "label": label,
            "access_token": access,
            "me_status": me.status_code,
            "me": me_body if isinstance(me_body, dict) else {},
            "session_token_legacy": st,
        }


def raw(c: httpx.Client, method: str, path: str, token: str, json_body=None, params=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    r = c.request(method, f"{INTERNAL_BASE}{path}", headers=headers, json=json_body, params=params)
    try:
        body = r.json()
    except Exception:
        body = r.text[:500]
    return r.status_code, body


def display_name(user: dict) -> str:
    first = str(user.get("firstname") or "").strip()
    last = str(user.get("realname") or "").strip()
    name = f"{first} {last}".strip()
    return name or str(user.get("username") or user.get("id") or "")


def probe_gates(access: str, label: str, me: dict) -> dict:
    out = {"label": label, "gates": {}, "me_id": me.get("id"), "username": me.get("username")}
    with httpx.Client(timeout=45.0) as c:
        # G-A4 catalog
        s, users = raw(
            c,
            "GET",
            "/api.php/v2.2/Administration/User",
            access,
            params={"start": 0, "limit": 10, "filter": "is_active==true", "sort": "id:asc"},
        )
        sample = []
        ids = []
        if isinstance(users, list):
            for u in users:
                ids.append(int(u["id"]))
                sample.append({"id": u["id"], "display_name": display_name(u)})
        out["gates"]["G-A4"] = {
            "ok": s in (200, 206) and bool(ids),
            "status": s,
            "count": len(ids),
            "sample": sample[:5],
            "path": "/Administration/User?filter=is_active==true",
        }

        # categories + create ticket
        cs, cats = raw(
            c,
            "GET",
            "/api.php/v2.2/Dropdowns/ITILCategory",
            access,
            params={"start": 0, "limit": 1, "filter": "is_helpdesk_visible==true"},
        )
        category_id = cats[0]["id"] if cs in (200, 206) and isinstance(cats, list) and cats else None
        out["category_id"] = category_id
        if not category_id:
            out["gates"]["G-A1_or_A2"] = {"ok": False, "reason": "no category"}
            return out

        ts, tbody = raw(
            c,
            "POST",
            "/api.php/v2.2/Assistance/Ticket",
            access,
            json_body={
                "name": f"[E0 assignee probe] {label} {datetime.now(timezone.utc).isoformat()}",
                "content": "Probe TeamMember role=assigned — safe to close",
                "urgency": 3,
                "category": {"id": int(category_id)},
            },
        )
        ticket_id = None
        if ts in (200, 201) and isinstance(tbody, dict):
            ticket_id = tbody.get("id")
        out["create_ticket"] = {"status": ts, "id": ticket_id}
        if not ticket_id:
            out["gates"]["G-A1_or_A2"] = {"ok": False, "status": ts, "body": tbody}
            return out

        # pick assignees: prefer others from catalog
        me_id = int(me["id"]) if me.get("id") else None
        assignee_candidates = [i for i in ids if me_id is None or i != me_id]
        if not assignee_candidates:
            assignee_candidates = ids or ([me_id] if me_id else [2])
        assignee_id = assignee_candidates[0]
        sibling_id = assignee_candidates[1] if len(assignee_candidates) > 1 else (
            assignee_candidates[0] if assignee_candidates else 2
        )

        body = {"type": "User", "role": "assigned", "id": int(assignee_id)}
        as_, ab = raw(
            c,
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/TeamMember",
            access,
            json_body=body,
        )
        out["gates"]["G-A1_or_A2"] = {
            "ok": as_ in (200, 201),
            "status": as_,
            "assignee_id": assignee_id,
            "request_body": body,
            "error": ab if as_ >= 400 else None,
        }

        gs, gb = raw(
            c,
            "GET",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/TeamMember/assigned",
            access,
        )
        out["assigned_after"] = {"status": gs, "body": gb}

        # G-A3 reassign: DELETE then POST sibling
        ds, db = raw(
            c,
            "DELETE",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/TeamMember",
            access,
            json_body={"type": "User", "role": "assigned", "id": int(assignee_id)},
        )
        # OpenAPI DELETE has no body — if 4xx try without body after GET ids
        if ds >= 400:
            # try DELETE with query-like path variants not available; second POST may replace
            ds2, db2 = raw(
                c,
                "DELETE",
                f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/TeamMember",
                access,
            )
            out["delete_fallback"] = {"status": ds2, "body": db2 if ds2 >= 400 else "ok"}

        rs, rb = raw(
            c,
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/TeamMember",
            access,
            json_body={"type": "User", "role": "assigned", "id": int(sibling_id)},
        )
        gs2, gb2 = raw(
            c,
            "GET",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/TeamMember/assigned",
            access,
        )
        assigned_ids = [m.get("id") for m in gb2] if isinstance(gb2, list) else []
        out["gates"]["G-A3"] = {
            "ok": rs in (200, 201) and sibling_id in assigned_ids,
            "delete_status": ds,
            "delete_error": db if ds >= 400 else None,
            "reassign_status": rs,
            "reassign_to": sibling_id,
            "assigned_ids": assigned_ids,
            "duplicate_actors": len([x for x in assigned_ids if x]) > 1,
        }

        # G-A5 negative
        ns, nb = raw(
            c,
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/TeamMember",
            access,
            json_body={"type": "User", "role": "assigned", "id": 999999999},
        )
        out["gates"]["G-A5"] = {"ok": ns in (400, 403, 404), "status": ns, "body": nb}

        # observer sanity HD-011
        obs_id = me_id or assignee_id
        os_, ob = raw(
            c,
            "POST",
            f"/api.php/v2.2/Assistance/Ticket/{ticket_id}/TeamMember",
            access,
            json_body={"type": "User", "role": "observer", "id": int(obs_id)},
        )
        out["observer_sanity"] = {"ok": os_ in (200, 201), "status": os_, "error": ob if os_ >= 400 else None}
        out["ticket_id"] = ticket_id
    return out


def main() -> int:
    # tokens provided via env (plain), not printed
    tech_token = os.environ.get("PROBE_TECH_USER_TOKEN") or os.environ["GLPI_LEGACY_USER_TOKEN"]
    colab_token = os.environ.get("PROBE_COLAB_USER_TOKEN", "")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "internal_base": INTERNAL_BASE,
        "probes": [],
    }

    tech = oauth_from_user_token(tech_token, "technician")
    if tech.get("access_token"):
        report["probes"].append(
            probe_gates(tech["access_token"], "technician", tech.get("me") or {})
        )
        report["tech_me"] = {"status": tech.get("me_status"), "id": (tech.get("me") or {}).get("id"), "username": (tech.get("me") or {}).get("username")}
    else:
        report["probes"].append({"label": "technician", "error": tech})

    if colab_token:
        colab = oauth_from_user_token(colab_token, "colaborador")
        if colab.get("access_token"):
            report["probes"].append(
                probe_gates(colab["access_token"], "colaborador", colab.get("me") or {})
            )
            report["colab_me"] = {
                "status": colab.get("me_status"),
                "id": (colab.get("me") or {}).get("id"),
                "username": (colab.get("me") or {}).get("username"),
            }
        else:
            report["probes"].append({"label": "colaborador", "error": colab})
    else:
        report["probes"].append({"label": "colaborador", "error": "no PROBE_COLAB_USER_TOKEN"})

    # strip any accidental tokens
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
