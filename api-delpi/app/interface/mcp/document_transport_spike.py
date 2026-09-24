"""Isolated DAVI document-transport provider spike (default OFF).

Synthetic PDF probe for proving ChatGPT model visibility of application/pdf
via remote MCP. Not a production document capability.

Hidden probe values MUST exist only inside the PDF body (and dedicated tests
that assert those values). They must not appear in URI, name, title,
description, tool metadata, or structuredContent returned to the provider.
"""

from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING

from mcp.types import (
    BlobResourceContents,
    CallToolResult,
    EmbeddedResource,
    ResourceLink,
)

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Public spike surface identifiers — no hidden PDF secrets here.
SPIKE_PDF_RESOURCE_URI = "davi-spike://document-probe"
SPIKE_TEXT_RESOURCE_URI = "davi-spike://text-probe"
SPIKE_TOOL_NAME = "spike_document_transport_probe"
SPIKE_PDF_RESOURCE_NAME = "document-probe"
SPIKE_TEXT_RESOURCE_NAME = "text-probe"
SPIKE_PDF_MIME = "application/pdf"
SPIKE_TEXT_MIME = "text/plain"

# Modes for the experimental tool (Phase B/C).
SPIKE_MODE_RESOURCE_LINK = "resource_link"
SPIKE_MODE_EMBEDDED = "embedded"

# Control text resource (different secrets from PDF — for TEXT vs PDF visibility).
_TEXT_PROBE_BODY = (
    "DOCUMENT TRANSPORT TEXT CONTROL\n"
    "CODE: TEXT-PROBE-ALPHA\n"
    "SHAPE: CIRCLE\n"
    "REVISION: V02\n"
)


def document_transport_spike_enabled() -> bool:
    from app.config import settings

    return bool(getattr(settings, "DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED", False))


def document_transport_spike_mode() -> str:
    from app.config import settings

    mode = str(getattr(settings, "DAVI_DOCUMENT_TRANSPORT_SPIKE_MODE", "") or "").strip().lower()
    if mode in {SPIKE_MODE_RESOURCE_LINK, SPIKE_MODE_EMBEDDED}:
        return mode
    return SPIKE_MODE_RESOURCE_LINK


class DocumentTransportSpikeMisconfigError(RuntimeError):
    """Spike enabled without an isolated non-production MCP resource binding."""


def assert_spike_environment_isolated() -> None:
    """Fail closed: never bind the experimental spike to the production MCP resource.

    Homolog (or any isolated nonprod) must set ``MCP_RESOURCE_URL`` to the exact
    non-production MCP resource. Missing or production values refuse registration.
    """
    import os

    from app.interface.mcp.oauth_contract import (
        CANONICAL_MCP_RESOURCE_URL,
        resolve_required_mcp_resource_audience,
    )

    explicit = (os.getenv("MCP_RESOURCE_URL") or "").strip()
    if not explicit:
        raise DocumentTransportSpikeMisconfigError(
            "DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED requires MCP_RESOURCE_URL "
            "set to an exact non-production MCP resource "
            f"(must not be {CANONICAL_MCP_RESOURCE_URL})"
        )
    if explicit.rstrip("/") == CANONICAL_MCP_RESOURCE_URL.rstrip("/"):
        raise DocumentTransportSpikeMisconfigError(
            "DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED refuses production MCP_RESOURCE_URL "
            f"({CANONICAL_MCP_RESOURCE_URL}); use an isolated homolog resource"
        )
    resolved = resolve_required_mcp_resource_audience().rstrip("/")
    if resolved == CANONICAL_MCP_RESOURCE_URL.rstrip("/"):
        raise DocumentTransportSpikeMisconfigError(
            "Document transport spike resolved MCP audience to production; "
            "set MCP_RESOURCE_URL (and PUBLIC_BASE_URL) to the homolog resource"
        )
    public_base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if public_base == "https://minhadelpi.com.br":
        raise DocumentTransportSpikeMisconfigError(
            "DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED refuses PUBLIC_BASE_URL="
            "https://minhadelpi.com.br; use a non-production homolog base URL"
        )


