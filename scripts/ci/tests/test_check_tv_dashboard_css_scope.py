"""Regressão: gate de escopo CSS do TV Dashboard."""

from __future__ import annotations

import sys
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_tv_dashboard_css_scope import (
    check_css,
    selector_is_scoped,
    split_selector_list,
)


class CheckTvDashboardCssScopeTest(unittest.TestCase):
    def test_split_selector_list(self) -> None:
        parts = split_selector_list(".td-a, .td-b:not(.x, .y), .td-c")
        self.assertEqual(parts, [".td-a", ".td-b:not(.x, .y)", ".td-c"])

    def test_scoped_selectors_ok(self) -> None:
        self.assertTrue(selector_is_scoped(".dashboard-tv-dashboard .td-app-shell"))
        self.assertTrue(
            selector_is_scoped(':root[data-theme="dark"] .dashboard-tv-dashboard .td-card')
        )
        self.assertTrue(
            selector_is_scoped("#root:has(> .dashboard-tv-dashboard) .td-btn")
        )

    def test_unscoped_component_fails(self) -> None:
        css = textwrap.dedent(
            """
            .td-app-shell {
              padding: 8px;
            }
            """
        )
        violations = check_css(css)
        self.assertTrue(any(v.kind == "unscoped-component" for v in violations))

    def test_scoped_component_passes(self) -> None:
        css = textwrap.dedent(
            """
            .dashboard-tv-dashboard .td-app-shell {
              padding: 8px;
            }
            @media (max-width: 768px) {
              .dashboard-tv-dashboard .td-app-shell {
                padding: 4px;
              }
            }
            @keyframes td-spin {
              from { opacity: 0; }
              to { opacity: 1; }
            }
            """
        )
        violations = check_css(css)
        self.assertEqual(violations, [])

    def test_bare_body_and_root_fail(self) -> None:
        css = textwrap.dedent(
            """
            body {
              margin: 0;
            }
            :root {
              --x: 1;
            }
            """
        )
        kinds = {v.kind for v in check_css(css)}
        self.assertIn("bare-body", kinds)
        self.assertIn("bare-root", kinds)

    def test_root_data_theme_allowed(self) -> None:
        css = textwrap.dedent(
            """
            :root[data-theme="dark"] .dashboard-tv-dashboard {
              --td-surface: #111;
            }
            """
        )
        self.assertEqual(check_css(css), [])

    def test_unscoped_inside_media_fails(self) -> None:
        css = textwrap.dedent(
            """
            @media (max-width: 768px) {
              .td-toolbar {
                flex-direction: column;
              }
            }
            """
        )
        violations = check_css(css)
        self.assertTrue(any(v.kind == "unscoped-component" for v in violations))


if __name__ == "__main__":
    unittest.main()
