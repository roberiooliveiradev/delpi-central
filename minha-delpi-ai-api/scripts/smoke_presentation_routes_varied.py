#!/usr/bin/env python3
"""Smoke E2E — apresentação em rotas variadas (produto, estoque, pais, estrutura, KPI, web).

Uso:
  PYTHONPATH=/app SMOKE_BASE_URL=http://delpi-gateway \\
    python scripts/smoke_presentation_routes_varied.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://delpi-gateway").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "90260149").strip()

_ABSENCE_RE = re.compile(
    r"ainda não cadastrad|não há dados suficientes",
    re.IGNORECASE,
)


def _request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(req, timeout=300) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _token() -> str:
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

    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    token = payload.get("access_token")

    if not token:
        raise RuntimeError("Token ausente")

    return str(token)


def _agent_id(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=10", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    return str(items[0]["id"])


def _send(token: str, agent_id: str, message: str) -> dict:
    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": f"Smoke rotas — {message[:40]}", "agentId": agent_id},
    )
    sid = str(session["id"])

    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{sid}/messages",
        token=token,
        body={"message": message, "agentId": agent_id},
    )


def _tool_meta(response: dict) -> dict:
    for call in response.get("toolCalls") or []:
        if call.get("name") == "web_search":
            return {"_web_search": True, "ok": True}

        meta = call.get("metadata")

        if isinstance(meta, dict) and meta.get("ok"):
            return meta

    return {}


def _check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"OK  {label}" + (f" — {detail}" if detail else ""))
        return

    print(f"FAIL {label}" + (f" — {detail}" if detail else ""), file=sys.stderr)
    raise AssertionError(label)


def main() -> int:
    failed = 0
    token = _token()
    agent_id = _agent_id(token)

    scenarios: list[tuple[str, str, callable]] = [
        (
            "produto analyser",
            f"me fale do produto {_PRODUCT}",
            lambda m, t: (
                str(m.get("path") or "").endswith("/analyser")
                and (m.get("stackPresentationPlan") or {}).get("humanizedSections") is True
                and (m.get("stackPresentationPlan") or {}).get("presentationProfile")
                == "product_analyser"
                and "[[table:" not in t
                and "[[arvore]]" not in t
                and not _ABSENCE_RE.search(
                    (t.split("**Destaques**")[-1].split("**Pontos")[0] if "**Destaques**" in t else t)
                )
            ),
        ),
        (
            "estoque produto",
            f"qual o estoque do produto {_PRODUCT}?",
            lambda m, t: (
                "/stock" in str(m.get("path") or "")
                and (m.get("stackPresentationPlan") or {}).get("humanizedSections") is True
                and (m.get("stackPresentationPlan") or {}).get("presentationProfile")
                == "product_stock"
                and "**Destaques**" in t
                and "[[table:" not in t
            ),
        ),
        (
            "onde é usado",
            f"onde é usado o produto {_PRODUCT}",
            lambda m, t: (
                "/parents" in str(m.get("path") or "")
                and (m.get("stackPresentationPlan") or {}).get("humanizedSections") is False
                and ("Onde é usado" in t or "Produtos pai" in t or bool(m.get("treePresentation")))
            ),
        ),
        (
            "estrutura",
            f"estrutura do produto {_PRODUCT}",
            lambda m, t: (
                "/structure" in str(m.get("path") or "")
                and (m.get("stackPresentationPlan") or {}).get("humanizedSections") is False
                and (
                    "Estrutura do produto" in t
                    or (m.get("treePresentation") or m.get("presentation") or {}).get("type") == "tree"
                )
            ),
        ),
        (
            "KPI estoque empresa",
            "qual o valor total de estoque da empresa",
            lambda m, t: (
                "stock-value" in str(m.get("path") or "").lower()
                or "stock_value" in str(m.get("actionId") or "").lower()
                or (m.get("presentation") or {}).get("type") in {"kpi", "table", "chart"}
            ),
        ),
        (
            "pesquisa internet",
            "pesquise na internet as últimas tendências em chicotes automotivos",
            lambda m, t: bool(m.get("_web_search")) and "web_search" not in str(m.get("path") or ""),
        ),
    ]

    for title, message, predicate in scenarios:
        try:
            response = _send(token, agent_id, message)
            meta = _tool_meta(response)
            text = (meta.get("textPresentation") or {}).get("markdown") or ""
            content = str(response.get("content") or "")

            if not meta:
                _check(title, False, "sem tool/metadata ok")
                continue

            ok = predicate(meta, text or content)
            path = meta.get("path") or ("web_search" if meta.get("_web_search") else "?")
            plan = meta.get("stackPresentationPlan") or {}
            _check(
                title,
                ok,
                f"path={path} humanized={plan.get('humanizedSections')} "
                f"profile={plan.get('presentationProfile')}",
            )
        except AssertionError:
            failed += 1
        except Exception as exc:
            print(f"FAIL {title} — {exc}", file=sys.stderr)
            failed += 1

    if failed:
        print(f"\n{failed} cenário(s) falharam", file=sys.stderr)
        return 1

    print("\nSmoke apresentação rotas variadas: todos os cenários passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
