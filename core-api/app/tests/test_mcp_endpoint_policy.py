"""R1-RW03: MCP endpoint registration policy negatives (pure domain)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.domain.mcp_providers.endpoint_policy import evaluate_mcp_endpoint_ref
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
        evaluate_mcp_endpoint_ref(url, resolved_ips=None)
    assert exc.value.code == code


def test_trusted_delpi_internal_allowed():
    assert (
        evaluate_mcp_endpoint_ref(
            "http://transformometro-api:8000/mcp", resolved_ips=None
        )
        == "http://transformometro-api:8000/mcp"
    )


def test_external_https_without_dns_ok_structurally():
    assert evaluate_mcp_endpoint_ref(
        "https://partner.example/mcp", resolved_ips=None
    ).startswith("https://")


def test_dns_resolution_to_private_blocked():
    with pytest.raises(McpProviderLifecycleError) as exc:
        evaluate_mcp_endpoint_ref(
            "https://partner.example/mcp",
            resolved_ips=["10.0.0.5"],
        )
    assert exc.value.code == "mcp_provider.endpoint_ssrf"


def test_domain_endpoint_policy_has_no_os_or_socket_imports():
    path = (
        Path(__file__).resolve().parents[1]
        / "domain/mcp_providers/endpoint_policy.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    banned: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in {"os", "socket"} or alias.name.startswith(
                    ("os.", "socket.")
                ):
                    banned.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module in {"os", "socket"}:
            banned.append(node.module)
    assert banned == [], f"Domain endpoint_policy imports I/O: {banned}"