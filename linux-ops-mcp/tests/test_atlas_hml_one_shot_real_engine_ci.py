"""Real Engine test ONLY on GitHub-hosted disposable Docker runner.

The existing atlas-p22e CI job owns the temporary delpi-hml-public-hub fixture.
This test does not create/delete containers, modify Docker, or touch srv-api.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone

import httpx
import pytest

from linux_ops_mcp import atlas_hml_one_shot_candidate as candidate
from linux_ops_mcp import atlas_hml_snapshot_file_reader as reader


pytestmark = pytest.mark.skipif(
    not (
        os.getenv("GITHUB_ACTIONS") == "true"
        and os.getenv("ATLAS_DISPOSABLE_DOCKER") == "true"
        and os.getenv("ATLAS_REAL_HML_CHAIN_CI") == "true"
        and os.getuid() != 0
    ),
    reason="real Engine is allowed only in disposable GitHub Actions Docker job",
)


class RecordingDockerTransport(httpx.AsyncBaseTransport):
    def __init__(self):
        self._transport = httpx.AsyncHTTPTransport(uds="/var/run/docker.sock")
        self.observed = []

    async def handle_async_request(self, request):
        self.observed.append((request.method, str(request.url)))
        return await self._transport.handle_async_request(request)

    async def aclose(self):
        await self._transport.aclose()


def test_real_engine_one_shot_creates_only_blocked_snapshot_under_tmp_path(tmp_path):
    directory = tmp_path / "candidate-only"
    directory.mkdir(mode=0o750)
    os.chmod(directory, 0o750)
    now = datetime.now(timezone.utc)
    transport = RecordingDockerTransport()

    result = asyncio.run(candidate._run_disposable_hml_producer_once(
        upstream=transport,
        directory=directory,
        owner_uid=os.getuid(),
        expected_gid=os.getgid(),
        observed_at=now,
    ))
    assert transport.observed == [(
        "GET", "http://docker.local/containers/delpi-hml-public-hub/json",
    )]
    assert result.status == "blocked" and result.snapshot_written is True
    assert not result.prepare_eligible and not result.can_execute
    raw = (directory / "inspect-snapshot.json").read_bytes()
    claims = json.loads(raw)
    assert set(claims) == {
        "schema", "source", "environment", "compose_project",
        "service_id", "container_name", "container_id", "image_id",
        "running", "healthy", "observed_at",
    }
    assert claims["environment"] == "hml"
    assert claims["container_name"] == "delpi-hml-public-hub"
    assert claims["running"] is True and claims["healthy"] is True
    assert len(claims["container_id"]) == 64
    assert claims["image_id"].startswith("sha256:")
    report = reader._review_from_directory(
        directory, owner_uid=os.getuid(), expected_gid=os.getgid(), now=now,
    )
    assert report.status == "blocked"
    assert not report.snapshot_origin_attested
    assert not report.docker_access_boundary_attested
    assert not report.prepare_eligible
    assert not report.can_execute
    assert list(directory.glob(".atlas-hml-stage-*")) == []
