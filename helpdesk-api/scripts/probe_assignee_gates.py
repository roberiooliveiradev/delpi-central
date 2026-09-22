#!/usr/bin/env python3
"""E0.S1 — live HLAPI gates for TeamMember assigned + User catalog by id."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

from helpdesk_app.infrastructure.crypto import TokenCipher
from helpdesk_app.infrastructure.glpi.http_client import HttpxGlpiClient
from helpdesk_app.infrastructure.glpi.mapping import team_member_observer_body


def _dsn() -> str:
    host = os.environ["PLUGINS_DB_HOST"]
    port = os.environ.get("PLUGINS_DB_PORT", "5432")
    db = os.environ["PLUGINS_DB_NAME"]
    user = os.environ["PLUGINS_DB_USER"]
    password = os.environ["PLUGINS_DB_PASSWORD"]
    ssl = os.environ.get("PLUGINS_DB_SSLMODE", "prefer")
    return f"host={host} port={port} dbname={db} user={user} password={password} sslmode={ssl}"


def _load_sessions(cipher: TokenCipher) -> list[dict]:
    with psycopg.connect(_dsn(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT subject, access_token_ciphertext, refresh_token_ciphertext, access_expires_at
                FROM helpdesk.oauth_sessions
                ORDER BY updated_at DESC
                LIMIT 40
                """
            )
            rows = cur.fetchall()
    out = []
    for row in rows:
        out.append(
            {
                "subject": row["subject"],
                "access_token": cipher.decrypt(row["access_token_ciphertext"]),
                "refresh_token": cipher.decrypt(row["refresh_token_ciphertext"]),
            }
        )
    return out


def _raw(method: str, url: str, *, token: str, json_body: dict | None = None) -> tuple[int, object]:
    data = None
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8") or "null"
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = raw
            return int(resp.status), body
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = raw[:500]
        return int(exc.code), body


def _display_name(user: dict) -> str:
    first = str(user.get("firstname") or "").strip()
    last = str(user.get("realname") or "").strip()
    name = f"{first} {last}".strip()
    return name or str(user.get("username") or user.get("name") or user.get("id") or "")


def _token_for(client: HttpxGlpiClient, session: dict) -> tuple[str, str]:
    try:
        tokens = client.refresh(session["refresh_token"])
        return tokens.access_token, "ok"
    except Exception as exc:  # noqa: BLE001
        return session["access_token"], f"fail:{type(exc).__name__}"