def build_probe_pdf_bytes() -> bytes:
    """Minimal valid-enough PDF with hidden text + triangle path.

    Content streams embed the secret probe strings. Do not put those strings
    in resource/tool metadata.
    """
    # Secrets live only in the content stream below.
    stream = (
        "BT /F1 14 Tf 40 160 Td (DOCUMENT TRANSPORT PROBE) Tj "
        "0 -20 Td (CODE: DAVI-PDF-7429) Tj "
        "0 -20 Td (SHAPE: TRIANGLE) Tj "
        "0 -20 Td (REVISION: R03) Tj ET "
        "100 40 m 160 120 l 40 120 l h S"
    )
    stream_bytes = stream.encode("latin-1")
    objects = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n",
        (
            b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] "
            b"/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
        ),
        (
            f"4 0 obj<< /Length {len(stream_bytes)} >>stream\n".encode("ascii")
            + stream_bytes
            + b"\nendstream\nendobj\n"
        ),
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n",
    ]
    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = b"".join(objects)
    offsets = [0]
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        cursor += len(obj)
    xref_start = cursor
    xref_lines = [b"xref\n0 6\n", b"0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref_lines.append(f"{off:010d} 00000 n \n".encode("ascii"))
    trailer = (
        b"trailer<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        + f"{xref_start}\n".encode("ascii")
        + b"%%EOF\n"
    )
    return header + body + b"".join(xref_lines) + trailer


def register_document_transport_spike(mcp: "FastMCP") -> None:
    """Register experimental resource(s) + optional probe tool. Caller gates with flag."""

    @mcp.resource(
        SPIKE_PDF_RESOURCE_URI,
        name=SPIKE_PDF_RESOURCE_NAME,
        title="Document transport probe",
        description="Synthetic PDF for MCP document transport experiments.",
        mime_type=SPIKE_PDF_MIME,
    )
    def document_probe_pdf() -> bytes:
        pdf = build_probe_pdf_bytes()
        logger.info(
            "davi document transport spike pdf resource read mime=%s bytes=%s",
            SPIKE_PDF_MIME,
            len(pdf),
        )
        return pdf

    @mcp.resource(
        SPIKE_TEXT_RESOURCE_URI,
        name=SPIKE_TEXT_RESOURCE_NAME,
        title="Document transport text control",
        description="Synthetic text control for MCP document transport experiments.",
        mime_type=SPIKE_TEXT_MIME,
    )
    def document_probe_text() -> str:
        logger.info(
            "davi document transport spike text resource read mime=%s bytes=%s",
            SPIKE_TEXT_MIME,
            len(_TEXT_PROBE_BODY.encode("utf-8")),
        )
        return _TEXT_PROBE_BODY

    @mcp.tool(
        name=SPIKE_TOOL_NAME,
        title="Spike document transport probe",
        description=(
            "Experimental document-transport probe. Returns a typed MCP document "
            "reference only; not a production DAVI tool."
        ),
    )
    def spike_document_transport_probe() -> CallToolResult:
        mode = document_transport_spike_mode()
        logger.info(
            "davi document transport spike tool invoked mode=%s",
            mode,
        )
        if mode == SPIKE_MODE_EMBEDDED:
            pdf = build_probe_pdf_bytes()
            blob = base64.standard_b64encode(pdf).decode("ascii")
            return CallToolResult(
                content=[
                    EmbeddedResource(
                        type="resource",
                        resource=BlobResourceContents(
                            uri=SPIKE_PDF_RESOURCE_URI,
                            mimeType=SPIKE_PDF_MIME,
                            blob=blob,
                        ),
                    )
                ],
                isError=False,
            )
        return CallToolResult(
            content=[
                ResourceLink(
                    type="resource_link",
                    uri=SPIKE_PDF_RESOURCE_URI,
                    name=SPIKE_PDF_RESOURCE_NAME,
                    mimeType=SPIKE_PDF_MIME,
                )
            ],
            isError=False,
        )
