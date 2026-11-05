"""Regressão: duplicata local de HelpTooltip e integração incompleta devem falhar o gate."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from audit_plugin_ui_duplication import (
    audit,
    is_thin_wrapper,
    is_thin_wrapper_content,
    scan_duplicate_components,
    scan_integration,
)


class AuditPluginUiDuplicationTest(unittest.TestCase):
    def test_is_thin_wrapper_detects_create_factory(self) -> None:
        content = textwrap.dedent(
            """
            import { createDashboardKpiCard } from "@delpi/plugin-ui";
            export const KpiCard = createDashboardKpiCard({ prefix: "dp" });
            """
        )
        self.assertTrue(is_thin_wrapper_content(content))

    def test_scan_flags_local_help_tooltip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "fake-dashboard"
            target = plugin_dir / "src/components/HelpTooltip.tsx"
            target.parent.mkdir(parents=True)
            target.write_text(
                "export function HelpTooltip() { return null; }\n",
                encoding="utf-8",
            )
            findings = scan_duplicate_components(plugin_dir, strict=False)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].level, "error")
        self.assertIn("HelpTooltip.tsx", findings[0].message)

    def test_scan_ignores_wrapper_kpi_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "fake-dashboard"
            target = plugin_dir / "src/components/KpiCard.tsx"
            target.parent.mkdir(parents=True)
            target.write_text(
                'import { createDashboardKpiCard } from "@delpi/plugin-ui";\n'
                'export const KpiCard = createDashboardKpiCard({ prefix: "dp" });\n',
                encoding="utf-8",
            )
            findings = scan_duplicate_components(plugin_dir, strict=True)
        self.assertEqual(findings, [])

    def test_scan_integration_requires_vite_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "fake-plugin"
            (plugin_dir / "src").mkdir(parents=True)
            (plugin_dir / "src/main.tsx").write_text(
                'import "../../plugin-ui/src/styles.css";\n'
                'import { FieldLabel } from "@delpi/plugin-ui";\n',
                encoding="utf-8",
            )
            (plugin_dir / "vite.config.ts").write_text("// sem alias\n", encoding="utf-8")
            findings = scan_integration(plugin_dir)
        self.assertTrue(any("pluginUiRemote()" in f.message for f in findings))
        self.assertFalse(any("preparePluginUiRemote" in f.message for f in findings))

    def test_scan_integration_ignores_comment_only_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "fake-mfe"
            (plugin_dir / "src").mkdir(parents=True)
            (plugin_dir / "src/bootstrap.tsx").write_text(
                'import { FieldLabel } from "@delpi/plugin-ui/index";\n'
                "await preparePluginUiRemote();\n",
                encoding="utf-8",
            )
            (plugin_dir / "vite.config.ts").write_text(
                "// remotes: pluginUiRemote(),\nremotes: {},\n",
                encoding="utf-8",
            )
            findings = scan_integration(plugin_dir)
        self.assertTrue(any("pluginUiRemote()" in f.message for f in findings))

    def test_scan_integration_ignores_comment_only_styles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "fake-mfe"
            (plugin_dir / "src").mkdir(parents=True)
            (plugin_dir / "src/App.tsx").write_text(
                'import { FieldLabel } from "@delpi/plugin-ui/index";\n',
                encoding="utf-8",
            )
            (plugin_dir / "src/bootstrap.tsx").write_text(
                "// await preparePluginUiRemote();\n",
                encoding="utf-8",
            )
            (plugin_dir / "vite.config.ts").write_text(
                "remotes: pluginUiRemote(),\n",
                encoding="utf-8",
            )
            findings = scan_integration(plugin_dir)
        self.assertEqual(len(findings), 1)
        self.assertIn("preparePluginUiRemote()", findings[0].message)

    def test_scan_integration_source_alias_does_not_replace_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "fake-mfe"
            (plugin_dir / "src").mkdir(parents=True)
            (plugin_dir / "src/bootstrap.tsx").write_text(
                'import { FieldLabel } from "@delpi/plugin-ui/index";\n'
                "await preparePluginUiRemote();\n",
                encoding="utf-8",
            )
            (plugin_dir / "vite.config.ts").write_text(
                'alias: { "@delpi/plugin-ui": "/tmp/plugin-ui" },\n',
                encoding="utf-8",
            )
            findings = scan_integration(plugin_dir)
        self.assertTrue(any("pluginUiRemote()" in f.message for f in findings))

    def test_scan_integration_mfe_without_vite_config_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "fake-mfe"
            (plugin_dir / "src").mkdir(parents=True)
            (plugin_dir / "src/bootstrap.tsx").write_text(
                'import { FieldLabel } from "@delpi/plugin-ui/index";\n'
                "await preparePluginUiRemote();\n",
                encoding="utf-8",
            )
            findings = scan_integration(plugin_dir)
        self.assertEqual(len(findings), 1)
        self.assertIn("vite.config.*", findings[0].message)

    def test_scan_integration_accepts_federation_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "fake-mfe"
            (plugin_dir / "src").mkdir(parents=True)
            (plugin_dir / "src/App.tsx").write_text(
                'import { FieldLabel } from "@delpi/plugin-ui/index";\n',
                encoding="utf-8",
            )
            (plugin_dir / "src/bootstrap.tsx").write_text(
                "await preparePluginUiRemote();\n",
                encoding="utf-8",
            )
            (plugin_dir / "vite.config.ts").write_text(
                "remotes: pluginUiRemote(),\n",
                encoding="utf-8",
            )
            findings = scan_integration(plugin_dir)
        self.assertEqual(findings, [])

    def test_scan_integration_federation_still_requires_styles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "fake-mfe"
            (plugin_dir / "src").mkdir(parents=True)
            (plugin_dir / "src/bootstrap.tsx").write_text(
                'import { FieldLabel } from "@delpi/plugin-ui/index";\n',
                encoding="utf-8",
            )
            (plugin_dir / "vite.config.ts").write_text(
                "remotes: pluginUiRemote(),\n",
                encoding="utf-8",
            )
            findings = scan_integration(plugin_dir)
        self.assertEqual(len(findings), 1)
        self.assertIn("preparePluginUiRemote()", findings[0].message)

    def test_scan_integration_skips_library_without_vite_app(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "fake-lib"
            (plugin_dir / "src").mkdir(parents=True)
            (plugin_dir / "src/index.ts").write_text(
                'import { FieldLabel } from "@delpi/plugin-ui/index";\n',
                encoding="utf-8",
            )
            findings = scan_integration(plugin_dir)
        self.assertEqual(findings, [])

    def test_audit_respects_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "maintenance"
            target = plugin_dir / "src/components/DataTableSection.tsx"
            target.parent.mkdir(parents=True)
            target.write_text("export function DataTableSection() { return null; }\n", encoding="utf-8")
            (plugin_dir / "package.json").write_text("{}", encoding="utf-8")

            with mock.patch(
                "audit_plugin_ui_duplication.PLUGINS_DIR",
                Path(tmp),
            ):
                findings = audit(strict=True)

        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
