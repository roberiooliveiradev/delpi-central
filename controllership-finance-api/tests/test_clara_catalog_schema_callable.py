"""CLARA F7-R — toda entrada do catálogo deve ser chamável
respeitando o inputSchema publicado em tools/list (jsonschema).

O revisor em PROD mostrou que JSON-RPC cru não pega enum incompleto;
clientes MCP reais (Claude/ChatGPT) validam o schema antes de enviar.
"""

from __future__ import annotations

import asyncio

import pytest
from jsonschema import Draft202012Validator

from controllership_finance_app.interface.mcp import semantic_bridge as sb
from controllership_finance_app.interface.mcp.server import clara_mcp_server


def _list_tools_by_name() -> dict:
    tools = asyncio.new_event_loop().run_until_complete(
        clara_mcp_server.list_tools()
    )
    return {t.name: t for t in tools}


def _schema_of(tool) -> dict:
    raw = getattr(tool, "inputSchema", None)
    if raw is None:
        raw = getattr(tool, "input_schema", None)
    if hasattr(raw, "model_dump"):
        return raw.model_dump(by_alias=True, exclude_none=True)
    if isinstance(raw, dict):
        return raw
    return dict(raw or {})


def _full_identity() -> dict:
    return {
        "is_manage": True,
        "is_dre": True,
        "lnf_read": True,
        "lnf_create": True,
        "lnf_write": True,
        "lnf_process": True,
        "lnf_manage": True,
        "lnf_review_unmapped": True,
    }


def _placeholder(name: str):
    if name in {"period"}:
        return "2026-09"
    if name in {"page", "page_size", "limit"}:
        return 1
    if name in {"amount"}:
        return 1.0
    if name.endswith("_id") or name in {"request_id", "knowledge_id"}:
        return "11111111-1111-4111-8111-111111111111"
    if name in {"subjects"}:
        return [
            {
                "reportId": "stock",
                "period": "2026-09",
                "branch": "01",
            }
        ]
    if name in {"filters", "params", "parameters", "batch"}:
        return {}
    return "x"


def _call_for_catalog_entry(entry: dict) -> tuple[str, dict]:
    tool = entry["tool"]
    entity = entry["entity"]
    action = entry["action"]
    required = list(entry.get("required_params") or [])

    if tool == "analyze":
        analysis_type = entry.get("analysis_type") or action
        payload = {"analysis_type": analysis_type}
        for key in required:
            if key == "period":
                payload["period"] = _placeholder("period")
            else:
                payload.setdefault("filters", {})
                payload["filters"][key] = _placeholder(key)
        # optional LNF filters exercise branch/period shape
        if analysis_type == "invoice_posting_backlog":
            payload.setdefault("filters", {})
            payload["filters"].setdefault("branch", "01")
            payload.setdefault("period", "2026-11")
        return tool, payload

    if tool == "read":
        payload = {"entity": entity, "action": action}
        for key in required:
            if key in {"ref", "period"}:
                payload[key] = _placeholder(key)
            else:
                payload.setdefault("filters", {})
                payload["filters"][key] = _placeholder(key)
        return tool, payload

    if tool == "knowledge":
        payload = {"action": action}
        for key in required:
            payload[key] = _placeholder(key)
        return tool, payload

    # execute / delete (governed)
    payload = {
        "entity": entity,
        "action": action,
        "params": {k: _placeholder(k) for k in required},
        "phase": "prepare",
    }
    return tool, payload


def test_analyze_enum_includes_invoice_posting_backlog():
    tools = _list_tools_by_name()
    schema = _schema_of(tools["analyze"])
    enum = schema["properties"]["analysis_type"]["enum"]
    assert "invoice_posting_backlog" in enum
    assert "invoice_posting.backlog" not in enum
    assert set(enum) == set(sb.analysis_types())


def test_every_catalog_entry_validates_against_tools_list_schema():
    tools = _list_tools_by_name()
    catalog = sb._semantic_catalog(_full_identity())
    buckets = (
        catalog["actions"]["read"]
        + catalog["actions"]["analyze"]
        + catalog["actions"]["knowledge"]
        + catalog["actions"]["governed"]
    )
    assert buckets, "catálogo vazio inesperado"
    failures: list[str] = []
    for entry in buckets:
        tool_name, payload = _call_for_catalog_entry(entry)
        tool = tools.get(tool_name)
        if tool is None:
            failures.append(f"{entry}: tool {tool_name} ausente em tools/list")
            continue
        schema = _schema_of(tool)
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
        if errors:
            failures.append(
                f"{tool_name} {entry.get('entity')}/{entry.get('action')}: "
                + "; ".join(e.message for e in errors)
            )
    assert failures == []


def test_schema_topic_resolves_lnf_analyze():
    schema = sb._schema_for("invoice_posting", "invoice_posting_backlog")
    assert schema is not None
    assert schema["tool"] == "analyze"
    assert schema["analysis_type"] == "invoice_posting_backlog"
    alias = sb._schema_for("invoice_posting", "invoice_posting.backlog")
    assert alias["analysis_type"] == "invoice_posting_backlog"
