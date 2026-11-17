"""Hermetic negative and positive coverage for the HML Docker upstream guard.

Only httpx.MockTransport and synthetic Docker inspect metadata are used.
No real Docker daemon, privileged process, network or persistent socket.
"""
from __future__ import annotations

import asyncio

import httpx
import pytest

from linux_ops_mcp.atlas_hml_engine_boundary import (
    HMLDockerGETTransport,
    HMLDockerInspectOnly,
    HML_TARGET,
    _HML_URL,
)
from linux_ops_mcp.deploy_host_source import HostSourceError, RuntimeTarget

CID = "a" * 64
IMAGE = "sha256:" + "b" * 64


def docker_json(*, project="delpi-hml", with_secret=False):
    return {
        "Id": CID,
        "Image": IMAGE,
        "Name": "/delpi-hml-public-hub",
        "Config": {
            "Labels": {
                "com.docker.compose.service": "public-hub",
                "com.docker.compose.project": project,
            },
            **({"Env": ["PRIVATE_TOKEN=synthetic_never_return"]} if with_secret else {}),
        },
        "State": {"Running": True, "Health": {"Status": "healthy"}},
    }


def test_exact_hml_inspect_succeeds_without_secrets():
    observed = []

    def responder(request):
        observed.append((request.method, str(request.url)))
        return httpx.Response(200, json=docker_json(with_secret=True))

    async def run():
        reader = HMLDockerInspectOnly(upstream=httpx.MockTransport(responder))
        return await reader.inspect(HML_TARGET)

    result = asyncio.run(run())
    assert result.container_id == CID
    assert result.image_id == IMAGE
    assert result.running and result.healthy
    assert "synthetic_never_return" not in repr(result)
    assert observed == [("GET", _HML_URL)]


@pytest.mark.parametrize("method,url,headers,content", [
    ("POST", _HML_URL, {}, b""),
    ("DELETE", _HML_URL, {}, b""),
    ("HEAD", _HML_URL, {}, b""),
    ("GET", "http://docker.local/containers/json", {}, b""),
    ("GET", "http://docker.local/containers/delpi-public-hub/json", {}, b""),
    ("GET", _HML_URL+"?all=1", {}, b""),
    ("GET", "http://docker.local:2375/containers/delpi-hml-public-hub/json", {}, b""),
    ("GET", "https://docker.local/containers/delpi-hml-public-hub/json", {}, b""),
    ("GET", _HML_URL, {"Authorization":"Bearer synthetic"}, b""),
    ("GET", _HML_URL, {"X-Docker-Container-Path":"other"}, b""),
    ("GET", _HML_URL, {}, b"body"),
])
def test_guard_denies_other_methods_paths_origins_headers_and_body(
    method, url, headers, content,
):
    calls = []

    def responder(request):
        calls.append(request)
        return httpx.Response(200, json=docker_json())

    async def run():
        async with httpx.AsyncClient(
            transport=HMLDockerGETTransport(httpx.MockTransport(responder)),
            follow_redirects=False,
            trust_env=False, timeout=3.0,
        ) as client:
            return await client.request(method, url, headers=headers, content=content)

    with pytest.raises(HostSourceError, match="HML_ENGINE_REQUEST_DENIED"):
        asyncio.run(run())
    assert calls == []


@pytest.mark.parametrize("target", [
    RuntimeTarget("prod","public-hub","srv-api-pilot","delpi-hml","delpi-hml-public-hub"),
    RuntimeTarget("hml","public-hub","srv-api-pilot","delpi-hml","delpi-public-hub"),
    RuntimeTarget("hml","public-hub","srv-api-pilot","delpi-prod","delpi-hml-public-hub"),
])
def test_typed_inspector_rejects_wrong_targets_before_upstream(target):
    calls=[]

    def responder(request):
        calls.append(request)
        return httpx.Response(200,json=docker_json())

    async def run():
        return await HMLDockerInspectOnly(
            upstream=httpx.MockTransport(responder),
        ).inspect(target)

    with pytest.raises(HostSourceError, match="HML_ENGINE_TARGET_DENIED"):
        asyncio.run(run())
    assert calls == []


def test_wrong_compose_labels_remain_rejected():
    async def run():
        return await HMLDockerInspectOnly(
            upstream=httpx.MockTransport(
                lambda _: httpx.Response(200,json=docker_json(project="prod")),
            ),
        ).inspect(HML_TARGET)
    with pytest.raises(HostSourceError, match="INSPECT_TARGET_MISMATCH"):
        asyncio.run(run())


@pytest.mark.parametrize("response", [
    lambda: httpx.Response(302,headers={"Location":"http://docker.local/containers/json"}),
    lambda: httpx.Response(101),
    lambda: httpx.Response(200,headers={"Content-Encoding":"gzip"},content=b"compressed"),
    lambda: httpx.Response(200,headers={"Content-Length":"999999999"},content=b"{}"),
])
def test_redirect_upgrade_compression_and_oversized_declared_size_fail_closed(response):
    async def run():
        async with httpx.AsyncClient(
            transport=HMLDockerGETTransport(httpx.MockTransport(lambda _: response())),
            trust_env=False, follow_redirects=False, timeout=3.0,
        ) as client:
            return await client.get(_HML_URL)
    with pytest.raises((HostSourceError, httpx.HTTPError)):
        asyncio.run(run())


def test_oversized_actual_response_never_reaches_runtime_payload():
    async def run():
        reader=HMLDockerInspectOnly(upstream=httpx.MockTransport(
            lambda _: httpx.Response(200,content=b"x"*262145),
        ))
        return await reader.inspect(HML_TARGET)
    with pytest.raises(HostSourceError, match="INSPECT_TOO_LARGE"):
        asyncio.run(run())


def test_transport_constructor_refuses_missing_or_wrong_backend():
    for bad in (None, object(), "unix:///var/run/docker.sock"):
        with pytest.raises(HostSourceError, match="HML_ENGINE_TRANSPORT_UNAVAILABLE"):
            HMLDockerGETTransport(bad)


def test_module_has_no_live_entrypoint():
    from linux_ops_mcp import atlas_hml_engine_boundary as guard
    assert not hasattr(guard,"main")
    assert not hasattr(guard,"create_mcp_server")
    assert not hasattr(guard,"run_server")
