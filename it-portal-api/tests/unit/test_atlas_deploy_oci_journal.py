"""Offline fail-closed checks for P2.2h.2b; no DB, Docker, network or API."""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from it_portal_app.infrastructure.persistence.atlas_deploy_journal import JournalRejected
from it_portal_app.infrastructure.persistence.atlas_deploy_oci_journal import (
    _binding_equals, store_oci_prepared,
)


class NoDb:
    def __getattr__(self, key):
        raise AssertionError(f"Unexpected DB call: {key}")


def test_no_backend_policy_is_denied_before_any_database_touch():
    with pytest.raises(JournalRejected, match="OCI_POLICY_DISABLED"):
        store_oci_prepared(
            NoDb(), intent=None, candidate=None, ci=None, host=None,
            signed_receipt_challenge="a" * 64,
        )


def test_bool_like_values_do_not_enable_policy():
    for invalid in (1, "true", [], None):
        with pytest.raises(JournalRejected, match="OCI_POLICY_DISABLED"):
            store_oci_prepared(
                NoDb(), intent=None, candidate=None, ci=None, host=None,
                signed_receipt_challenge="a" * 64,
                backend_policy_enabled=invalid,
            )


def test_missing_contract_is_denied_before_any_database_touch():
    with pytest.raises(JournalRejected, match="OCI_CONTRACT_INVALID"):
        store_oci_prepared(
            NoDb(), intent=None, candidate=None, ci=None, host=None,
            signed_receipt_challenge="a" * 64, backend_policy_enabled=True,
        )


def test_binding_comparison_catches_manifest_change_and_timestamp():
    now = datetime(2026, 11, 16, tzinfo=timezone.utc)
    expected = (
        "11111111-2222-4333-8444-555555555555",
        "01234567-89ab-4def-8abc-0123456789ab",
        "prod", "public-hub", "a" * 40, "b" * 40, "sha256:" + "c" * 64,
        "sha256:" + "d" * 64, "sha256:" + "e" * 64, "sha256:" + "e" * 64,
        "f" * 64, "9" * 64, "8" * 64, "7" * 64, now, now,
    )
    assert _binding_equals(expected, expected)
    modified = list(expected)
    modified[6] = "sha256:" + "0" * 64
    assert not _binding_equals(modified, expected)
    modified = list(expected)
    modified[13] = "0" * 64
    assert not _binding_equals(modified, expected)
    modified = list(expected)
    modified[14] = now.replace(tzinfo=None)
    assert not _binding_equals(modified, expected)
    assert not _binding_equals(expected[:-1], expected)


def test_oci_persistence_has_no_mutating_host_or_http_apis():
    source = (Path(__file__).resolve().parents[2]
              / "it_portal_app/infrastructure/persistence/atlas_deploy_oci_journal.py").read_text()
    for forbidden in ("subprocess", "docker pull", "docker compose", "os.system",
                      "requests.post", "ssh ", "paramiko", "httpx.post"):
        assert forbidden not in source
