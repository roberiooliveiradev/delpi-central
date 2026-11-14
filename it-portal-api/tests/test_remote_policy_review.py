"""G0-SEC-S2: policy/network/recovery drafts must NEVER grant remote access."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from it_portal_app.domain.remote_policy_review import (
    CONTROL_OWNERS, DOCUMENTS, REGISTER, assess,
)

REPO = Path(__file__).resolve().parents[2]


def registry() -> dict:
    return json.loads((REPO / REGISTER).read_text(encoding="utf-8"))


def test_real_public_policy_drafts_are_complete_but_blocked():
    draft = registry()
    result = assess(REPO, draft)
    assert result.ci_pass, result.errors
    assert result.status == "BLOCKED"
    assert not result.remote_or_lab_authorized
    assert set(result.pending) == set(CONTROL_OWNERS)
    assert all(row["private_evidence_recorded"] is False for row in draft["checkpoints"])


def test_in_review_is_not_an_approval():
    draft = registry()
    for row in draft["checkpoints"]:
        row["review_state"] = "in_review"
    result = assess(REPO, draft)
    assert result.ci_pass, result.errors
    assert result.status == "BLOCKED"
    assert not result.remote_or_lab_authorized


@pytest.mark.parametrize("change", [
    "approved", "authorized", "lab_install", "unattended", "screen_capture",
    "retention", "rpo", "rto", "extra_key", "wrong_phase", "missing_gate",
    "duplicate_gate", "unknown_gate", "wrong_owner", "evidence_claim",
    "extra_gate_field", "string_false", "bad_docs", "schema_bool",
])
def test_unauthorized_policy_changes_fail_closed(change):
    draft = registry()
    if change == "approved":
        draft["status"] = "approved"
    elif change == "authorized":
        draft["remote_authorized"] = True
    elif change == "lab_install":
        draft["lab_install_authorized"] = True
    elif change == "unattended":
        draft["unattended_enabled"] = True
    elif change == "screen_capture":
        draft["screen_recording_enabled"] = True
    elif change == "retention":
        draft["retention_days"] = 90
    elif change == "rpo":
        draft["rpo_minutes"] = 60
    elif change == "rto":
        draft["rto_minutes"] = 120
    elif change == "extra_key":
        draft["keycloak_token"] = "test-secret"
    elif change == "wrong_phase":
        draft["phase"] = "G3-ENGINE"
    elif change == "missing_gate":
        draft["checkpoints"].pop()
    elif change == "duplicate_gate":
        draft["checkpoints"][0]["id"] = draft["checkpoints"][1]["id"]
    elif change == "unknown_gate":
        draft["checkpoints"][0]["id"] = "allow_anyone"
    elif change == "wrong_owner":
        draft["checkpoints"][0]["owner_role"] = "anonymous"
    elif change == "evidence_claim":
        draft["checkpoints"][0]["private_evidence_recorded"] = True
    elif change == "extra_gate_field":
        draft["checkpoints"][0]["signed_by"] = "somebody"
    elif change == "string_false":
        draft["remote_authorized"] = "false"
    elif change == "bad_docs":
        draft["documents"]["network"] = "../private/network.env"
    elif change == "schema_bool":
        draft["schema_version"] = True
    result = assess(REPO, draft)
    assert result.status == "INVALID", (change, result)
    assert result.errors
    assert not result.ci_pass
    assert not result.remote_or_lab_authorized


def test_missing_policy_document_fails_closed(tmp_path):
    draft = registry()
    result = assess(tmp_path, draft)
    assert not result.ci_pass
    assert any("documento ausente" in e for e in result.errors)


def test_documents_must_clearly_be_drafts_and_gate_blocked(tmp_path):
    draft = registry()
    for relative in DOCUMENTS.values():
        p = tmp_path / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# G0-SEC-S2\n**Status:** MINUTA\n**Gate:** G0-SEC\nBLOQUEADO\n", encoding="utf-8")
    ready = assess(tmp_path, draft)
    assert ready.ci_pass, ready.errors
    path = tmp_path / DOCUMENTS["recovery"]
    path.write_text("# G0-SEC-S2\n**Status:** APROVADO\n**Gate:** G0-SEC\n", encoding="utf-8")
    blocked = assess(tmp_path, draft)
    assert not blocked.ci_pass
    assert blocked.status == "INVALID"


def test_malformed_records_fail_closed():
    for value in ([], "", None, {}, {"schema_version": 1}):
        result = assess(REPO, value)
        assert not result.ci_pass
        assert not result.remote_or_lab_authorized


def test_register_contains_no_private_evidence_or_real_credentials():
    record = registry()
    raw = json.dumps(record, sort_keys=True)
    assert "token" not in raw.lower()
    assert "password" not in raw.lower()
    assert "client_secret" not in raw.lower()
    assert not record["remote_authorized"]
    assert not record["lab_install_authorized"]
