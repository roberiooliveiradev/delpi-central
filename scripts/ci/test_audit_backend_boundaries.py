#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_backend_boundaries.py")
spec = importlib.util.spec_from_file_location("audit_backend_boundaries", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def make_package(root: Path, api: str, package: str, *, under_src: bool = False) -> Path:
    base = root / api / ("src" if under_src else "") / package
    base.mkdir(parents=True, exist_ok=True)
    (base / "__init__.py").write_text("", encoding="utf-8")
    return base


class BackendBoundariesTest(unittest.TestCase):
    def test_discovers_unique_package_owners_without_manual_list(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_package(root, "commercial-api", "commercial_app")
            make_package(root, "financial-api", "financial_app")
            owners = mod.discover_unique_package_owners(root)
        self.assertEqual(owners["commercial_app"], "commercial-api")
        self.assertEqual(owners["financial_app"], "financial-api")

    def test_src_layout_package_is_discovered(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_package(root, "orders-api", "orders_service", under_src=True)
            owners = mod.discover_unique_package_owners(root)
        self.assertEqual(owners["orders_service"], "orders-api")

    def test_ambiguous_package_name_is_not_auto_gated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_package(root, "alpha-api", "app")
            make_package(root, "beta-api", "app")
            owners = mod.discover_unique_package_owners(root)
        self.assertNotIn("app", owners)

    def test_direct_import_from_sibling_api_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_package(root, "commercial-api", "commercial_app")
            make_package(root, "financial-api", "financial_app")
            source_file = root / "financial-api" / "financial_app" / "service.py"
            source_file.write_text("from commercial_app.domain import Customer\n", encoding="utf-8")
            owners = mod.discover_unique_package_owners(root)
            findings = mod.scan_source(
                "financial-api/financial_app/service.py",
                source_file.read_text(encoding="utf-8"),
                {1},
                owners,
                root,
            )
        self.assertEqual([item.rule for item in findings], ["BACKEND_SIBLING_API_IMPORT"])

    def test_plain_import_from_sibling_api_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_package(root, "commercial-api", "commercial_app")
            make_package(root, "financial-api", "financial_app")
            owners = mod.discover_unique_package_owners(root)
            findings = mod.scan_source(
                "financial-api/financial_app/service.py",
                "import commercial_app.domain\n",
                {1},
                owners,
                root,
            )
        self.assertEqual([item.rule for item in findings], ["BACKEND_SIBLING_API_IMPORT"])

    def test_import_from_own_package_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_package(root, "commercial-api", "commercial_app")
            make_package(root, "financial-api", "financial_app")
            owners = mod.discover_unique_package_owners(root)
            findings = mod.scan_source(
                "financial-api/financial_app/service.py",
                "from financial_app.domain import Invoice\n",
                {1},
                owners,
                root,
            )
        self.assertEqual(findings, [])

    def test_shared_or_third_party_import_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_package(root, "financial-api", "financial_app")
            owners = mod.discover_unique_package_owners(root)
            findings = mod.scan_source(
                "financial-api/financial_app/service.py",
                "from delpi_auth import require_auth\nimport httpx\n",
                {1, 2},
                owners,
                root,
            )
        self.assertEqual(findings, [])

    def test_relative_import_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_package(root, "financial-api", "financial_app")
            owners = mod.discover_unique_package_owners(root)
            findings = mod.scan_source(
                "financial-api/financial_app/service.py",
                "from .domain import Invoice\n",
                {1},
                owners,
                root,
            )
        self.assertEqual(findings, [])

    def test_historical_import_not_on_changed_line_does_not_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_package(root, "commercial-api", "commercial_app")
            make_package(root, "financial-api", "financial_app")
            owners = mod.discover_unique_package_owners(root)
            findings = mod.scan_source(
                "financial-api/financial_app/service.py",
                "from commercial_app.domain import Customer\nVALUE = 1\n",
                {2},
                owners,
                root,
            )
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
