"""Local protocol proofs for DAVI document-transport provider spike (default OFF)."""

from __future__ import annotations

import asyncio
import base64
import os

import pytest

from app.interface.mcp.document_transport_spike import (
    SPIKE_MODE_EMBEDDED,
    SPIKE_MODE_RESOURCE_LINK,
    SPIKE_PDF_MIME,
    SPIKE_PDF_RESOURCE_URI,
    SPIKE_TEXT_RESOURCE_URI,
    SPIKE_TOOL_NAME,
    build_probe_pdf_bytes,
    register_document_transport_spike,
)
from app.interface.mcp.server import create_mcp_server
from mcp.server.fastmcp import FastMCP
from mcp.types import EmbeddedResource, ResourceLink

# Expected hidden values — assertions only; must not appear in MCP metadata.
_PROBE_CODE = "DAVI-PDF-7429"
_PROBE_SHAPE = "TRIANGLE"
_PROBE_REV = "R03"
_TEXT_CODE = "TEXT-PROBE-ALPHA"

# Isolated non-production resource required when spike is ON (fail-closed vs production).
_HOMOLOG_MCP_RESOURCE = "https://homolog.example.test/apps/api-delpi/mcp"
_HOMOLOG_PUBLIC_BASE = "https://homolog.example.test"


def _enable_isolated_spike(monkeypatch: pytest.MonkeyPatch, *, mode: str = SPIKE_MODE_RESOURCE_LINK) -> None:
    from app.config import settings

    monkeypatch.setenv("MCP_RESOURCE_URL", _HOMOLOG_MCP_RESOURCE)
    monkeypatch.setenv("PUBLIC_BASE_URL", _HOMOLOG_PUBLIC_BASE)
    monkeypatch.setattr(settings, "DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED", True)
    monkeypatch.setattr(settings, "DAVI_DOCUMENT_TRANSPORT_SPIKE_MODE", mode)


def _metadata_blob(mcp: FastMCP) -> str:
    resources = asyncio.run(mcp.list_resources())
    tools = asyncio.run(mcp.list_tools())
    parts: list[str] = []
    for r in resources:
        parts.extend(
            [
                str(getattr(r, "uri", "")),
                str(getattr(r, "name", "") or ""),
                str(getattr(r, "title", "") or ""),
                str(getattr(r, "description", "") or ""),
                str(getattr(r, "mimeType", "") or ""),
            ]
        )
    for t in tools:
        parts.extend(
            [
                str(getattr(t, "name", "") or ""),
                str(getattr(t, "title", "") or ""),
                str(getattr(t, "description", "") or ""),
            ]
        )
    return "\n".join(parts)


def test_probe_pdf_contains_hidden_content_and_starts_with_pdf_magic() -> None:
    pdf = build_probe_pdf_bytes()
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 100
    text = pdf.decode("latin-1")
    assert _PROBE_CODE in text
    assert _PROBE_SHAPE in text
    assert _PROBE_REV in text
    assert "DOCUMENT TRANSPORT PROBE" in text


def test_spike_disabled_by_default_keeps_three_tools_and_no_spike_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED", raising=False)
    monkeypatch.setenv("DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED", "false")
    # Force settings reload pattern used by module: patch settings attribute
    from app.config import settings

    monkeypatch.setattr(settings, "DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED", False)

    mcp = create_mcp_server()
    tools = asyncio.run(mcp.list_tools())
    names = sorted(t.name for t in tools)
    assert names == [
        "discover_delpi_information",
        "execute_delpi_information",
        "search_products",
    ]
    resources = asyncio.run(mcp.list_resources())
    uris = {str(r.uri) for r in resources}
    assert SPIKE_PDF_RESOURCE_URI not in uris
    assert SPIKE_TEXT_RESOURCE_URI not in uris
    assert SPIKE_TOOL_NAME not in names


