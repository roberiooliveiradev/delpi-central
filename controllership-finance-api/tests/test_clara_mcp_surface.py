"""CLARA MCP — superfície e contrato (não-PG).

CLARA-MCP-SEMANTIC-001 (doc 119): superfície pública = seis tools
semânticas estáveis (get_context/read/analyze/knowledge/execute/
delete). Os 43 nomes legados permanecem em LEGACY_TOOL_CLASS como
janela de compatibilidade (handlers vivos no dispatcher) — não são
registrados no tools/list.

Cobre: registro das 6 tools com classes DISCOVERY/READ/ANALYSIS/ACT,
anotações honestas (readOnly/destructive), securitySchemes no wire,
instructions, mount paths e o guard de transporte (service tokens
proibidos na superfície de dados).
"""

from __future__ import annotations

import asyncio

import pytest

from controllership_finance_app.interface.mcp.asgi import (
    _MCP_EXACT_PATHS,
    normalize_mcp_mount_path,
)
from controllership_finance_app.interface.mcp.branding import (
    CLARA_MCP_INSTRUCTIONS,
)
from controllership_finance_app.interface.mcp.constants import (
    CLARA_LEGACY_TOOL_NAMES,
    LEGACY_TOOL_CLASS,
    MCP_PREDEFINED_CLIENT_ID,
    MCP_TOOL_NAMES,
    SEMANTIC_TOOL_CLASS,
    TOOL_CLASS,
)
from controllership_finance_app.interface.mcp.server import (
    clara_mcp_server,
)
from controllership_finance_app.interface.mcp import tool_bridge


def _list_tools():
    return asyncio.new_event_loop().run_until_complete(
        clara_mcp_server.list_tools()
    )


def test_oauth_client_id_contract():
    # Decisão PO 2026-10-26: client Keycloak definitivo é
    # mcp-controllership-finance (mcp-clara = histórico). O transporte
    # autentica por aud=resource URL + scope mcp:tools — o client_id é
    # apenas identidade de cadastro, nunca substituto de audience.
    assert MCP_PREDEFINED_CLIENT_ID == "mcp-controllership-finance"


def test_tool_names_and_classes():
    tools = _list_tools()
    names = {t.name for t in tools}
    assert names == set(MCP_TOOL_NAMES)
    assert len(tools) == 6
    for t in tools:
        assert (t.meta or {}).get("delpi/toolClass") == TOOL_CLASS[t.name]


def test_semantic_surface_contract():
    """Doc 119: exatamente seis tools semânticas estáveis."""
    assert set(SEMANTIC_TOOL_CLASS) == {
        "get_context",
        "read",
        "analyze",
        "knowledge",
        "execute",
        "delete",
    }
    assert MCP_TOOL_NAMES == (
        "get_context",
        "read",
        "analyze",
        "knowledge",
        "execute",
        "delete",
    )


def test_legacy_names_kept_for_compat_window():
    """Doc 119: legado não é removido sem migração comprovada —
    os nomes/handlers seguem documentados e despacháveis, mas fora
    do tools/list público."""
    assert len(CLARA_LEGACY_TOOL_NAMES) == 43
    for name in CLARA_LEGACY_TOOL_NAMES:
        assert name not in MCP_TOOL_NAMES
        assert name in TOOL_CLASS
        assert callable(getattr(tool_bridge, f"tool_{name}"))


def test_tool_taxonomy():
    assert TOOL_CLASS["get_context"] == "DISCOVERY"
    assert TOOL_CLASS["read"] == "READ"
    assert TOOL_CLASS["analyze"] == "ANALYSIS"
    assert TOOL_CLASS["knowledge"] == "READ"
    assert TOOL_CLASS["execute"] == "ACT"
    assert TOOL_CLASS["delete"] == "ACT"
    # Taxonomia legada preservada na janela de compatibilidade.
    assert LEGACY_TOOL_CLASS["get_catalog"] == "DISCOVERY"
    assert LEGACY_TOOL_CLASS["prepare_governed_operation"] == "PREPARE"
    assert LEGACY_TOOL_CLASS["commit_proposal"] == "ACT"
    for name in (
        "get_my_context",
        "get_competence_state",
        "get_checklist_items",
        "list_documents",
        "get_p3_reconciliation",
        "list_pendencies",
        "get_package_review",
        "search_closing_knowledge",
        "get_knowledge_item",
        # paridade READ Portal × CLARA (execução 016)
        "list_competences",
        "get_competence",
        "get_checklist_item",
        "get_closing_cockpit",
        "list_my_tasks",
        "get_pendency",
        "list_p3_events",
        "get_package",
        "get_document",
        "get_item_validation",
        "lookup_participants",
        "get_financial_settlements",
        "get_financial_settlements_summary",
        "get_stock_inventory",
        "get_stock_movements",
        "get_work_in_process",
        "get_stock_reconciliation",
        "get_report_matrix",
        "list_closing_catalogs",
        "list_catalog_entries",
        "list_checklist_templates",
        "get_checklist_template_version",
        "list_received_deliveries",
        "get_received_delivery",
        "get_received_document",
    ):
        assert TOOL_CLASS[name] == "READ", name
    assert TOOL_CLASS["analyze_closing_blockers"] == "ANALYSIS"
    assert TOOL_CLASS["prepare_governed_operation"] == "PREPARE"
    assert TOOL_CLASS["commit_proposal"] == "ACT"
    assert TOOL_CLASS["get_batch_status"] == "READ"
    assert TOOL_CLASS["prepare_batch"] == "PREPARE"
    assert TOOL_CLASS["confirm_batch"] == "PREPARE"
    assert TOOL_CLASS["execute_batch"] == "ACT"


