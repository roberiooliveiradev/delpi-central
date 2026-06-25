#!/usr/bin/env python3
"""Smoke H11 — workflow de aprovação de eficácia PAC."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _base_url() -> str:
    return (os.environ.get("BASE_URL") or "http://localhost/apps/api-delpi").rstrip("/")


def _token() -> str:
    token = (
        os.environ.get("TOKEN")
        or os.environ.get("API_DELPI_INTERNAL_SERVICE_TOKEN")
        or ""
    ).strip()
    if not token:
        raise SystemExit("Defina TOKEN ou API_DELPI_INTERNAL_SERVICE_TOKEN")
    return token


def _request(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{_base_url()}{path}"
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Content-Type": "application/json",
        },
        data=data,
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode())


def main() -> int:
    suffix = os.environ.get("H11_SUFFIX", "smoke")
    try:
        created = _request(
            "POST",
            "/quality/action-plans",
            {
                "title": f"[H11-{suffix}] Eficácia workflow",
                "branch_code": "01",
                "nonconformity_scope": "internal",
                "severity": "medium",
                "status": "waiting_validation",
            },
        )
        plan = (created.get("data") or created).get("plan") or created.get("data") or created
        plan_id = plan["id"]
        print("plan_id:", plan_id)

        submitted = _request(
            "POST",
            f"/quality/action-plans/{plan_id}/effectiveness-review/submit",
            {
                "effectiveness_status": "effective",
                "notes": "Evidência de smoke H11.",
            },
        )
        print("submit:", (submitted.get("data") or submitted).get("effectiveness_approval_status"))

        pending = _request("GET", "/quality/action-plans/effectiveness-review/pending?page_size=50")
        items = (pending.get("data") or pending).get("items") or []
        assert any(str(item.get("id")) == str(plan_id) for item in items), "plano não na fila pendente"
        print("pending_count:", len(items))

        approved = _request(
            "POST",
            f"/quality/action-plans/{plan_id}/effectiveness-review/approve",
            {},
        )
        print(
            "approved:",
            (approved.get("data") or approved).get("effectiveness_status"),
        )

        audit = _request("GET", f"/quality/action-plans/{plan_id}/audit-log")
        events = [item.get("event_type") for item in (audit.get("data") or audit).get("items") or []]
        print("audit_events:", events)
        assert "effectiveness_submitted" in events
        assert "effectiveness_approved" in events
        return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        print(f"HTTP {exc.code}: {body}", file=sys.stderr)
        return 1
    except AssertionError as exc:
        print(f"Assertion failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
