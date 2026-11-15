"""Static, no-network regression checks for strict Linux Ops MCP publication."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROD = ROOT / "gateway/nginx.conf"
DEV = ROOT / "gateway/nginx.dev.conf"
SNIPPET = ROOT / "gateway/snippets/linux-ops-mcp-locations.conf"


def test_gateway_configs_include_shared_route_once():
    line = "include /etc/nginx/snippets/linux-ops-mcp-locations.conf;"
    for path in (PROD, DEV):
        text = path.read_text()
        assert text.count(line) == 1, path


def test_only_mcp_and_protected_metadata_are_forwarded():
    text = SNIPPET.read_text()
    assert "location ~ ^/apps/linux-ops-mcp/mcp/?$ {" in text
    assert "location = /apps/linux-ops-mcp/.well-known/oauth-protected-resource {" in text
    assert "location /apps/linux-ops-mcp/ {" in text
    assert "return 404;" in text
    assert text.count("proxy_pass http://$upstream_linux_ops_mcp;") == 2
    assert "rewrite ^/apps/linux-ops-mcp/(.*)$ /$1 break;" in text
    assert "proxy_set_header Authorization $http_authorization;" in text
    assert "proxy_buffering off;" in text
    assert "proxy_request_buffering off;" in text
    assert "proxy_pass http://127.0.0.1:18765" not in text
    assert "proxy_pass http://$upstream_linux_ops_mcp" in text
    assert "proxy_pass http://linux-ops-mcp:8000;" not in text
    assert "docker.sock" not in text.lower()
    assert "healthz {" not in text


def test_existing_mcp_paths_are_not_replaced():
    for path in (PROD, DEV):
        text = path.read_text()
        assert "location ^~ /apps/supplies-api/mcp" in text
        assert "include /etc/nginx/snippets/linux-ops-mcp-locations.conf;" in text
