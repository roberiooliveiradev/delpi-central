"""P2.2e: real Engine GET only on ephemeral GitHub-hosted CI pilot container.

Skipped by default, including on srv-api. Never runs with MCP privileges.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest

from linux_ops_mcp.deploy_host_receipt import verify_host_receipt
from linux_ops_mcp.deploy_host_runtime_v2 import (
    issue_host_runtime_receipt_v2, verify_host_runtime_receipt_v2,
)
from linux_ops_mcp.deploy_host_signer import (
    SignedReleaseRecord, _DOMAIN, issue_host_receipt,
)
from linux_ops_mcp.deploy_host_source import (
    DockerReadOnlyInspect, HostSourceError, RuntimeTarget,
)

pytestmark = pytest.mark.skipif(
    not (os.getenv("GITHUB_ACTIONS") == "true"
         and os.getenv("ATLAS_DISPOSABLE_DOCKER") == "true"),
    reason="only on GitHub-hosted disposable Docker CI runner",
)

TARGET = RuntimeTarget(
    environment="hml", service_id="atlas-ci-pilot", host_id="atlas-ci-host",
    compose_project="atlas-ci-hml", container_name="atlas-ci-pilot-hml",
)
RELEASE_KEY = b"ci-only-executor-seal-key-32-characters-plus"
HOST_KEY = b"ci-only-host-attestation-key-32-characters"
CHALLENGE = "f" * 64


def inspect(target: RuntimeTarget):
    async def inner():
        transport = httpx.AsyncHTTPTransport(uds="/var/run/docker.sock")
        try:
            return await DockerReadOnlyInspect(transport=transport).inspect(target)
        finally:
            await transport.aclose()
    return asyncio.run(inner())


def test_real_ephemeral_docker_image_and_labels():
    measured = inspect(TARGET)
    assert measured.running is True and measured.healthy is True
    assert measured.image_id.startswith("sha256:")
    assert len(measured.container_id) == 64
    for wrong in (
        replace(TARGET, service_id="another-service"),
        replace(TARGET, compose_project="another-project"),
    ):
        with pytest.raises(HostSourceError, match="INSPECT_TARGET_MISMATCH"):
            inspect(wrong)


def test_real_engine_release_image_binding_and_signed_receipt():
    measured = inspect(TARGET)
    now = datetime.now(timezone.utc)
    record = {
        "version": 1,
        "repository": "roberiooliveiradev/delpi-central",
        "host_id": TARGET.host_id,
        "environment": TARGET.environment,
        "service_id": TARGET.service_id,
        "execution_id": str(uuid4()),
        "commit_sha": "a" * 40,
        "image_id": measured.image_id,
    }
    encoded = json.dumps(record, separators=(",", ":"), sort_keys=True).encode()
    signed = SignedReleaseRecord(
        encoded, hmac.new(RELEASE_KEY, _DOMAIN + encoded, hashlib.sha256).hexdigest()
    )

    async def sign():
        transport = httpx.AsyncHTTPTransport(uds="/var/run/docker.sock")
        try:
            return await issue_host_receipt(
                target=TARGET, release_record=signed,
                inspector=DockerReadOnlyInspect(transport=transport),
                release_key=RELEASE_KEY, host_key=HOST_KEY,
                challenge=CHALLENGE, now=now,
            )
        finally:
            await transport.aclose()

    receipt = asyncio.run(sign())
    proof = verify_host_receipt(
        receipt, secret=HOST_KEY, expected_host_id=TARGET.host_id,
        expected_environment="hml", expected_service_id=TARGET.service_id,
        expected_challenge=CHALLENGE, now=now,
    )
    assert proof.deployed_commit_sha == "a" * 40
    # Synthetic CI release record is not true deployment provenance.
    assert not proof.checkout_clean
    assert not proof.migrations_safe
    assert not proof.rollback_ready

    async def sign_v2():
        transport = httpx.AsyncHTTPTransport(uds="/var/run/docker.sock")
        try:
            return await issue_host_runtime_receipt_v2(
                target=TARGET, release_record=signed,
                inspector=DockerReadOnlyInspect(transport=transport),
                release_key=RELEASE_KEY, host_key=HOST_KEY,
                challenge=CHALLENGE, now=now,
            )
        finally:
            await transport.aclose()

    receipt_v2 = asyncio.run(sign_v2())
    snapshot = verify_host_runtime_receipt_v2(
        receipt_v2, secret=HOST_KEY, target=TARGET,
        expected_challenge=CHALLENGE, now=now,
    )
    assert snapshot.running_image_id == measured.image_id
    assert snapshot.container_id == measured.container_id
    assert snapshot.container_name == TARGET.container_name
    assert snapshot.compose_project == TARGET.compose_project
    assert snapshot.signature_verified and snapshot.challenge_bound
    assert not snapshot.checkout_clean
    assert not snapshot.migrations_safe
    assert not snapshot.rollback_ready
    assert not snapshot.challenge_consumed
