"""Trava do nome do fechamento mensal — N4.

O código do TÉO não volta para o texto que a CLARA mostra, salvo a
linha de identificação da ficha.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from controllership_finance_app.application.clara.corpus_manifest import (
    AUTHORIZED_SOURCES,
)
from controllership_finance_app.application.clara.corpus_manifest_lnf import (
    LNF_AUTHORIZED_SOURCES,
)
from controllership_finance_app.application.clara.agent_intelligence_service import (
    CONTENT_PATH,
)
from controllership_finance_app.interface.mcp.branding import (
    CLARA_MISSION,
    build_clara_mcp_instructions,
)
from controllership_finance_app.interface.mcp.server import clara_mcp_server

TOKEN = "PROC-0072"
D3 = "Código no Transformômetro (TÉO): PROC-0072"
REPO = Path(__file__).resolve().parents[2]


def _list_tools():
    return asyncio.new_event_loop().run_until_complete(
        clara_mcp_server.list_tools()
    )


def test_corpus_sources_keep_teo_code_only_on_the_ficha():
    violations: list[str] = []
    d3_hits = 0
    for spec in (*AUTHORIZED_SOURCES, *LNF_AUTHORIZED_SOURCES):
        assert TOKEN not in spec.name, spec.source_id
        path = REPO / spec.path
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if TOKEN not in line:
                continue
            if D3 in line and spec.source_id == "ficha-processo":
                d3_hits += 1
                continue
            violations.append(f"{spec.source_id}:{path.name}:{lineno}")
    assert d3_hits == 1
    assert violations == []


def test_mcp_surface_and_intelligence_hide_teo_code():
    instructions = build_clara_mcp_instructions()
    assert TOKEN not in instructions
    assert TOKEN not in CLARA_MISSION
    assert "Nunca mostre ao usuário códigos internos" in instructions
    tools = _list_tools()
    assert {tool.name for tool in tools} == {
        "get_context",
        "read",
        "analyze",
        "knowledge",
        "execute",
        "delete",
    }
    for tool in tools:
        assert TOKEN not in (tool.description or ""), tool.name
    raw = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    blob = json.dumps(raw, ensure_ascii=False)
    assert TOKEN not in blob
    assert raw["version"] == "2026.11.14.1"


def test_negative_sibling_source_name_is_not_the_code():
    by_id = {spec.source_id: spec for spec in AUTHORIZED_SOURCES}
    assert "Ficha do Fechamento mensal da Controladoria" == by_id[
        "ficha-processo"
    ].name
    assert TOKEN not in by_id["doc-118"].name
    assert TOKEN not in by_id["doc-02"].name