def probe_one(client: HttpxGlpiClient, base: str, session: dict, label: str) -> dict:
    result: dict = {"label": label, "subject": session["subject"], "gates": {}, "catalog_paths": {}}
    token, refresh_status = _token_for(client, session)
    result["token_refresh"] = refresh_status

    # Baseline Assistance rights
    code, tickets = _raw(
        "GET",
        f"{base}/api.php/v2.2/Assistance/Ticket?start=0&limit=3&sort=id:desc",
        token=token,
    )
    result["ticket_list"] = {
        "status": code,
        "count": len(tickets) if isinstance(tickets, list) else 0,
        "ids": [t.get("id") for t in tickets[:3]] if isinstance(tickets, list) else [],
    }

    # Catalog candidates
    catalog_candidates = [
        ("User_list", "GET", "/api.php/v2.2/Administration/User?start=0&limit=5&filter=" + urllib.parse.quote("is_active==true")),
        ("User_Me", "GET", "/api.php/v2.2/Administration/User/Me"),
        ("User_by_id_2", "GET", "/api.php/v2.2/Administration/User/2"),
        ("User_by_id_6", "GET", "/api.php/v2.2/Administration/User/6"),
        ("Dropdowns_root", "GET", "/api.php/v2.2/Dropdowns/"),
        ("Contact_list", "GET", "/api.php/v2.2/Management/Contact?start=0&limit=3"),
    ]
    known_user_ids: list[int] = []
    for name, method, path in catalog_candidates:
        c, body = _raw(method, f"{base}{path}", token=token)
        sample = None
        if isinstance(body, list):
            sample = [{"id": x.get("id"), "name": _display_name(x)} for x in body[:3] if isinstance(x, dict)]
            for x in body:
                if isinstance(x, dict) and x.get("id"):
                    known_user_ids.append(int(x["id"]))
        elif isinstance(body, dict):
            sample = {"id": body.get("id"), "username": body.get("username"), "keys": list(body.keys())[:8]}
            if body.get("id") and "User" in name:
                known_user_ids.append(int(body["id"]))
        result["catalog_paths"][name] = {"status": c, "sample": sample}

    # Collect user ids from ticket team if present
    if isinstance(tickets, list):
        for t in tickets:
            team = t.get("team") or []
            if isinstance(team, list):
                for m in team:
                    if isinstance(m, dict) and m.get("id") and str(m.get("type") or "User") in ("User", "user"):
                        known_user_ids.append(int(m["id"]))

    # Also try GET ticket detail for team
    ticket_id = None
    if isinstance(tickets, list) and tickets:
        ticket_id = tickets[0].get("id")
        if ticket_id:
            d_code, detail = _raw(
                "GET", f"{base}/api.php/v2.2/Assistance/Ticket/{int(ticket_id)}", token=token
            )
            result["ticket_detail_status"] = d_code
            if isinstance(detail, dict):
                for m in detail.get("team") or []:
                    if isinstance(m, dict) and m.get("id"):
                        known_user_ids.append(int(m["id"]))

    known_user_ids = list(dict.fromkeys(known_user_ids))
    result["known_user_ids"] = known_user_ids[:10]

    # G-A4: catalog by id — either list OR get-by-id returning id+display
    list_ok = result["catalog_paths"]["User_list"]["status"] == 200
    by_id_ok = any(
        result["catalog_paths"][k]["status"] == 200 for k in ("User_by_id_2", "User_by_id_6", "User_Me")
    )
    # Search by name filter still keyed by id in response
    search_q = urllib.parse.urlencode(
        {"filter": 'username=like="%"', "start": 0, "limit": 5}
    )
    s_code, s_body = _raw(
        "GET", f"{base}/api.php/v2.2/Administration/User?{search_q}", token=token
    )
    result["catalog_paths"]["User_filter_like"] = {
        "status": s_code,
        "count": len(s_body) if isinstance(s_body, list) else 0,
    }
    if isinstance(s_body, list):
        for u in s_body:
            if isinstance(u, dict) and u.get("id"):
                known_user_ids.append(int(u["id"]))
        known_user_ids = list(dict.fromkeys(known_user_ids))

    result["gates"]["G-A4"] = {
        "ok": list_ok or (by_id_ok and known_user_ids),
        "list_status": result["catalog_paths"]["User_list"]["status"],
        "filter_status": s_code,
        "by_id_ok": by_id_ok,
        "path_canonical": "/Administration/User" if list_ok or s_code == 200 else (
            "/Administration/User/{id}" if by_id_ok else None
        ),
        "note": "catalog must expose numeric id; name-only forbidden",
    }

    # Create dedicated ticket for write
    created_id = None
    cats_code, cats = _raw(
        "GET",
        f"{base}/api.php/v2.2/Dropdowns/ITILCategory?start=0&limit=1&filter="
        + urllib.parse.quote("is_helpdesk_visible==true"),
        token=token,
    )
    category_id = None
    if cats_code == 200 and isinstance(cats, list) and cats:
        category_id = cats[0].get("id")
    result["category"] = {"status": cats_code, "id": category_id}

    if category_id and result["ticket_list"]["status"] == 200:
        c_code, c_body = _raw(
            "POST",
            f"{base}/api.php/v2.2/Assistance/Ticket",
            token=token,
            json_body={
                "name": f"[E0 probe assignee] {datetime.now(timezone.utc).isoformat()}",
                "content": "Probe TeamMember assigned — safe to close",
                "urgency": 3,
                "category": {"id": int(category_id)},
            },
        )
        result["create_ticket"] = {"status": c_code}
        if c_code in (200, 201):
            if isinstance(c_body, dict):
                created_id = c_body.get("id") or c_body.get("ID")
            elif isinstance(c_body, (int, str)):
                created_id = int(c_body)
            ticket_id = created_id or ticket_id
            result["create_ticket"]["id"] = created_id

    result["ticket_id"] = ticket_id

    assignee_id = known_user_ids[0] if known_user_ids else None
    sibling_id = known_user_ids[1] if len(known_user_ids) > 1 else None
    # Fallback: try common technician ids from env or historically used
    if assignee_id is None:
        for guess in (2, 6, 4, 3, 5):
            g_code, g_body = _raw(
                "GET", f"{base}/api.php/v2.2/Administration/User/{guess}", token=token
            )
            result["catalog_paths"][f"User_guess_{guess}"] = {"status": g_code}
            if g_code == 200 and isinstance(g_body, dict) and g_body.get("id"):
                assignee_id = int(g_body["id"])
                known_user_ids.append(assignee_id)
                break

    if not ticket_id:
        result["gates"]["G-A1_or_A2"] = {"ok": False, "reason": "no writable ticket"}
        result["gates"]["G-A3"] = {"ok": False, "reason": "no ticket"}
        result["gates"]["G-A5"] = {"ok": False, "reason": "no ticket"}
        return result

    if not assignee_id:
        # Still try assign with id=2 to observe 403 vs 201 (rights vs catalog)
        assignee_id = 2
        result["assignee_fallback"] = True

    body = {"type": "User", "role": "assigned", "id": int(assignee_id)}
    a_code, a_body = _raw(
        "POST",
        f"{base}/api.php/v2.2/Assistance/Ticket/{int(ticket_id)}/TeamMember",
        token=token,
        json_body=body,
    )
    result["gates"]["G-A1_or_A2"] = {
        "status": a_code,
        "ok": a_code in (200, 201),
        "assignee_id": assignee_id,
        "request_body": body,
        "error": a_body if a_code >= 400 else None,
    }

    g_code, g_body = _raw(
        "GET",
        f"{base}/api.php/v2.2/Assistance/Ticket/{int(ticket_id)}/TeamMember/assigned",
        token=token,
    )
    result["assigned_after_first"] = {"status": g_code, "body": g_body}

    # Reassign
    if sibling_id is None:
        sibling_id = 6 if int(assignee_id) != 6 else 4
    d_code, d_body = _raw(
        "DELETE",
        f"{base}/api.php/v2.2/Assistance/Ticket/{int(ticket_id)}/TeamMember",
        token=token,
        json_body={"type": "User", "role": "assigned", "id": int(assignee_id)},
    )
    # Also try DELETE without body / with query — capture status
    r_code, r_body = _raw(
        "POST",
        f"{base}/api.php/v2.2/Assistance/Ticket/{int(ticket_id)}/TeamMember",
        token=token,
        json_body={"type": "User", "role": "assigned", "id": int(sibling_id)},
    )
    g2_code, g2_body = _raw(
        "GET",
        f"{base}/api.php/v2.2/Assistance/Ticket/{int(ticket_id)}/TeamMember/assigned",
        token=token,
    )
    assigned_ids = [m.get("id") for m in g2_body] if isinstance(g2_body, list) else []
    result["gates"]["G-A3"] = {
        "delete_status": d_code,
        "delete_error": d_body if d_code >= 400 else None,
        "reassign_status": r_code,
        "reassign_to": sibling_id,
        "assigned_ids": assigned_ids,
        "ok": r_code in (200, 201)
        and (sibling_id in assigned_ids or a_code not in (200, 201)),
        "duplicate_actors": len(assigned_ids) > 1,
    }

    # Negative: impossible id
    n_code, n_body = _raw(
        "POST",
        f"{base}/api.php/v2.2/Assistance/Ticket/{int(ticket_id)}/TeamMember",
        token=token,
        json_body={"type": "User", "role": "assigned", "id": 999999999},
    )
    result["gates"]["G-A5"] = {
        "status": n_code,
        "ok": n_code in (400, 403, 404),
        "body": n_body if n_code >= 400 else n_body,
    }

    # Observer sanity
    obs_id = known_user_ids[0] if known_user_ids else assignee_id
    o_code, o_body = _raw(
        "POST",
        f"{base}/api.php/v2.2/Assistance/Ticket/{int(ticket_id)}/TeamMember",
        token=token,
        json_body=team_member_observer_body(int(obs_id)),
    )
    result["observer_sanity"] = {"status": o_code, "ok": o_code in (200, 201), "error": o_body if o_code >= 400 else None}

    return result


