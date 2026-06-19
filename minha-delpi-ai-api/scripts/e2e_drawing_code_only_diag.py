#!/usr/bin/env python3
"""Diagnóstico — extração PDF live 90263396."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://delpi-gateway").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_PRODUCT_CODE = os.environ.get("SMOKE_PRODUCT_CODE", "90263396").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()


def _request(method, url, *, token=None, body=None, timeout=600):
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _fetch_token():
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USERNAME,
            "password": _PASSWORD,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["access_token"]


def main() -> int:
    token = _fetch_token()
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=5", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    agent_id = str(items[0]["id"])
    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "diag", "agentId": agent_id},
    )
    sid = str(session["id"])
    resp = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{sid}/messages",
        token=token,
        body={"message": f"Analise o desenho {_PRODUCT_CODE}", "agentId": agent_id},
    )

    meta = resp.get("metadata") if isinstance(resp.get("metadata"), dict) else {}
    intel = meta.get("intelligence") if isinstance(meta.get("intelligence"), dict) else {}
    admin = meta.get("adminDebug") if isinstance(meta.get("adminDebug"), dict) else {}

    print("drawingPdfExtractSummary:", json.dumps(intel.get("drawingPdfExtractSummary"), ensure_ascii=False, indent=2)[:4000])

    trace = admin.get("drawingAnalysisTrace") if isinstance(admin.get("drawingAnalysisTrace"), dict) else {}
    for phase in trace.get("phases") or []:
        if not isinstance(phase, dict):
            continue
        if phase.get("id") == "pdf_extraction":
            print("\npdf_extraction phase:", json.dumps(phase, ensure_ascii=False, indent=2)[:5000])

    drawing = intel.get("drawingAnalysis") if isinstance(intel.get("drawingAnalysis"), dict) else {}
    for row in drawing.get("items") or []:
        if not isinstance(row, dict):
            continue
        if "Intermediário" in str(row.get("item") or "") or "Comprimento" in str(row.get("item") or ""):
            print("ITEM:", json.dumps(row, ensure_ascii=False))

    msgs = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{sid}/messages", token=token)
    msg_items = msgs if isinstance(msgs, list) else msgs.get("items", [])
    for msg in msg_items:
        role = msg.get("role")
        md = msg.get("metadata") if isinstance(msg.get("metadata"), dict) else {}
        atts = md.get("attachments") or []
        print(f"\nROLE={role} attachments={len(atts)}")
        if atts:
            print(json.dumps(atts[0], ensure_ascii=False, indent=2)[:1500])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
