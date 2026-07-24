"""Executa um smoke Nível A (TestClient + mocks)."""

from __future__ import annotations

from typing import Any

from tests.support.route_envelope_smoke import assert_ok_envelope, assert_plain_health, body_json
from tests.support.route_smoke_openapi import (
    body_for_operation,
    fill_path,
    is_multipart,
    looks_binary_path,
    query_for_operation,
)

_PLAIN_HEALTH_OIDS = frozenset({"health", "module_health"})
_BINARY_OIDS = frozenset(
    {
        "dashboard_export_csv",
        "dashboard_export_excel",
        "export_json",
        "export_package",
        "get_processo_decomposicao_export_csv",
        "download_processo_arquivo",
        "download_revisao_evidencia",
    }
)


def run_route_smoke(client, meta: dict[str, Any]) -> None:
    oid = meta["operationId"]
    method = meta["method"]
    path = fill_path(meta["path"])
    op = meta["op"]
    components = meta["components"]
    params = query_for_operation(oid)
    body = body_for_operation(oid, op, components)

    kwargs: dict[str, Any] = {}
    if params:
        kwargs["params"] = params

    if is_multipart(op) or oid in {
        "attach_revisao_evidencia",
        "attach_processo_arquivo",
        "import_package_preview",
        "import_package_apply",
    }:
        if oid.startswith("import_package"):
            kwargs["files"] = {
                "file": ("smoke.tmbackup.zip", b"PK\x03\x04smoke", "application/zip"),
            }
            kwargs["data"] = {"mode": "merge", "import_format": "auto"}
        else:
            kwargs["data"] = {
                "tipo": "link",
                "url_externa": "https://example.com/smoke",
                "descricao": "smoke",
            }
        response = getattr(client, method.lower())(path, **kwargs)
    elif body is not None and method in {"POST", "PUT", "PATCH"}:
        kwargs["json"] = body
        response = getattr(client, method.lower())(path, **kwargs)
    elif method == "DELETE" and body is not None:
        kwargs["json"] = body
        response = client.request("DELETE", path, **kwargs)
    else:
        response = getattr(client, method.lower())(path, **kwargs)

    assert response.status_code < 500, (oid, response.status_code, response.text[:800])

    if oid in _PLAIN_HEALTH_OIDS:
        assert response.status_code == 200, (oid, response.text[:500])
        assert_plain_health(body_json(response))
        return

    if oid in _BINARY_OIDS or looks_binary_path(meta["path"]):
        assert response.status_code == 200, (oid, response.text[:500])
        assert response.content is not None
        return

    assert response.status_code in {200, 201}, (oid, response.status_code, response.text[:800])
    assert_ok_envelope(body_json(response))
