"""G0-SEC-S1: no public file or CI check may authorize MeshCentral."""
from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

import pytest

from it_portal_app.domain.remote_engine_lab_intake import (
    MANIFEST_PATH, REQUIRED_RISK_IDS, assess,
)

REPO = Path(__file__).resolve().parents[2]


def candidate() -> dict:
    return json.loads((REPO / MANIFEST_PATH).read_text(encoding="utf-8"))


def test_official_release_identity_is_pinned_but_lab_stays_blocked():
    record = candidate()
    report = assess(record, today=date(2026, 11, 13))
    assert report.ci_pass, report.errors
    assert report.status == "BLOCKED"
    assert not report.engine_install_authorized
    assert report.pending
    assert {risk["id"] for risk in record["risks"]} == REQUIRED_RISK_IDS
    assert record["source"]["artifact_sha256"] is None


@pytest.mark.parametrize("bad", [
    "changed_repo", "changed_tag", "changed_commit", "short_sha",
    "bad_digest", "secret_field", "public_inbound", "truthy_string",
    "prod_credentials", "prod_agents", "remote_running",
    "risks_missing", "risks_approved", "risk_duplicate", "malicious_ref",
    "future_verified", "schema_downgrade",
])
def test_lab_gates_fail_closed_for_untrusted_config(bad):
    record = candidate()
    src, env, risks = record["source"], record["environment"], record["risks"]
    if bad == "changed_repo":
        src["repository"] = "https://example.com/MeshCentral"
    elif bad == "changed_tag":
        src["tag"] = "1.3.2"
    elif bad == "changed_commit":
        src["tag_commit_sha"] = "f" * 40
    elif bad == "short_sha":
        src["tag_commit_sha"] = "f436143"
    elif bad == "bad_digest":
        src["artifact_sha256"] = "NOT_VERIFIED"
    elif bad == "secret_field":
        record["client_secret"] = "SHOULD_NEVER_EXIST"
    elif bad == "public_inbound":
        env["inbound_from_internet"] = True
    elif bad == "truthy_string":
        env["inbound_from_internet"] = "false"
    elif bad == "prod_credentials":
        env["production_credentials"] = True
    elif bad == "prod_agents":
        env["production_devices_enrolled"] = True
    elif bad == "remote_running":
        env["remote_engine_installed"] = True
    elif bad == "risks_missing":
        risks.pop()
    elif bad == "risks_approved":
        risks[0]["state"] = "approved"
    elif bad == "risk_duplicate":
        risks[0]["id"] = risks[1]["id"]
    elif bad == "malicious_ref":
        risks[0]["public_reference"] = "http://localhost/pseudo"
    elif bad == "future_verified":
        src["verified_on"] = "2099-01-01"
    elif bad == "schema_downgrade":
        record["schema_version"] = 0
    result = assess(record, today=date(2026, 11, 13))
    assert result.status == "INVALID", bad
    assert result.errors, bad
    assert not result.engine_install_authorized
    assert not result.ci_pass


def test_digest_presence_cannot_authorize_deployment():
    record = candidate()
    record["source"]["artifact_sha256"] = "a" * 64
    for risk in record["risks"]:
        risk["state"] = "in_review"
    result = assess(record, today=date(2026, 11, 13))
    assert result.status == "BLOCKED"
    assert not result.engine_install_authorized


def test_stale_source_is_warning_not_auto_permission_or_unrelated_ci_failure():
    record = candidate()
    result = assess(record, today=date(2026, 12, 15))
    assert result.status == "BLOCKED"
    assert result.ci_pass
    assert not result.engine_install_authorized
    assert any("antiga" in warning for warning in result.warnings)


def test_explicit_disallowed_types_rejected():
    record = candidate()
    record["source"]["tag_commit_sha"] = None
    assert not assess(record, today=date(2026, 11, 13)).ci_pass
    record = candidate()
    record["source"]["artifact_sha256"] = True
    assert not assess(record, today=date(2026, 11, 13)).ci_pass


def test_incomplete_or_unrecognized_manifest_fails_closed():
    for record in (None, [], {}, {"schema_version": 1}, "ready"):
        result = assess(record, today=date(2026, 11, 13))
        assert result.status == "INVALID"
        assert not result.ci_pass