def main() -> int:
    base = os.environ["GLPI_BASE_URL"].rstrip("/")
    cipher = TokenCipher(os.environ["HELPDESK_TOKEN_ENCRYPTION_KEY"])
    client = HttpxGlpiClient(
        base_url=base,
        client_id=os.environ["GLPI_OAUTH_CLIENT_ID"],
        client_secret=os.environ["GLPI_OAUTH_CLIENT_SECRET"],
        redirect_uri=os.environ["GLPI_OAUTH_REDIRECT_URI"],
    )
    sessions = _load_sessions(cipher)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "session_count": len(sessions),
        "subjects": [s["subject"] for s in sessions],
        "probes": [],
    }
    if not sessions:
        report["error"] = "no oauth sessions"
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    seen = set()
    for session in sessions:
        if session["subject"] in seen:
            continue
        seen.add(session["subject"])
        report["probes"].append(probe_one(client, base, session, f"subject-{len(seen)}"))
        if len(seen) >= 5:
            break

    # Summary
    summary = {"any_assign_ok": False, "any_catalog_ok": False, "any_ticket_ok": False}
    for p in report["probes"]:
        if p.get("ticket_list", {}).get("status") == 200:
            summary["any_ticket_ok"] = True
        if p.get("gates", {}).get("G-A4", {}).get("ok"):
            summary["any_catalog_ok"] = True
        if p.get("gates", {}).get("G-A1_or_A2", {}).get("ok"):
            summary["any_assign_ok"] = True
    report["summary"] = summary
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
