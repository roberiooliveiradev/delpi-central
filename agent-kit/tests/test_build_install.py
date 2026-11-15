"""Tests for agent-kit/scripts/build.py and install.py (stdlib unittest)."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "scripts"))

import build  # noqa: E402
import install  # noqa: E402


def frontmatter(text: str) -> str:
    assert text.startswith("---\n"), "agente sem frontmatter"
    return text.split("---\n", 2)[1]


class BuildTests(unittest.TestCase):
    def test_render_all_platforms(self):
        for platform in build.PLATFORMS:
            with self.subTest(platform=platform):
                text = build.render_agent(platform, "model-x", "/usr/bin/python3", Path("/h/.delpi-agent-kit"))
                fm = frontmatter(text)
                self.assertIn("name: delpi-verifier", fm)
                self.assertIn("model: model-x", fm)
                self.assertNotIn("{{", text)
                self.assertIn(build.AGENT_FILE_MARKER, text)
                self.assertIn('"/h/.delpi-agent-kit/verifier_hooks.py" record', text)
                self.assertIn("# Relatório do delpi-verifier", text)

    def test_model_line_dropped_when_absent(self):
        fm = frontmatter(build.render_agent("cursor", None, "/usr/bin/python3", Path("/k")))
        self.assertNotIn("model:", fm)

    def test_platform_specific_permissions(self):
        cursor = frontmatter(build.render_agent("cursor", None, "py", Path("/k")))
        devin = frontmatter(build.render_agent("devin", None, "py", Path("/k")))
        claude = frontmatter(build.render_agent("claude", None, "py", Path("/k")))
        self.assertIn("readonly: false", cursor)  # readonly:true would block test runs in Cursor
        self.assertIn("- exec", devin)
        self.assertNotIn("- write", devin)
        self.assertNotIn("- edit", devin)
        self.assertIn("tools: Read, Grep, Glob, Bash", claude)
        self.assertIn("guard --host claude --always", claude)

    def test_hook_configs_reference_script(self):
        for hooks in (build.cursor_hooks("py", Path("/k")), build.devin_hooks("py", Path("/k"))):
            self.assertTrue(all(build.HOOK_SCRIPT_NAME in json.dumps(v) for v in hooks.values()))
        self.assertEqual(build.cursor_hooks("py", Path("/k"))["stop"][0]["loop_limit"], 2)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_install(self, *extra: str) -> int:
        with redirect_stdout(io.StringIO()):
            return install.main(["--home", str(self.home), "--python", "/usr/bin/python3", *extra])

    def loc(self):
        return install.locations(self.home, windows=False)

    def test_dry_run_writes_nothing(self):
        self.assertEqual(self.run_install("--dry-run", "--cursor-model", "a", "--devin-model", "b"), 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_install_creates_verify_and_hooks_without_subagents(self):
        self.assertEqual(self.run_install("--cursor-model", "a", "--devin-model", "b"), 0)
        loc = self.loc()
        for key in ("cursor_hooks", "devin_config"):
            self.assertTrue(loc[key].exists(), key)
        self.assertFalse(loc["cursor_agent"].exists())
        self.assertFalse(loc["devin_agent"].exists())
        self.assertFalse(loc["claude_agent"].exists())
        self.assertTrue((loc["kit_home"] / "verifier_hooks.py").exists())
        self.assertTrue((loc["kit_home"] / "verify.py").exists())
        self.assertTrue((loc["kit_home"] / "protocol.headless.md").exists())
        manifest = json.loads((loc["kit_home"] / "install.json").read_text())
        self.assertEqual(manifest["models"], {"devin": "b", "cursor": "a"})
        self.assertFalse(manifest.get("with_subagents"))
        hooks = json.loads(loc["cursor_hooks"].read_text())
        self.assertIn("beforeShellExecution", hooks["hooks"])
        self.assertNotIn("subagentStart", hooks["hooks"])

    def test_merge_preserves_foreign_hooks_and_is_idempotent(self):
        loc = self.loc()
        loc["cursor_hooks"].parent.mkdir(parents=True)
        loc["cursor_hooks"].write_text(json.dumps({"version": 1, "hooks": {"stop": [{"command": "my-lint.sh"}]}}))
        loc["devin_config"].parent.mkdir(parents=True)
        loc["devin_config"].write_text(json.dumps({"theme": "dark", "hooks": {"Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "mine"}]}]}}))
        self.run_install()
        self.run_install()
        cursor = json.loads(loc["cursor_hooks"].read_text())
        self.assertEqual([e["command"] for e in cursor["hooks"]["stop"]][0], "my-lint.sh")
        self.assertEqual(len(cursor["hooks"]["stop"]), 2)  # foreign + ours, no duplicates after re-run
        devin = json.loads(loc["devin_config"].read_text())
        self.assertEqual(devin["theme"], "dark")
        self.assertEqual(len(devin["hooks"]["Stop"]), 2)
        self.assertTrue(list(loc["cursor_hooks"].parent.glob("hooks.json.bak-*")))

    def test_jsonc_config_requires_manual_merge(self):
        loc = self.loc()
        loc["devin_config"].parent.mkdir(parents=True)
        original = '{\n  // comentário\n  "theme": "dark"\n}\n'
        loc["devin_config"].write_text(original)
        self.assertEqual(self.run_install(), 3)
        self.assertEqual(loc["devin_config"].read_text(), original)
        self.assertTrue((loc["kit_home"] / "devin-hooks.snippet.json").exists())

    def test_uninstall_removes_only_ours(self):
        loc = self.loc()
        loc["cursor_hooks"].parent.mkdir(parents=True)
        loc["cursor_hooks"].write_text(json.dumps({"version": 1, "hooks": {"stop": [{"command": "my-lint.sh"}]}}))
        self.run_install("--platforms", "cursor,devin,claude", "--with-subagents")
        self.assertTrue(loc["claude_agent"].exists())
        self.run_install("--uninstall")
        for key in ("cursor_agent", "devin_agent", "claude_agent"):
            self.assertFalse(loc[key].exists(), key)
        self.assertFalse(loc["kit_home"].exists())
        cursor = json.loads(loc["cursor_hooks"].read_text())
        self.assertEqual(cursor["hooks"], {"stop": [{"command": "my-lint.sh"}]})

    def test_rejects_unknown_platform(self):
        with self.assertRaises(SystemExit):
            install.parse_args(["--platforms", "vscode"])


if __name__ == "__main__":
    unittest.main()
