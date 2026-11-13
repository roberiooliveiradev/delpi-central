"""G2-S1 contract tests: local, no database and no device credentials."""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from it_portal_app.domain.workstation_snapshots import (
    SnapshotValidationError,
    validate_workstation_snapshot,
)

NOW = datetime(2026, 11, 13, 19, tzinfo=timezone.utc)


def sample():
    return {
        "source": "windows_workstation_local_v1",
        "schema_version": "1",
        "run_id": "2bb2c32d-d851-4e93-8f8a-cd845671c32a",
        "observed_at": "2026-11-13T18:59:59.000Z",
        "status": "partial",
        "host": {"hostname": "EXAMPLE-DEV-01"},
        "hardware": {
            "manufacturer": "Example Inc.", "model": "Model X",
            "cpu_name": "CPU Test", "logical_processors": 8,
            "memory_total_bytes": 17179869184,
        },
        "os": {
            "name": "Microsoft Windows 11 Pro", "version": "10.0.26200",
            "build_number": "26200", "architecture": "64-bit",
            "uptime_seconds": 3600,
        },
        "volumes": [{
            "mount_point": "C:", "filesystem": "NTFS",
            "capacity_bytes": 1000, "free_bytes": 500,
        }],
        "network": {"private_ipv4": []},
        "sections_status": {
            "hardware": "ok", "os": "ok", "volumes": "ok", "network": "unavailable",
        },
    }


class SnapshotTests(unittest.TestCase):
    def parse(self, raw):
        return validate_workstation_snapshot(raw, now=NOW)

    def test_valid_local_snapshot(self):
        result = self.parse(sample())
        self.assertEqual(result["host"]["hostname"], "example-dev-01")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["volumes"][0]["mount_point"], "C:")

    def test_complete_with_private_network(self):
        raw = sample()
        raw["network"]["private_ipv4"] = ["192.168.50.10", "10.1.0.7"]
        raw["sections_status"]["network"] = "ok"
        raw["status"] = "complete"
        self.assertEqual(self.parse(raw)["status"], "complete")

    def test_failed_all_unavailable(self):
        raw = sample()
        raw["sections_status"] = {v: "unavailable" for v in (
            "hardware", "os", "volumes", "network",
        )}
        raw["hardware"] = None
        raw["os"] = None
        raw["volumes"] = []
        raw["status"] = "failed"
        self.assertEqual(self.parse(raw)["status"], "failed")

    def test_private_ip_is_required(self):
        for bad in ["54.232.10.10", "127.0.0.1", "169.254.12.4", "8.8.8.8", "::1"]:
            raw = sample()
            raw["network"]["private_ipv4"] = [bad]
            with self.subTest(ip=bad), self.assertRaises(SnapshotValidationError):
                self.parse(raw)

    def test_refuses_sensitive_or_unknown_fields(self):
        for where in ["root", "hardware", "network"]:
            raw = sample()
            target = raw if where == "root" else raw[where]
            target["password"] = "not allowed"
            with self.subTest(where=where), self.assertRaises(SnapshotValidationError):
                self.parse(raw)

    def test_refuses_bad_disk_size(self):
        raw = sample()
        raw["volumes"][0]["free_bytes"] = 1001
        with self.assertRaises(SnapshotValidationError):
            self.parse(raw)

    def test_refuses_missing_timezone_and_old_timestamp(self):
        raw = sample()
        raw["observed_at"] = "2026-11-13T18:00:00"
        with self.assertRaises(SnapshotValidationError):
            self.parse(raw)
        raw["observed_at"] = (NOW - timedelta(days=2)).isoformat()
        with self.assertRaises(SnapshotValidationError):
            self.parse(raw)

    def test_refuses_invalid_id_and_mismatch(self):
        raw = sample()
        raw["run_id"] = "x"
        with self.assertRaises(SnapshotValidationError):
            self.parse(raw)
        raw = sample()
        raw["status"] = "complete"
        with self.assertRaises(SnapshotValidationError):
            self.parse(raw)

    def test_refuses_oversized_and_negative_count(self):
        raw = sample()
        raw["hardware"]["logical_processors"] = -1
        with self.assertRaises(SnapshotValidationError):
            self.parse(raw)
        raw = sample()
        raw["hardware"]["model"] = "A" * 35000
        with self.assertRaises(SnapshotValidationError):
            self.parse(raw)

    def test_script_is_local_only_by_construction(self):
        script = (Path(__file__).resolve().parents[1] / "collectors" / "windows_workstation"
                  / "Collect-ItPortalWorkstationSnapshot.ps1").read_text("utf-8")
        for forbidden in (
            "Invoke-RestMethod", "Invoke-WebRequest", "New-PSSession",
            "Start-Process", "Register-ScheduledTask", "Set-Service",
        ):
            self.assertNotIn(forbidden, script)
        self.assertIn("Win32_LogicalDisk", script)
        self.assertIn("Get-CimInstance", script)


if __name__ == "__main__":
    unittest.main()
