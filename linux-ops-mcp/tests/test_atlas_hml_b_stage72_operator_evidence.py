"""ATLAS stage 72: disposable operator evidence gate, never PROD or srv-api."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from linux_ops_mcp import atlas_hml_b_stage72_operator_evidence as stage72
from linux_ops_mcp.atlas_hml_b_stage71_readonly_preflight import (
    collect_stage71_readonly,
)

_REVIEW = Path(__file__).resolve().parents[1] / "ops-review" / "atlas-hml-stage72-host-evidence.sh.review"


def test_cli_requires_explicit_scope_and_does_not_read_real_host(capsys):
    with pytest.raises(SystemExit) as exc:
        stage72.main([])
    assert exc.value.code == 2
    assert not capsys.readouterr().out


@pytest.mark.parametrize("bad", [".", "relative/path", "missing-dir"])
def test_cli_rejects_relative_fixture_root(bad):
    with pytest.raises(SystemExit) as exc:
        stage72.main(["--fixture-root", bad])
    assert exc.value.code == 2


def test_cli_fixture_stdout_only_blocked(tmp_path, capsys):
    assert stage72.main(["--fixture-root", str(tmp_path)]) == 0
    lines = capsys.readouterr()
    assert not lines.err
    doc = json.loads(lines.out)
    assert doc["schema"] == "atlas.hml.stage72.readonly-observation.v1"
    assert doc["status"] == "blocked"
    assert doc["observation_kind"] == "operator_self_observation"
    assert doc["host_attested"] is False
    assert doc["prepare_eligible"] is False
    assert doc["can_execute"] is False
    assert doc["prepare_enabled"] is False and doc["act_enabled"] is False
    assert doc["docker_socket_metadata"]["endpoint_connect_attempted"] is False
    assert doc["docker_socket_metadata"]["kind"] == "absent"
    assert doc["mcp_tools"] == [
        "get_deployment_revision", "get_host_health",
        "get_service_health", "list_managed_services",
    ]
    assert "SEC_01_TO_10_PENDING" in doc["blocks"]
    assert len(doc["directories"]) == 5
    assert len(doc["identities"]) == 3


def test_cli_fixture_does_not_create_files(tmp_path, capsys):
    before = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")}
    assert stage72.main(["--fixture-root", str(tmp_path)]) == 0
    capsys.readouterr()
    after = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")}
    assert before == after


def test_build_report_has_no_runtime_privilege_promotion(tmp_path):
    probe = collect_stage71_readonly(root=tmp_path)
    report = stage72.build_stage72_evidence(probe)
    assert report["status"] == "blocked"
    assert not report["host_attested"]
    assert not report["can_execute"]
    assert "NOT_INDEPENDENT_HOST_ATTESTATION" in report["blocks"]
    with pytest.raises(ValueError, match="STAGE72_OBSERVATION_TYPE_DENIED"):
        stage72.build_stage72_evidence({"status": "ready"})


def test_review_only_shell_has_readonly_fixed_scope():
    raw = _REVIEW.read_text(encoding="utf-8")
    assert raw.startswith("#!/bin/sh\n")
    assert "GIT_OPTIONAL_LOCKS=0" in raw
    assert "delpi-hml-public-hub delpi-public-hub" in raw
    assert "HEALTH={{with index .State" in raw
    assert "HOST_ATTESTED=false" in raw
    assert "NO_DEPLOY_NO_MUTATION" in raw
    assert "PREPARE=false ACT=false" in raw
    assert "sudo " not in raw
    assert "docker inspect --type container" in raw
    forbidden = [
        "docker rm ", "docker run ", "docker restart ", "docker compose ",
        "git pull ", "git fetch ", "git reset ", "git stash ", "git clean ",
        "systemctl start ", "systemctl stop ", "systemctl enable ",
        "useradd ", "groupadd ", "chown ", "chmod ",
        "mktemp ", "tee ", "exec ", "curl ", "wget ",
    ]
    for token in forbidden:
        assert token not in raw, token
