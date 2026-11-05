#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_mfe_plugin_ui_css.py")
spec = importlib.util.spec_from_file_location("audit_mfe_plugin_ui_css", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

BUILD_SCRIPT = Path(__file__).resolve().parents[2] / "scripts/ci/build-tv-dashboard.sh"


class MfePluginUiCssInventoryTest(unittest.TestCase):
    def finding(self, plugin: str, path: str, line: int, snippet: str) -> mod.Finding:
        return mod.Finding(plugin, path, line, snippet)

    def test_open_debt_is_never_labeled_pass(self):
        report = mod.render_report(
            [self.finding("helpdesk", "plugins/helpdesk/src/index.css", 4, ".x .delpi-ui-action-btn { }")]
        )
        self.assertIn("FULL_TREE_DEBT = OPEN", report)
        self.assertNotIn("FULL_TREE_DEBT = PASS", report)
        self.assertIn("helpdesk 1", report)
        self.assertIn("action-btn 1", report)

    def test_zero_debt_is_clear(self):
        report = mod.render_report([])
        self.assertIn("FULL_TREE_DEBT = CLEAR", report)
        self.assertIn("TOTAL = 0", report)

    def test_removed_and_new_identities_are_listed(self):
        old = self.finding("foo", "plugins/foo/src/a.css", 1, ".a .delpi-ui-card { color: red; }")
        kept = self.finding("foo", "plugins/foo/src/a.css", 2, ".a .delpi-ui-icon-btn { }")
        new = self.finding("foo", "plugins/foo/src/a.css", 3, ".a .delpi-ui-modal { }")
        added, removed = mod.diff_findings([old, kept], [kept, new])
        report = mod.render_report([kept, new], added=added, removed=removed)
        self.assertIn("NEW = 1", report)
        self.assertIn("REMOVED = 1", report)
        self.assertIn("delpi-ui-modal", report)
        self.assertIn("delpi-ui-card", report)
        self.assertNotIn("FULL_TREE_DEBT = PASS", report)

    def test_tv_build_keeps_inventory_and_blocks_only_the_regression_gate(self):
        text = BUILD_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('python3 "$ROOT/scripts/ci/audit_mfe_plugin_ui_css.py" --base "$REGRESSION_BASE"', text)
        self.assertNotIn("audit_mfe_plugin_ui_css.py --check", text)
        self.assertIn(
            'python3 "$ROOT/scripts/ci/audit_platform_guardrails.py" --check --base "$REGRESSION_BASE"',
            text,
        )
        self.assertIn("merge-base HEAD origin/main", text)
        resolver = text.split("resolve_regression_base()", 1)[1].split("echo \"[CI] Gate CSS", 1)[0]
        self.assertLess(resolver.index("merge-base HEAD origin/main"), resolver.index("HEAD^"))


if __name__ == "__main__":
    unittest.main()
