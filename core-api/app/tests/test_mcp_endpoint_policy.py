"""R1-RW03: MCP endpoint registration policy negatives."""

from __future__ import annotations

import pytest

from app.domain.mcp_providers.endpoint_policy import validate_mcp_endpoint_ref
from app.domain.mcp_providers.lifecycle import McpProviderLifecycleError


@pytest.mark.parametrize(
    "url,code",
    [
        ("http://127.0.0.1/mcp", "mcp_provider.endpoint_ssrf"),
        ("http://[::1]/mcp", "mcp_provider.endpoint_ssrf"),
        ("http://localhost/mcp", "mcp_provider.endpoint_ssrf"),
        ("http://169.254.169.254/latest", "mcp_provider.endpoint_ssrf"),
        ("https://user:pass@example.com/mcp", "mcp_provider.endpoint_credentials"),
        ("ftp://example.com/mcp", "mcp_provider.endpoint_scheme"),
        ("http://evil.example/mcp", "mcp_provider.endpoint_https_required"),
    ],
)
def test_blocked_endpoints(url, code):
    with pytest.raises(McpProviderLifecycleError) as exc:
        validate_mcp_endpoint_ref(url, resolve_dns=False)
    assert exc.value.code == code


def test_trusted_delpi_internal_allowed():
    assert (
        validate_mcp_endpoint_ref(
            "http://transformometro-api:8000/mcp", resolve_dns=False
        )
        == "http://transformometro-api:8000/mcp"
    )


def test_external_https_without_dns_ok_structurally():
    assert validate_mcp_endpoint_ref(
        "https://partner.example/mcp", resolve_dns=False
    ).startswith("https://")
