"""One-shot HML tests. Writes are confined to pytest tmp_path fixtures.

A Docker Engine is never accessed by these tests; only httpx.MockTransport.
No privilege changes, service installs, Docker requests, Keycloak or MCP tools.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone

import httpx
import pytest

from linux_ops_mcp import atlas_hml_one_shot_candidate as one_shot
from linux_ops_mcp import atlas_hml_snapshot_file_reader as reader

ID = "a" * 64
IMAGE = "sha256:" + "b" * 64


@pytest.fixture
def directory(tmp_path):
    root = tmp_path / "candidate-hml"
    root.mkdir()
    os.chmod(root, 0o750)
    return root


def docker_payload(*, name="/delpi-hml-public-hub",
                   project="delpi-hml", running=True, healthy="healthy"):
    return {
        "Id": ID,
        "Image": IMAGE,
        "Name": name,
        "Config": {
            "Labels": {
                "com.docker.compose.project": project,
                "com.docker.compose.service": "public-hub",
            },
            "Env": ["SYNTHETIC_PASSWORD=never_return_this_value"],
        },
        "Mounts": [{"Source": "/root/very-private"}],
        "State": {"Running": running, "Health": {"Status": healthy}},
    }


async def produce(directory, responder, *, now=None, owner=None, gid=None):
    return await one_shot._run_disposable_hml_producer_once(
        upstream=httpx.MockTransport(responder), directory=directory,
        owner_uid=os.getuid() if owner is None else owner,
        expected_gid=os.getgid() if gid is None else gid,
        observed_at=now or datetime.now(timezone.utc),
    )


def inspect(directory, now):
    return reader._review_from_directory(
        directory, owner_uid=os.getuid(), expected_gid=os.getgid(), now=now,
    )


def test_one_shot_hml_get_atomic_publication_and_readback(directory):
    calls = []
    now = datetime.now(timezone.utc)

    def response(request):
        calls.append((request.method, str(request.url)))
        return httpx.Response(200, json=docker_payload())

    result = asyncio.run(produce(directory, response, now=now))
    assert calls == [(
        "GET", "http://docker.local/containers/delpi-hml-public-hub/json",
    )]
    assert result.status == "blocked"
    assert result.snapshot_written is True
    for field in ("snapshot_origin_attested", "upstream_isolation_attested",
                  "host_identity_attested", "checkout_integrity_attested",
                  "challenge_consumed", "prepare_eligible", "can_execute"):
        assert getattr(result, field) is False

    raw = (directory / "inspect-snapshot.json").read_bytes()
    assert b"SYNTHETIC_PASSWORD" not in raw
    assert b"/root/very-private" not in raw
    assert len(json.loads(raw)) == 11
    report = inspect(directory, now)
    assert report.container_id == ID
    assert report.image_id == IMAGE
    assert report.running and report.healthy
    assert report.status == "blocked"
    assert not report.prepare_eligible and not report.can_execute
    assert list(directory.glob(".atlas-hml-stage-*")) == []


@pytest.mark.parametrize("response", [
    lambda: httpx.Response(302, headers={"Location": "http://docker.local/containers/json"}),
    lambda: httpx.Response(401, json={"message":"synthetic secret"}),
    lambda: httpx.Response(200, json=docker_payload(project="delpi-prod")),
    lambda: httpx.Response(200, json=docker_payload(name="/delpi-public-hub")),
    lambda: httpx.Response(200, json={"unexpected": "production"}),
    lambda: httpx.Response(200, content=b"x"*262145),
])
def test_untrusted_engine_response_never_writes_snapshot(directory, response):
    seen=[]

    def reply(request):
        seen.append((request.method, str(request.url)))
        return response()

    with pytest.raises(one_shot.HMLOneShotError, match="HML_ONESHOT_INSPECT_UNAVAILABLE"):
        asyncio.run(produce(directory, reply))
    assert seen == [(
        "GET", "http://docker.local/containers/delpi-hml-public-hub/json",
    )]
    assert list(directory.iterdir()) == []


def test_unhealthy_engine_can_only_produce_a_blocked_diagnostic(directory):
    now = datetime.now(timezone.utc)
    result = asyncio.run(produce(
        directory,
        lambda _: httpx.Response(200, json=docker_payload(running=False, healthy="unhealthy")),
        now=now,
    ))
    assert not result.can_execute
    report = inspect(directory, now)
    assert not report.running and not report.healthy
    assert "HML_CONTAINER_NOT_HEALTHY" in report.blocks
    assert report.status == "blocked"


def test_upstream_error_keeps_previous_generation_and_sanitizes_details(directory):
    now = datetime.now(timezone.utc)
    asyncio.run(produce(
        directory, lambda _: httpx.Response(200, json=docker_payload()), now=now,
    ))
    before = (directory / "inspect-snapshot.json").read_bytes()
    def failed(_):
        raise httpx.ConnectError("SYNTHETIC_CREDENTIAL_IN_UPSTREAM")
    with pytest.raises(one_shot.HMLOneShotError) as exc:
        asyncio.run(produce(directory, failed, now=now))
    assert exc.value.code == "HML_ONESHOT_INSPECT_UNAVAILABLE"
    assert "SYNTHETIC_CREDENTIAL" not in str(exc.value)
    assert (directory / "inspect-snapshot.json").read_bytes() == before
    assert list(directory.glob(".atlas-hml-stage-*")) == []


def test_invalid_owner_group_or_path_denied_before_writes(directory):
    seen = []
    def reply(request):
        seen.append(request)
        return httpx.Response(200, json=docker_payload())
    with pytest.raises(one_shot.HMLOneShotError, match="HML_ONESHOT_INPUT_INVALID"):
        asyncio.run(produce(directory, reply, owner=-1))
    assert seen == []
    with pytest.raises(one_shot.HMLOneShotError, match="HML_ONESHOT_PUBLISH_UNAVAILABLE"):
        asyncio.run(produce(directory, reply, gid=os.getgid()+1))
    assert list(directory.iterdir()) == []


def test_bad_directory_permission_blocks_snapshot_and_no_temp(directory):
    os.chmod(directory, 0o777)
    with pytest.raises(one_shot.HMLOneShotError, match="HML_ONESHOT_PUBLISH_UNAVAILABLE"):
        asyncio.run(produce(
            directory, lambda _: httpx.Response(200, json=docker_payload()),
        ))
    assert list(directory.iterdir()) == []


def test_existing_symlink_destination_is_never_replaced(directory):
    victim = directory.with_name("do-not-touch")
    victim.write_text("safe")
    (directory / "inspect-snapshot.json").symlink_to(victim)
    with pytest.raises(one_shot.HMLOneShotError, match="HML_ONESHOT_PUBLISH_UNAVAILABLE"):
        asyncio.run(produce(
            directory, lambda _: httpx.Response(200, json=docker_payload()),
        ))
    assert victim.read_text() == "safe"
    assert list(directory.glob(".atlas-hml-stage-*")) == []


def test_transport_input_is_required_and_not_constructed_in_module(directory):
    with pytest.raises(one_shot.HMLOneShotError, match="HML_ONESHOT_INPUT_INVALID"):
        asyncio.run(one_shot._run_disposable_hml_producer_once(
            upstream=None, directory=directory, owner_uid=os.getuid(),
            expected_gid=os.getgid(), observed_at=datetime.now(timezone.utc),
        ))
    for name in ("main","get_docker_socket","create_mcp_server","deploy","serve"):
        assert not hasattr(one_shot, name)
