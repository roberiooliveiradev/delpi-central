"""Native BPMN Convergence — lock de escrita legada.

Todo PUT de modelagem flowchart_v1 deve responder 409 tipado
LEGACY_DIAGRAM_READ_ONLY (AuthZ primeiro), sem mutação. GETs legados
seguem funcionando (cobertura já existente nos smokes Nível A).
"""

from __future__ import annotations

import pytest

LOCKED_PUTS = (
    (
        "/transformometro/processos/p1/diagrama",
        {"conteudo": {"nodes": [], "edges": []}},
    ),
    (
        "/transformometro/processos/p1/diagrama/bpmn.xml",
        {"xml": "<definitions/>"},
    ),
    (
        "/transformometro/instancias/i1/diagrama-escopo",
        {"node_ids": ["n1"], "inherit_all": False, "include_boundary_edges": True},
    ),
    (
        "/transformometro/revisoes/r1/diagrama/overlay",
        {"conteudo": {"node_overrides": {}}},
    ),
)


@pytest.mark.parametrize("path,body", LOCKED_PUTS)
def test_legacy_diagram_put_returns_typed_read_only(tm_client, path, body):
    response = tm_client.put(path, json=body)

    assert response.status_code == 409, (path, response.status_code, response.text[:500])
    payload = response.json()
    assert payload.get("success") is False, payload
    data = payload.get("data", {})
    assert data.get("error_code") == "LEGACY_DIAGRAM_READ_ONLY", payload
    assert data.get("legacy_format") == "flowchart_v1", payload
    assert "migrate_legacy_diagram_to_native_bpmn" in str(payload), payload
