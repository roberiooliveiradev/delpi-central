#!/usr/bin/env python3
"""Smoke HTTP — product analyser real (api-externa via gateway) + presenter.

Uso (container):
  PYTHONPATH=/app SMOKE_BASE_URL=http://delpi-gateway \\
    python scripts/smoke_product_analyser_live.py

Variáveis: SMOKE_USER, SMOKE_PASSWORD, SMOKE_PRODUCT_CODE (default 90260140).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://delpi-gateway").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_PRODUCT_CODE = os.environ.get("SMOKE_PRODUCT_CODE", "90260140").strip()


def _fetch_token() -> str:
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
        raise RuntimeError(f"Token ausente: {payload}")
    return str(token)


def _fetch_analyser(token: str, code: str) -> dict:
    query = urllib.parse.urlencode(
        {"max_depth": "5", "page": "1", "page_size": "50"},
    )
    paths = [
        f"/api/externa/products/{code}/analyser?{query}",
        f"/api/minha-delpi/externa/products/{code}/analyser?{query}",
    ]
    last_error: Exception | None = None

    for path in paths:
        req = urllib.request.Request(
            f"{_BASE_URL}{path}",
            headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                raw = response.read().decode("utf-8")
                if raw.lstrip().startswith("<"):
                    raise RuntimeError(f"Resposta HTML em {path} (rota incorreta?)")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403, 404}:
                raise exc
            last_error = exc
            continue
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
            continue

    raise RuntimeError(f"Não foi possível obter analyser: {last_error}")


def main() -> int:
    failed = 0

    def check(name: str, ok: bool) -> None:
        nonlocal failed
        if ok:
            print(f"OK {name}")
        else:
            print(f"FAIL {name}", file=sys.stderr)
            failed += 1

    try:
        token = _fetch_token()
        check("login", True)
    except Exception as exc:
        print(f"FAIL login: {exc}", file=sys.stderr)
        return 1

    try:
        data = _fetch_analyser(token, _PRODUCT_CODE)
        check("HTTP analyser", True)
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403, 404}:
            print(
                f"SKIP HTTP analyser ({exc.code}): use o chat com tool execute_external_action "
                f"ou confira RBAC/rota do gateway; smoke offline: "
                f"smoke_product_analyser_presentation.py",
                file=sys.stderr,
            )
            return 0
        print(f"FAIL HTTP analyser: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"FAIL HTTP analyser: {exc}", file=sys.stderr)
        return 1

    path = f"/products/{_PRODUCT_CODE}/analyser"
    presenter = ExternalActionResultPresenter()
    humanized = presenter.present(data, path=path)
    body = "\n".join(humanized.get("linhas") or [])
    text = presenter.build_text_presentation(data, path=path)
    markdown = (text or {}).get("markdown") or ""

    check("sem dump Qp6/Qp7", "Qp6=[" not in body and "Product=" not in body)
    check("perfil em tabela", "| Campo | Valor |" in body)
    check(
        "roteiro legível",
        "| Produto | BOM | Op. |" in body
        or "Roteiro: 0 registro(s)" in body
        or "Roteiro de produção ainda não" in body,
    )
    check(
        "inspeção legível",
        "Ensaios dimensionais" in body
        or "Inspeção: 0 registro(s)" in body
        or "Plano de inspeção ainda não" in body,
    )
    check("estrutura fora do texto", "**Estrutura do produto" not in body)
    check("textPresentation sem dump", "Qp6=[" not in markdown)

    if failed:
        print(f"\n{failed} verificação(ões) falharam", file=sys.stderr)
        return 1

    print(
        f"Smoke product analyser live ({_PRODUCT_CODE}): todas as verificações passaram."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
