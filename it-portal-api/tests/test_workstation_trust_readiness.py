"""P4 tests: even a green Windows probe cannot approve a device."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from it_portal_app.domain.workstation_trust_readiness import evaluate_report

NOW = datetime(2026, 11, 15, 0, 40, tzinfo=timezone.utc)


def report(**changes):
    data = {
        "schema_version": 1,
        "kind": "delpi-it-remote-p4-readiness",
        "origin": "unauthenticated-local-readonly",
        "collected_at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platform": "windows",
        "tpm": {"present": "yes", "ready": "yes", "spec": "2.0"},
        "secure_boot": "enabled",
        "hardware_attested": False,
        "key_bound": False,
        "activation_authorized": False,
    }
    data.update(changes)
    return json.dumps(data)


def validate(raw):
    return evaluate_report(raw, now=NOW)


def test_ready_only_candidate_never_authorized():
    result = validate(report())
    assert result.status == "CANDIDATE"
    assert result.attested is False
    assert result.enrollment_authorized is False


@pytest.mark.parametrize("change", [
    {"tpm": {"present": "no", "ready": "no", "spec": "unknown"}},
    {"tpm": {"present": "yes", "ready": "no", "spec": "2.0"}},
    {"tpm": {"present": "yes", "ready": "yes", "spec": "1.2"}},
    {"secure_boot": "disabled"},
])
def test_missing_security_preconditions(change):
    assert validate(report(**change)).status == "NOT_READY"


@pytest.mark.parametrize("change", [
    {"tpm": {"present": "unknown", "ready": "unknown", "spec": "unknown"}},
    {"tpm": {"present": "yes", "ready": "unknown", "spec": "2.0"}},
    {"secure_boot": "unknown"},
])
def test_missing_privileges_or_unknown(change):
    assert validate(report(**change)).status == "INCONCLUSIVE"


def test_non_windows_not_ready():
    raw = report(platform="non_windows",
                 tpm={"present": "unknown", "ready": "unknown", "spec": "unknown"},
                 secure_boot="unknown")
    assert validate(raw).status == "NOT_READY"


@pytest.mark.parametrize("change", [
    {"hardware_attested": True}, {"key_bound": True},
    {"activation_authorized": True}, {"activation_authorized": "false"},
    {"hostname": "HOST-NAME"}, {"ek_certificate": "SECRET"},
    {"schema_version": True}, {"schema_version": 2},
    {"kind": "other"}, {"origin": "attested-by-tpm"},
    {"secure_boot": True}, {"platform": "server"},
    {"tpm": {"present": "yes", "ready": "yes", "spec": "2.0", "serial": "hidden"}},
    {"tpm": {"present": "no", "ready": "yes", "spec": "unknown"}},
    {"tpm": {"present": "unknown", "ready": "unknown", "spec": "2.0"}},
])
def test_strict_rejections(change):
    assert validate(report(**change)).status == "INVALID"


def test_duplicate_json_keys_must_not_override_protection():
    raw = report()
    assert validate(raw[:-1] + ',"activation_authorized":true}').status == "INVALID"


@pytest.mark.parametrize("offset", [-960, 130])
def test_stale_and_future_timestamp_rejected(offset):
    stamp = (NOW + timedelta(seconds=offset)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert validate(report(collected_at=stamp)).status == "INVALID"


def test_timestamp_utc_size_and_malformed_rejected():
    assert validate(report(collected_at=NOW.isoformat())).status == "INVALID"
    assert validate(report(extra_field="x" * 3000)).status == "INVALID"
    for raw in ("{}", "null", "not json"):
        assert validate(raw).status == "INVALID"


def test_non_windows_cannot_forge_tpm():
    assert validate(report(platform="non_windows")).status == "INVALID"