def test_spike_enabled_registers_resources_and_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_isolated_spike(monkeypatch, mode=SPIKE_MODE_RESOURCE_LINK)

    mcp = create_mcp_server()
    tools = asyncio.run(mcp.list_tools())
    names = sorted(t.name for t in tools)
    assert SPIKE_TOOL_NAME in names
    assert len(names) == 4

    resources = asyncio.run(mcp.list_resources())
    by_uri = {str(r.uri): r for r in resources}
    assert SPIKE_PDF_RESOURCE_URI in by_uri
    assert by_uri[SPIKE_PDF_RESOURCE_URI].mimeType == SPIKE_PDF_MIME
    assert SPIKE_TEXT_RESOURCE_URI in by_uri


def test_spike_resource_read_returns_pdf_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_isolated_spike(monkeypatch)
    mcp = create_mcp_server()
    contents = asyncio.run(mcp.read_resource(SPIKE_PDF_RESOURCE_URI))
    assert len(contents) == 1
    payload = contents[0].content
    assert isinstance(payload, (bytes, memoryview))
    raw = bytes(payload)
    assert raw.startswith(b"%PDF")
    assert _PROBE_CODE.encode("latin-1") in raw


def test_metadata_does_not_leak_probe_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_isolated_spike(monkeypatch)
    mcp = create_mcp_server()
    blob = _metadata_blob(mcp)
    assert _PROBE_CODE not in blob
    assert _PROBE_SHAPE not in blob
    assert _PROBE_REV not in blob
    assert _TEXT_CODE not in blob


def test_resource_link_tool_result_has_no_secret_text(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_isolated_spike(monkeypatch, mode=SPIKE_MODE_RESOURCE_LINK)
    mcp = create_mcp_server()
    result = asyncio.run(mcp.call_tool(SPIKE_TOOL_NAME, {}))
    assert isinstance(result, object)
    content = getattr(result, "content", None) or result
    assert len(content) == 1
    link = content[0]
    assert isinstance(link, ResourceLink)
    assert str(link.uri) == SPIKE_PDF_RESOURCE_URI
    dumped = str(result)
    assert _PROBE_CODE not in dumped
    assert _PROBE_SHAPE not in dumped
    assert _PROBE_REV not in dumped
    assert getattr(result, "structuredContent", None) in (None, {})


def test_embedded_resource_tool_result_is_pdf_blob(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_isolated_spike(monkeypatch, mode=SPIKE_MODE_EMBEDDED)
    mcp = create_mcp_server()
    result = asyncio.run(mcp.call_tool(SPIKE_TOOL_NAME, {}))
    block = result.content[0]
    assert isinstance(block, EmbeddedResource)
    resource = block.resource
    assert resource.mimeType == SPIKE_PDF_MIME
    raw = base64.standard_b64decode(resource.blob)
    assert raw.startswith(b"%PDF")
    assert _PROBE_CODE.encode("latin-1") in raw
    # structuredContent must not carry the PDF
    assert result.structuredContent in (None, {})


def test_spike_refuses_missing_mcp_resource_url(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings
    from app.interface.mcp.document_transport_spike import DocumentTransportSpikeMisconfigError

    monkeypatch.delenv("MCP_RESOURCE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.setattr(settings, "DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED", True)
    with pytest.raises(DocumentTransportSpikeMisconfigError) as exc:
        create_mcp_server()
    assert "MCP_RESOURCE_URL" in str(exc.value)


def test_spike_refuses_production_mcp_resource_url(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings
    from app.interface.mcp.document_transport_spike import DocumentTransportSpikeMisconfigError
    from app.interface.mcp.oauth_contract import CANONICAL_MCP_RESOURCE_URL

    monkeypatch.setenv("MCP_RESOURCE_URL", CANONICAL_MCP_RESOURCE_URL)
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    monkeypatch.setattr(settings, "DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED", True)
    with pytest.raises(DocumentTransportSpikeMisconfigError):
        create_mcp_server()


def test_register_on_fresh_server_without_production_tools() -> None:
    mcp = FastMCP("isolated-spike")
    register_document_transport_spike(mcp)
    resources = asyncio.run(mcp.list_resources())
    assert {str(r.uri) for r in resources} == {
        SPIKE_PDF_RESOURCE_URI,
        SPIKE_TEXT_RESOURCE_URI,
    }
