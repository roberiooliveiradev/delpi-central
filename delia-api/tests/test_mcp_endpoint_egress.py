"""Connection-time MCP endpoint egress negatives (DÉLIA transport)."""

from __future__ import annotations

import pytest

from app.application.specialist_interop.errors import SpecialistInteropError
from app.infrastructure.interoperability.mcp.endpoint_egress import (
    MCP_ENDPOINT_EGRESS_DENIED,
    assert_endpoint_allowed_for_connect,
)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/mcp",
        "http://[::1]/mcp",
        "http://localhost/mcp",
        "http://169.254.169.254/latest",
        "https://user:pass@example.com/mcp",
        "http://evil.example/mcp",
    ],
)
def test_connect_time_blocks_disallowed(url):
    with pytest.raises(SpecialistInteropError) as exc:
        assert_endpoint_allowed_for_connect(url)
    assert exc.value.code == MCP_ENDPOINT_EGRESS_DENIED


def test_trusted_internal_allowed():
    assert_endpoint_allowed_for_connect("http://transformometro-api:8000/mcp")
