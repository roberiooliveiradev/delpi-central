#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("audit_platform_guardrails.py")
spec = importlib.util.spec_from_file_location("audit_platform_guardrails", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class PlatformGuardrailsTest(unittest.TestCase):
    def test_versioned_migration_detection(self):
        self.assertTrue(mod.is_versioned_migration("requests-api/migrations/V004__add_status.sql"))
        self.assertTrue(mod.is_versioned_migration("x/migrations/sql/V12__foo.sql"))
        self.assertFalse(mod.is_versioned_migration("x/migrations/README.md"))
        self.assertFalse(mod.is_versioned_migration("x/migrations/004_add_status.py"))

    def test_new_migration_is_allowed_but_mutation_is_blocked(self):
        with patch.object(mod, "changed_paths", return_value=[("A", ["x/migrations/V002__new.sql"])]):
            self.assertEqual(mod.scan_migration_mutations("base"), [])
        with patch.object(mod, "changed_paths", return_value=[("M", ["x/migrations/V001__old.sql"])]):
            findings = mod.scan_migration_mutations("base")
            self.assertEqual([item.rule for item in findings], ["IMMUTABLE_MIGRATION_MUTATION"])

    def test_migration_rename_is_blocked(self):
        with patch.object(
            mod,
            "changed_paths",
            return_value=[("R100", ["x/migrations/V001__old.sql", "x/migrations/V001__renamed.sql"])],
        ):
            findings = mod.scan_migration_mutations("base")
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].rule, "IMMUTABLE_MIGRATION_MUTATION")

    def test_mfe_css_scope(self):
        self.assertTrue(mod.is_mfe_css("plugins/my-requests/src/index.css"))
        self.assertFalse(mod.is_mfe_css("plugins/plugin-ui/src/styles/kpi.css"))
        self.assertFalse(mod.is_mfe_css("portal/src/index.css"))

    def test_global_css_is_blocked_but_scoped_dark_root_is_allowed(self):
        findings = mod.scan_mfe_css(
            "plugins/foo/src/index.css",
            {
                1: "body { margin: 0; }",
                2: ':root[data-theme="dark"] .dashboard-foo { --x: 1; }',
                3: ".dashboard-foo .card { padding: 1rem; }",
            },
        )
        self.assertEqual([item.rule for item in findings], ["MFE_GLOBAL_CSS"])

    def test_plugin_ui_class_override_is_blocked_but_token_is_allowed(self):
        findings = mod.scan_mfe_css(
            "plugins/foo/src/index.css",
            {
                1: ".dashboard-foo { --delpi-ui-surface: var(--surface); }",
                2: ".dashboard-foo .delpi-ui-kpi-card { padding: 4px; }",
            },
        )
        self.assertEqual([item.rule for item in findings], ["MFE_PLUGIN_UI_OVERRIDE"])

    def test_mfe_with_own_api_cannot_call_api_delpi_directly(self):
        with patch.object(mod, "mfe_has_own_api", return_value=True):
            findings = mod.scan_mfe_own_api_bypass(
                "plugins/foo/src/api.ts",
                {4: 'return fetch("/apps/api-delpi/products/123")'},
            )
        self.assertEqual([item.rule for item in findings], ["MFE_OWN_API_BYPASS"])

    def test_mfe_without_own_api_can_call_api_delpi(self):
        with patch.object(mod, "mfe_has_own_api", return_value=False):
            findings = mod.scan_mfe_own_api_bypass(
                "plugins/foo/src/api.ts",
                {4: 'return fetch("/apps/api-delpi/products/123")'},
            )
        self.assertEqual(findings, [])

    def test_mfe_own_api_gate_ignores_docs_and_shared_package(self):
        with patch.object(mod, "mfe_has_own_api", return_value=True):
            self.assertEqual(
                mod.scan_mfe_own_api_bypass(
                    "plugins/foo/README.md", {1: "GET /apps/api-delpi/products"}
                ),
                [],
            )
            self.assertEqual(
                mod.scan_mfe_own_api_bypass(
                    "plugins/plugin-ui/src/index.ts", {1: '"/apps/api-delpi/products"'}
                ),
                [],
            )

    def test_jwt_verify_disabled_is_blocked_in_production(self):
        findings = mod.scan_jwt_verify_disabled(
            "some-api/app/auth.py",
            {10: 'jwt.decode(token, key, options={"verify_signature": False})'},
        )
        self.assertEqual([item.rule for item in findings], ["JWT_VERIFY_DISABLED"])

    def test_jwt_verify_disabled_test_fixture_is_ignored(self):
        findings = mod.scan_jwt_verify_disabled(
            "some-api/tests/test_auth.py",
            {10: 'jwt.decode(token, key, options={"verify_signature": False})'},
        )
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
