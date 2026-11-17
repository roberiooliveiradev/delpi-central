"""Pure, offline validation for the provisional HML snapshot contract.

Only synthetic JSON is used. No Docker, host, process or socket interaction.
"""
from __future__ import annotations

import json
import unittest
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from linux_ops_mcp.atlas_hml_snapshot_candidate import (
    SnapshotContractError,
    review_untrusted_snapshot,
)

NOW = datetime(2026, 11, 17, 15, 0, tzinfo=timezone.utc)
GOOD = {
    "schema": "atlas.hml.inspect.v1",
    "source": "root-one-shot-snapshot-claim-untrusted",
    "environment": "hml",
    "compose_project": "delpi-hml",
    "service_id": "public-hub",
    "container_name": "delpi-hml-public-hub",
    "container_id": "a" * 64,
    "image_id": "sha256:" + "b" * 64,
    "running": True,
    "healthy": True,
    "observed_at": "2026-11-17T15:00:00Z",
}


def encode(obj: dict[str, object]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


class TestProvisionalSnapshot(unittest.TestCase):
    def test_valid_shape_never_becomes_an_authorization(self):
        report = review_untrusted_snapshot(encode(GOOD), now=NOW)
        self.assertEqual(report.status, "blocked")
        for field in (
            "snapshot_origin_attested", "docker_access_boundary_attested",
            "proxy_policy_independently_attested", "host_identity_attested",
            "checkout_integrity_attested", "challenge_consumed",
            "prepare_eligible", "can_execute",
        ):
            self.assertIs(asdict(report)[field], False)
        self.assertIn("PREPARE_DISABLED", report.blocks)
        self.assertIn("ACT_DISABLED", report.blocks)
        self.assertIn("SNAPSHOT_TIMESTAMP_CLAIM_ONLY", report.blocks)

    def test_rejects_other_environment_project_container_and_source(self):
        for key, value in (
            ("environment", "prod"), ("compose_project", "delpi-prod"),
            ("service_id", "other"), ("container_name", "delpi-public-hub"),
            ("source", "self-attested-safe"),
        ):
            with self.subTest(key=key):
                self._reject({**GOOD, key: value}, "HML_SNAPSHOT_TARGET_DENIED")

    def test_rejects_extraneous_fields_including_env_and_mounts(self):
        for key, value in (("Env", ["SECRET=bad"]), ("Mounts", []), ("token", "s")):
            with self.subTest(key=key):
                self._reject({**GOOD, key: value}, "HML_SNAPSHOT_SCHEMA_INVALID")

    def test_rejects_missing_field(self):
        missing = dict(GOOD)
        del missing["image_id"]
        self._reject(missing, "HML_SNAPSHOT_SCHEMA_INVALID")

    def test_rejects_duplicate_keys_and_json_nonfinite(self):
        duplicate = encode(GOOD)[:-1] + b',"environment":"prod"}'
        self._reject_raw(duplicate, "HML_SNAPSHOT_DUPLICATE_FIELD")
        self._reject_raw(encode(GOOD).replace(b"true", b"NaN", 1), "HML_SNAPSHOT_JSON_INVALID")

    def test_rejects_invalid_id_and_bool_type_confusion(self):
        for key, value in (
            ("container_id", "a" * 63),
            ("container_id", "g" * 64),
            ("image_id", "sha256:" + "B" * 64),
            ("running", 1), ("healthy", "true"),
        ):
            with self.subTest(key=key):
                self._reject({**GOOD, key: value}, "HML_SNAPSHOT_CONTENT_INVALID")

    def test_timestamp_must_be_utc_and_recent(self):
        for stamp, code in (
            ("2026-11-17T14:58:59Z", "HML_SNAPSHOT_EXPIRED_OR_FUTURE"),
            ("2026-11-17T15:00:06Z", "HML_SNAPSHOT_EXPIRED_OR_FUTURE"),
            ("2026-11-17T15:00:00+03:00", "HML_SNAPSHOT_TIMESTAMP_INVALID"),
            ("not-a-time", "HML_SNAPSHOT_TIMESTAMP_INVALID"),
        ):
            with self.subTest(stamp=stamp):
                self._reject({**GOOD, "observed_at": stamp}, code)

    def test_boundary_timestamp_is_allowed_only_as_claim(self):
        report = review_untrusted_snapshot(
            encode({**GOOD, "observed_at": "2026-11-17T14:59:00Z"}), now=NOW,
        )
        self.assertEqual(report.status, "blocked")
        self.assertFalse(report.snapshot_origin_attested)

    def test_unhealthy_not_a_readiness_pass(self):
        report = review_untrusted_snapshot(encode({**GOOD, "running": False}), now=NOW)
        self.assertIn("HML_CONTAINER_NOT_HEALTHY", report.blocks)
        self.assertFalse(report.can_execute)

    def test_rejects_oversize_and_non_bytes(self):
        self._reject_raw(b"X" * 2049, "HML_SNAPSHOT_INPUT_INVALID")
        with self.assertRaisesRegex(SnapshotContractError, "HML_SNAPSHOT_INPUT_INVALID"):
            review_untrusted_snapshot("not bytes", now=NOW)

    def test_errors_are_finite_and_do_not_reflect_sensitive_input(self):
        raw = b'{"token":"SECRET_NEVER_EXPOSE"}'
        with self.assertRaises(SnapshotContractError) as ctx:
            review_untrusted_snapshot(raw, now=NOW)
        self.assertEqual(str(ctx.exception), "HML_SNAPSHOT_SCHEMA_INVALID")
        self.assertNotIn("SECRET_NEVER_EXPOSE", str(ctx.exception))

    def _reject(self, data: dict[str, object], code: str):
        self._reject_raw(encode(data), code)

    def _reject_raw(self, raw: bytes, code: str):
        with self.assertRaises(SnapshotContractError) as ctx:
            review_untrusted_snapshot(raw, now=NOW)
        self.assertEqual(ctx.exception.code, code)


if __name__ == "__main__":
    unittest.main()
