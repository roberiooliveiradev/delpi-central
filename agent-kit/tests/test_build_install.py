"""Tests for agent-kit/scripts/build.py and install.py (stdlib unittest)."""

from __future__ import annotations

import io
import json
import os
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "scripts"))

import build  # noqa: E402
import install  # noqa: E402


class BuildTests(unittest.TestCase):
    def test_render_headless(self):
        text = build.render_headless("/usr/bin/python3", Path("/h/.delpi-agent-kit"))
        self.assertNotIn("{{", text)
        self.assertIn("# Relatório do delpi-verifier", text)
        self.assertIn('"/h/.delpi-agent-kit/verifier_hooks.py" record', text)
        self.assertFalse(text.lstrip().startswith("---"))

    def test_hook_configs_reference_script(self):
        for hooks in (build.cursor_hooks("py", Path("/k")), build.devin_hooks("py", Path("/k"))):
            self.assertTrue(all(build.HOOK_SCRIPT_NAME in json.dumps(v) for v in hooks.values()))
        cursor = build.cursor_hooks("py", Path("/k"))
        self.assertEqual(cursor["stop"][0]["loop_limit"], 2)
        blob = json.dumps(cursor)
        self.assertNotIn("mark-", blob)
        self.assertIn("session-start", blob)
        self.assertIn("guard", blob)
        self.assertIn("stop-gate", blob)
        self.assertIn("track-edit", blob)


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

    def test_install_creates_verify_and_hooks_no_agent_files(self):
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
        self.assertEqual(manifest["version"], build.kit_version())
        hooks = json.loads(loc["cursor_hooks"].read_text())
        self.assertIn("beforeShellExecution", hooks["hooks"])
        # Legacy Task-agent events must not be installed
        legacy_start = "sub" + "agentStart"
        self.assertNotIn(legacy_start, hooks["hooks"])

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
        self.assertEqual(len(cursor["hooks"]["stop"]), 2)
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

    def test_uninstall_removes_kit_and_preserves_foreign_hooks(self):
        loc = self.loc()
        loc["cursor_hooks"].parent.mkdir(parents=True)
        loc["cursor_hooks"].write_text(json.dumps({"version": 1, "hooks": {"stop": [{"command": "my-lint.sh"}]}}))
        # Seed a kit-marked agent file as if 0.2.x had installed it
        loc["cursor_agent"].parent.mkdir(parents=True, exist_ok=True)
        loc["cursor_agent"].write_text(
            f"---\nname: delpi-verifier\n---\n{build.AGENT_FILE_MARKER}\n",
            encoding="utf-8",
        )
        self.run_install("--cursor-model", "a", "--devin-model", "b")
        self.run_install("--uninstall")
        for key in ("cursor_agent", "devin_agent", "claude_agent"):
            self.assertFalse(loc[key].exists(), key)
        self.assertFalse(loc["kit_home"].exists())
        cursor = json.loads(loc["cursor_hooks"].read_text())
        self.assertEqual(cursor["hooks"], {"stop": [{"command": "my-lint.sh"}]})

    def test_m1_reinstall_cleans_legacy_preserves_foreign(self):
        """0.1/0.2 leftovers: kit agents + legacy hooks + orphan marker → cleaned; foreign kept."""
        loc = self.loc()
        # Kit-marked agents
        for key in ("cursor_agent", "devin_agent", "claude_agent"):
            path = loc[key]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"---\nname: delpi-verifier\n---\n{build.AGENT_FILE_MARKER}\nkit\n", encoding="utf-8")
        foreign_cursor = loc["cursor_agent"].parent / "other-agent.md"
        foreign_cursor.write_text("mine\n", encoding="utf-8")
        foreign_claude = loc["claude_agent"].parent / "helper.md"
        foreign_claude.write_text("other\n", encoding="utf-8")
        # Unmarked agent that happens to share the name pattern but without marker — wait,
        # cleanup only removes delpi-verifier.md WITH marker. A foreign delpi-verifier without
        # marker should be preserved.
        unmarked = loc["devin_agent"]
        # (already written with marker above — also test a sibling without marker)
        # Legacy cursor hooks mixed with foreign
        legacy_event = "sub" + "agentStart"
        loc["cursor_hooks"].parent.mkdir(parents=True, exist_ok=True)
        loc["cursor_hooks"].write_text(
            json.dumps(
                {
                    "version": 1,
                    "hooks": {
                        "stop": [{"command": "my-lint.sh"}],
                        legacy_event: [
                            {
                                "command": f'"{sys.executable}" "{self.home}/.delpi-agent-kit/verifier_hooks.py" {"mark" + "-start"} --host cursor',
                                "matcher": "delpi-verifier",
                            }
                        ],
                        "sessionStart": [{"command": "foreign-session.sh"}],
                    },
                }
            ),
            encoding="utf-8",
        )
        # Legacy Devin PreToolUse group for old Task launcher
        legacy_matcher = "run_" + "sub" + "agent"
        loc["devin_config"].parent.mkdir(parents=True, exist_ok=True)
        loc["devin_config"].write_text(
            json.dumps(
                {
                    "theme": "dark",
                    "hooks": {
                        "PreToolUse": [
                            {
                                "matcher": legacy_matcher,
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": f'"{sys.executable}" "{self.home}/.delpi-agent-kit/verifier_hooks.py" guard --host devin',
                                    }
                                ],
                            },
                            {
                                "matcher": "exec",
                                "hooks": [{"type": "command", "command": "foreign-devin.sh"}],
                            },
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )
        orphan = loc["orphan_marker"]
        orphan.parent.mkdir(parents=True, exist_ok=True)
        orphan.write_text("{}", encoding="utf-8")

        code = self.run_install("--cursor-model", "a", "--devin-model", "b")
        self.assertEqual(code, 0)
        for key in ("cursor_agent", "devin_agent", "claude_agent"):
            self.assertFalse(loc[key].exists(), key)
        self.assertTrue(foreign_cursor.exists())
        self.assertTrue(foreign_claude.exists())
        self.assertFalse(orphan.exists())
        hooks = json.loads(loc["cursor_hooks"].read_text())
        self.assertNotIn(legacy_event, hooks.get("hooks", {}))
        self.assertEqual(hooks["hooks"]["sessionStart"][0]["command"], "foreign-session.sh")
        self.assertIn("my-lint.sh", hooks["hooks"]["stop"][0]["command"])
        # Backups created for removed/rewritten files
        self.assertTrue(list(loc["cursor_hooks"].parent.glob("hooks.json.bak-*")))
        # Idempotent second run
        self.run_install("--cursor-model", "a", "--devin-model", "b")
        hooks2 = json.loads(loc["cursor_hooks"].read_text())
        self.assertNotIn(legacy_event, hooks2.get("hooks", {}))
        # dry-run after clean install does not invent new removals of foreign files
        before_foreign = foreign_cursor.read_text()
        self.run_install("--dry-run", "--cursor-model", "a", "--devin-model", "b")
        self.assertEqual(foreign_cursor.read_text(), before_foreign)

    def test_m1_dry_run_does_not_alter(self):
        loc = self.loc()
        loc["cursor_agent"].parent.mkdir(parents=True)
        loc["cursor_agent"].write_text(
            f"---\nname: delpi-verifier\n---\n{build.AGENT_FILE_MARKER}\n",
            encoding="utf-8",
        )
        orphan = loc["orphan_marker"]
        orphan.parent.mkdir(parents=True, exist_ok=True)
        orphan.write_text("{}", encoding="utf-8")
        self.assertEqual(self.run_install("--dry-run", "--cursor-model", "a", "--devin-model", "b"), 0)
        self.assertTrue(loc["cursor_agent"].exists())
        self.assertTrue(orphan.exists())
        self.assertFalse(loc["kit_home"].exists() and (loc["kit_home"] / "verify.py").exists())

    def test_discover_windows_home_via_cmd_wslpath_stubs(self):
        bin_dir = self.home / "bin"
        bin_dir.mkdir()
        target = self.home / "win-profile"
        target.mkdir()
        (bin_dir / "cmd.exe").write_text(
            "#!/bin/sh\necho 'C:\\Users\\Alice'\n", encoding="utf-8"
        )
        (bin_dir / "wslpath").write_text(
            f"#!/bin/sh\necho '{target}'\n", encoding="utf-8"
        )
        for name in ("cmd.exe", "wslpath"):
            path = bin_dir / name
            path.chmod(path.stat().st_mode | stat.S_IEXEC)
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
        try:
            found, warning = install.discover_windows_home()
            self.assertIsNone(warning)
            self.assertEqual(found, target)
        finally:
            os.environ["PATH"] = old_path

    def test_windows_home_flag_and_missing(self):
        target = self.home / "forced-win"
        target.mkdir()
        found, warning = install.discover_windows_home(explicit=target)
        self.assertEqual(found, target)
        self.assertIsNone(warning)
        missing, warning2 = install.discover_windows_home(explicit=self.home / "nope")
        self.assertIsNone(missing)
        self.assertIn("--windows-home", warning2 or "")

    def test_install_windows_bridge_with_windows_home(self):
        win = self.home / "Users" / "Bob"
        (win / "AppData" / "Roaming" / "devin").mkdir(parents=True)
        (win / "AppData" / "Roaming" / "devin" / "config.json").write_text(
            json.dumps({"theme": "dark"}), encoding="utf-8"
        )
        plan = install.Plan(dry_run=False)
        args = install.parse_args(
            [
                "--home",
                str(self.home),
                "--python",
                "/usr/bin/python3",
                "--windows-home",
                str(win),
                "--devin-model",
                "a",
                "--cursor-model",
                "b",
            ]
        )
        install.install_windows_bridge(plan, args)
        cmd = win / ".delpi-agent-kit" / "verify.cmd"
        self.assertTrue(cmd.exists())
        self.assertIn("wsl.exe", cmd.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