def test_annotations_readonly_and_destructive():
    tools = {t.name: t for t in _list_tools()}
    for name in MCP_TOOL_NAMES:
        cls = SEMANTIC_TOOL_CLASS[name]
        ann = tools[name].annotations
        expected_readonly = cls in {"DISCOVERY", "READ", "ANALYSIS"}
        assert bool(ann.read_only_hint) == expected_readonly, name
    assert bool(
        tools["execute"].annotations.destructive_hint
    ) is True
    assert bool(
        tools["delete"].annotations.destructive_hint
    ) is True
    assert bool(
        tools["read"].annotations.destructive_hint
    ) in (False, None)


def test_security_schemes_on_wire():
    for t in _list_tools():
        schemes = getattr(t, "securitySchemes", None) or (
            t.meta or {}
        ).get("securitySchemes")
        assert schemes, f"{t.name} sem securitySchemes"
        assert schemes[0]["type"] == "oauth2"


def test_instructions_honesty_invariants():
    assert "never zero" in CLARA_MCP_INSTRUCTIONS
    assert "confirmation_url" in CLARA_MCP_INSTRUCTIONS
    assert "NOT consent" in CLARA_MCP_INSTRUCTIONS
    assert "plan_hash" in CLARA_MCP_INSTRUCTIONS
    assert "untrusted data" in CLARA_MCP_INSTRUCTIONS
    assert "phase='prepare'" in CLARA_MCP_INSTRUCTIONS
    assert "get_context" in CLARA_MCP_INSTRUCTIONS


def test_mount_path_normalization():
    assert normalize_mcp_mount_path("/mcp") == "/mcp/"
    assert normalize_mcp_mount_path(
        "/apps/controllership-finance-api/mcp"
    ) == "/apps/controllership-finance-api/mcp/"
    assert normalize_mcp_mount_path("/mcp/") == "/mcp/"
    assert normalize_mcp_mount_path("/health") == "/health"
    assert "/mcp" in _MCP_EXACT_PATHS


def test_mcp_data_path_requires_root_stripped():
    from delpi_mcp.auth import is_mcp_data_path
    from controllership_finance_app.middleware.auth_middleware import (
        _strip_root_path,
    )

    class _Req:
        def __init__(self, path, root_path):
            self.url = type("U", (), {"path": path})()
            self.scope = {"root_path": root_path}

    req = _Req(
        "/apps/controllership-finance-api/mcp",
        "/apps/controllership-finance-api",
    )
    assert _strip_root_path(req) == "/mcp"
    assert is_mcp_data_path(_strip_root_path(req)) is True
    req2 = _Req("/closing/competences", "")
    assert is_mcp_data_path(_strip_root_path(req2)) is False


def test_tool_error_mapping_typed():
    from controllership_finance_app.domain.closing_checklist.errors import (
        ChecklistDomainError,
    )

    class _Custom(ChecklistDomainError):
        code = "terminal_rejection_active"
        status = 409

    result = tool_bridge.handle_tool_error(
        _Custom("Rejeição terminal ativa.")
    )
    assert result.is_error is True
    import json

    payload = json.loads(result.content[0].text)
    assert payload["success"] is False
    assert payload["data"]["error"]["code"] == (
        "terminal_rejection_active"
    )
    assert payload["status_code"] == 409


def test_unauthenticated_maps_401_with_challenge():
    result = tool_bridge.handle_tool_error(
        PermissionError("Unauthorized")
    )
    assert result.is_error is True
    import json

    payload = json.loads(result.content[0].text)
    assert payload["status_code"] == 401
    meta = getattr(result, "meta", None) or {}
    assert "mcp/www_authenticate" in str(meta)


def test_internal_error_never_leaks():
    result = tool_bridge.handle_tool_error(
        RuntimeError("db connection trace secret")
    )
    import json

    payload = json.loads(result.content[0].text)
    assert payload["status_code"] == 500
    assert "secret" not in result.content[0].text
    assert "Erro interno" in payload["message"]


def test_public_path_gate_well_known():
    from controllership_finance_app.middleware.auth_middleware import (
        _is_controllership_finance_public_path,
    )

    assert _is_controllership_finance_public_path(
        "/.well-known/oauth-protected-resource"
    )
    assert _is_controllership_finance_public_path(
        "/apps/controllership-finance-api/"
        ".well-known/oauth-protected-resource"
    )
    assert not _is_controllership_finance_public_path("/mcp")
    assert not _is_controllership_finance_public_path(
        "/closing/competences"
    )


def test_manifest_covers_only_existing_docs():
    from pathlib import Path

    from controllership_finance_app.application.clara.corpus_manifest import (  # noqa: E501
        AUTHORIZED_SOURCES,
    )
    repo_root = Path(__file__).resolve().parents[2]
    missing = [
        s.path for s in AUTHORIZED_SOURCES
        if not (repo_root / s.path).is_file()
    ]
    assert not missing, f"Fontes declaradas ausentes: {missing}"
    ids = [s.source_id for s in AUTHORIZED_SOURCES]
    assert len(ids) == len(set(ids))


def test_segmenter_splits_oversized_section():
    from controllership_finance_app.application.clara.corpus_ingestion import (  # noqa: E501
        segment_markdown,
    )

    text = "# Doc\n\n## Big\n\n" + ("linha de conteúdo\n" * 600)
    segs = segment_markdown(text, max_chars=1000)
    big = [s for s in segs if s.heading_path.startswith("Doc > Big")]
    assert len(big) > 1
    assert all("#part-" in s.heading_path or i == 0
               for i, s in enumerate(big))
