"""Transporte de submit do coletor — Host opcional e headers S2S."""

from __future__ import annotations

from collectors.linux_host.submit import (
    DEFAULT_USER_AGENT,
    SERVICE_AUTH_HEADER,
    build_ingest_request,
)


def test_build_ingest_request_without_custom_host():
    request = build_ingest_request(
        base_url="http://127.0.0.1/apps/it-portal-api",
        server_id="459fd1b8-643f-493d-9911-0ff7aaf91424",
        token="svc-token",
        body={"run_id": "run-test-0001"},
    )
    assert request.full_url.endswith(
        "/collector/v1/servers/459fd1b8-643f-493d-9911-0ff7aaf91424/observations"
    )
    headers = {k.lower(): v for k, v in request.header_items()}
    assert headers["content-type"] == "application/json"
    assert headers[SERVICE_AUTH_HEADER.lower()] == "Bearer svc-token"
    assert headers["user-agent"] == DEFAULT_USER_AGENT
    assert "host" not in headers


def test_build_ingest_request_with_optional_host_override():
    request = build_ingest_request(
        base_url="http://127.0.0.1/apps/it-portal-api",
        server_id="459fd1b8-643f-493d-9911-0ff7aaf91424",
        token="svc-token",
        body={"run_id": "run-test-0002"},
        http_host="minhadelpi.com.br",
    )
    headers = {k.lower(): v for k, v in request.header_items()}
    assert headers["host"] == "minhadelpi.com.br"
    assert headers[SERVICE_AUTH_HEADER.lower()] == "Bearer svc-token"


def test_submit_observation_posts_via_injected_opener(monkeypatch):
    from collectors.linux_host import submit as submit_mod

    class FakeProvider:
        def get_token(self):
            return "minted-token"

    captured: dict = {}

    class FakeResponse:
        status = 201

        def read(self):
            return b'{"success":true,"data":{"run_id":"run-http-1"}}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_open(request, timeout=30):
        captured["url"] = request.full_url
        captured["headers"] = {k.lower(): v for k, v in request.header_items()}
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        submit_mod,
        "ClientCredentialsTokenProvider",
        type("P", (), {"from_env": staticmethod(lambda env: FakeProvider())}),
    )
    monkeypatch.setattr(
        submit_mod,
        "build_observation_payload",
        lambda: {"run_id": "run-http-1", "source": "linux_host_collector"},
    )

    result = submit_mod.submit_observation(
        environ={
            "IT_PORTAL_COLLECTOR_BASE_URL": "http://127.0.0.1/apps/it-portal-api",
            "IT_PORTAL_COLLECTOR_SERVER_ID": "459fd1b8-643f-493d-9911-0ff7aaf91424",
            "S2S_TOKEN_URL": "https://example/token",
            "S2S_CLIENT_ID": "it-portal-host-collector",
            "S2S_CLIENT_SECRET": "secret",
        },
        http_open=fake_open,
    )
    assert result["http_status"] == 201
    assert captured["url"].startswith("http://127.0.0.1/apps/it-portal-api/collector/v1/")
    assert captured["headers"][SERVICE_AUTH_HEADER.lower()] == "Bearer minted-token"
    assert "host" not in captured["headers"]
