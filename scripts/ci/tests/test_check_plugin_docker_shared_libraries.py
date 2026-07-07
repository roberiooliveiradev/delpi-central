"""Regressão: consumidor de biblioteca compartilhada sem COPY no Dockerfile deve falhar o gate."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_plugin_docker_shared_libraries import (
    detect_shared_dependencies,
    dockerfile_copies_directory,
    validate,
)


class CheckPluginDockerSharedLibrariesTest(unittest.TestCase):
    def test_detect_plugin_ui_dependency(self) -> None:
        manifest = {
            "libraries": [
                {
                    "directory": "plugin-ui",
                    "markers": ["@delpi/plugin-ui"],
                }
            ]
        }
        plugin_dir = Path("/tmp/fake-plugin")
        with mock.patch(
            "check_plugin_docker_shared_libraries.collect_plugin_sources",
            return_value='import { HelpTooltip } from "@delpi/plugin-ui";',
        ):
            deps = detect_shared_dependencies(plugin_dir, manifest)
        self.assertEqual(deps, {"plugin-ui"})

    def test_dockerfile_copy_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dockerfile = Path(tmp) / "Dockerfile"
            dockerfile.write_text(
                textwrap.dedent(
                    """
                    COPY plugin-ui/package*.json ./plugin-ui/
                    COPY plugin-ui ./plugin-ui
                    """
                ),
                encoding="utf-8",
            )
            self.assertTrue(dockerfile_copies_directory(dockerfile, "plugin-ui"))

    def test_validate_flags_missing_copy(self) -> None:
        manifest = {
            "requiredBuildContext": "../plugins",
            "libraries": [
                {
                    "directory": "plugin-ui",
                    "markers": ["@delpi/plugin-ui"],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = Path(tmp) / "tv-dashboard"
            plugin_dir.mkdir()
            (plugin_dir / "package.json").write_text("{}", encoding="utf-8")
            (plugin_dir / "Dockerfile").write_text("FROM node\n", encoding="utf-8")

            with (
                mock.patch(
                    "check_plugin_docker_shared_libraries.PLUGINS_DIR",
                    Path(tmp),
                ),
                mock.patch(
                    "check_plugin_docker_shared_libraries.detect_shared_dependencies",
                    return_value={"plugin-ui"},
                ),
                mock.patch(
                    "check_plugin_docker_shared_libraries.compose_build_context",
                    return_value="../plugins",
                ),
            ):
                errors = validate(manifest)

        self.assertEqual(len(errors), 1)
        self.assertIn("plugin-ui", errors[0])


if __name__ == "__main__":
    unittest.main()
