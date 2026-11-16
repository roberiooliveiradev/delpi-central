"""Cross-context ATLAS CI: real Linux host signers -> real Portal TI verifier.

Only disposable Git tmp_path and a simulated Docker GET response are used.
No production server, raw socket, database, network, migration, approval,
PREPARE or ACT. This catches drift between two Python package contracts.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import subprocess
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from linux_ops_mcp.deploy_git_checkout_readonly import GitCheckoutReadOnlyObserver
from linux_ops_mcp.deploy_git_checkout_witness import issue_git_checkout_witness
from linux_ops_mcp.deploy_host_runtime_v2 import issue_host_runtime_receipt_v2
from linux_ops_mcp.deploy_host_signer import SignedReleaseRecord, _DOMAIN as RELEASE_DOMAIN
from linux_ops_mcp.deploy_host_source import RuntimeContainer, RuntimeTarget

from it_portal_app.infrastructure.persistence.atlas_deploy_host_receipt_bridge import (
    ExpectedBaseRelease, HostReceiptBridgeError, PinnedHostTarget,
    SignedReceiptWire, verify_host_receipt_pair,
)

NOW = datetime(2026, 11, 16, 23, 0, tzinfo=timezone.utc)
TARGET = RuntimeTarget(
    environment="hml", service_id="public-hub", host_id="srv-api-pilot",
    container_name="delpi-hml-public-hub", compose_project="delpi-hml",
)
HOST_KEY = b"isolated-host-witness-32-plus-byte-fixture-key"
GIT_KEY = b"isolated-git-witness-32-plus-byte-fixture-key"
RELEASE_KEY = b"isolated-executor-record-32-plus-byte-fixture"
IMAGE = "sha256:" + "c" * 64
NONCE = "a" * 64


def fixture_git(root, *args):
    env = {
        "PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
    }
    return subprocess.run(
        ["git", "-C", str(root), *args], env=env,
        text=True, check=True, capture_output=True, timeout=10,
    ).stdout.strip()


class DockerStub:
    async def inspect(self, target):
        assert target == TARGET
        return RuntimeContainer(
            container_id="e" * 64, image_id=IMAGE,
            running=True, healthy=True,
        )


def make_pair(tmp_path):
    root=tmp_path/"ci-readonly-pilot"
    root.mkdir()
    fixture_git(root,"init","-q","-b","main")
    (root/"clean.txt").write_text("signed checkout fixture\n")
    fixture_git(root,"add","clean.txt")
    fixture_git(
        root,"-c","user.name=CI Test","-c","user.email=ci@example.invalid",
        "commit","-q","-m","isolated source revision",
    )
    sha=fixture_git(root,"rev-parse","HEAD")
    content=json.dumps({
        "version":1, "repository":"roberiooliveiradev/delpi-central",
        "host_id":TARGET.host_id,"environment":TARGET.environment,
        "service_id":TARGET.service_id,
        "execution_id":str(uuid4()),"commit_sha":sha,"image_id":IMAGE,
    },sort_keys=True,separators=(",",":")).encode()
    release=SignedReleaseRecord(
        content,
        hmac.new(RELEASE_KEY,RELEASE_DOMAIN+content,hashlib.sha256).hexdigest(),
    )
    signed_docker=asyncio.run(issue_host_runtime_receipt_v2(
        target=TARGET, release_record=release, inspector=DockerStub(),
        release_key=RELEASE_KEY, host_key=HOST_KEY, challenge=NONCE, now=NOW,
    ))
    observer=GitCheckoutReadOnlyObserver(
        checkout_root=root, clock=lambda:NOW,
    )
    signed_git=issue_git_checkout_witness(
        observer=observer, target=TARGET, signing_key=GIT_KEY,
        challenge=NONCE, now=NOW,
    )
    return sha, signed_docker, signed_git


def review(sha, runtime, git, **kwargs):
    return verify_host_receipt_pair(
        runtime_receipt=SignedReceiptWire(runtime.body,runtime.mac_hex),
        git_receipt=SignedReceiptWire(git.body,git.mac_hex),
        runtime_key=HOST_KEY, git_key=GIT_KEY,
        target=PinnedHostTarget(
            host_id=TARGET.host_id, environment=TARGET.environment,
            service_id=TARGET.service_id, container_name=TARGET.container_name,
            compose_project=TARGET.compose_project,
        ),
        base=ExpectedBaseRelease(sha,IMAGE), nonce=kwargs.get("nonce",NONCE),
        now=kwargs.get("now",NOW),
    )


def test_real_linux_signed_receipts_verify_cross_package_and_remain_inert(tmp_path):
    sha, runtime, git=make_pair(tmp_path)
    pair=review(sha,runtime,git)
    assert pair.signature_integrity_verified
    assert pair.base_commit_sha == sha
    assert pair.base_image_id == IMAGE
    assert pair.git_head_sha == sha
    assert pair.branch == "main"
    assert pair.running and pair.healthy and pair.git_observed_clean
    assert pair.challenge_digest == hashlib.sha256(bytes.fromhex(NONCE)).hexdigest()
    assert pair.blocks == (
        "HOST_COLLECTOR_IDENTITY_NOT_ATTESTED",
        "GIT_IGNORED_FILES_NOT_ATTESTED",
        "GIT_FILESYSTEM_NOT_ATOMIC",
        "CHALLENGE_NOT_CONSUMED",
    )
    assert not pair.collector_identity_attested
    assert not pair.checkout_integrity_attested
    assert not pair.challenge_consumed
    assert not pair.prepare_eligible


def test_real_linux_receipts_not_reusable_for_other_nonce_or_after_expiration(tmp_path):
    sha, runtime, git=make_pair(tmp_path)
    with pytest.raises(
        HostReceiptBridgeError, match="ATLAS_HOST_TARGET_OR_NONCE_DRIFT",
    ):
        review(sha,runtime,git,nonce="b"*64)
    with pytest.raises(
        HostReceiptBridgeError, match="ATLAS_HOST_RECEIPT_STALE",
    ):
        review(sha,runtime,git,now=NOW+timedelta(seconds=91))


def test_valid_linux_hmac_does_not_authorize_wrong_base_image(tmp_path):
    sha, runtime, git=make_pair(tmp_path)
    with pytest.raises(HostReceiptBridgeError, match="ATLAS_HOST_BASE_DRIFT"):
        verify_host_receipt_pair(
            runtime_receipt=SignedReceiptWire(runtime.body,runtime.mac_hex),
            git_receipt=SignedReceiptWire(git.body,git.mac_hex),
            runtime_key=HOST_KEY,git_key=GIT_KEY,
            target=PinnedHostTarget(
                host_id=TARGET.host_id, environment=TARGET.environment,
                service_id=TARGET.service_id, container_name=TARGET.container_name,
                compose_project=TARGET.compose_project,
            ),
            base=ExpectedBaseRelease(sha,"sha256:"+"0"*64),
            nonce=NONCE,now=NOW,
        )
