"""Tests for agent-kit/scripts/verify.py (stdlib unittest, no network, no real models)."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "scripts"))
sys.path.insert(0, str(KIT / "hooks"))

import verify  # noqa: E402
import verifier_hooks as vh  # noqa: E402


COMPLETE_REQUEST = textwrap.dedent(
    """\
    PEDIDO DE VERIFICAÇÃO
    objetivo: Adicionar cupom FRETEGRATIS.
    RQ-1: zera frete.
    AC-1: checkout_total com FRETEGRATIS == subtotal.
    escopo: working tree
    alegacoes: Alterei pricing e testes. unittest OK.
    modelo_executor: test-executor
    rodada: 1
    ordens_anteriores: nenhuma
    """
)


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self._old_home = os.environ.get("DELPI_AGENT_KIT_HOME")
        self._old_path = os.environ.get("PATH", "")
        os.environ["DELPI_AGENT_KIT_HOME"] = str(self.home / ".delpi-agent-kit")
        # Keep system bins for git/python; put stub bin first.
        self._safe_path = f"{self.bin}{os.pathsep}/usr/bin{os.pathsep}/bin"
        os.environ["PATH"] = self._safe_path
        self.kit = Path(os.environ["DELPI_AGENT_KIT_HOME"])
        self.kit.mkdir(parents=True)
        # Minimal hooks script for activate/clear/record/status
        (self.kit / "verifier_hooks.py").write_text(
            (KIT / "hooks" / "verifier_hooks.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (self.kit / "VERSION").write_text("0.2.0\n", encoding="utf-8")
        (self.kit / "protocol.headless.md").write_text(
            "# headless protocol\nveredito: PLACEHOLDER\n", encoding="utf-8"
        )
        (self.kit / "report-format.md").write_text("# Relatório\n", encoding="utf-8")
        subprocess.run(["git", "init"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=self.repo, check=True, capture_output=True)
        (self.repo / "AGENTS.md").write_text(
            "## Verificação\n\n<!-- delpi-verifier:contract v1 -->\n", encoding="utf-8"
        )
        (self.repo / "a.txt").write_text("a\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.repo, check=True, capture_output=True)
        (self.repo / "a.txt").write_text("a2\n", encoding="utf-8")  # dirty working tree

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("DELPI_AGENT_KIT_HOME", None)
        else:
            os.environ["DELPI_AGENT_KIT_HOME"] = self._old_home
        os.environ["PATH"] = self._old_path
        os.environ.pop("DELPI_VERIFIER_ACTIVE", None)
        self.tmp.cleanup()

    def write_install(self, engines=None, models=None, paths=None):
        data = {
            "version": "0.2.0",
            "engines": engines or ["devin", "cursor"],
            "models": models or {"devin": "swe-2-high", "cursor": "composer-2.5"},
            "timeout_sec": 5,
            "devin": {"permission_mode": "smart"},
            "paths": paths or {},
        }
        (self.kit / "install.json").write_text(json.dumps(data), encoding="utf-8")

    def stub(self, name: str, script: str) -> Path:
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + script + "\n", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
        return path

    def request_file(self, text: str = COMPLETE_REQUEST) -> Path:
        path = self.root / "pedido.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_incomplete_request_exit_2_without_launching(self):
        self.write_install()
        launched = self.root / "launched"
        self.stub("devin", f'echo launched > "{launched}"; echo should-not-run')
        bad = self.request_file("objetivo: x\nescopo: working tree\n")
        code = verify.main(["--request-file", str(bad), "--repo", str(self.repo), "--engine", "devin"])
        self.assertEqual(code, 2)
        self.assertFalse(launched.exists())

    def test_engine_order_devin_then_cursor(self):
        self.write_install(engines=["devin", "cursor"])
        self.stub(
            "devin",
            'printf "%s\\n" "# Relatório" "motor: ignored" "veredito: ACCEPT" "resumo: ok"',
        )
        self.stub("agent", 'echo cursor-should-not-run; exit 1')
        code = verify.main(
            ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "auto"]
        )
        self.assertEqual(code, 0)

    def test_fallback_when_devin_absent(self):
        self.write_install(engines=["devin", "cursor"])
        # No `devin` stub → absent; only cursor agent available.
        self.stub(
            "agent",
            'printf "%s\\n" "# Relatório" "veredito: ACCEPT" "resumo: cursor"',
        )
        code = verify.main(
            ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "auto"]
        )
        self.assertEqual(code, 0)
        reports = list((self.repo / ".git" / "delpi-verifier" / "reports").glob("*-cursor.md"))
        self.assertTrue(reports)
        self.assertIn("motor: cursor", reports[0].read_text(encoding="utf-8"))

    def test_no_engine_inconclusive_exit_3(self):
        self.write_install(engines=["devin", "cursor"], paths={})
        # PATH without agent/devin stubs (only system bins for git).
        empty = self.root / "empty"
        empty.mkdir()
        os.environ["PATH"] = f"{empty}{os.pathsep}/usr/bin{os.pathsep}/bin"
        code = verify.main(
            ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "auto"]
        )
        self.assertEqual(code, 3)
        reports = list((self.repo / ".git" / "delpi-verifier" / "reports").glob("*.md"))
        self.assertTrue(reports)
        text = reports[0].read_text(encoding="utf-8")
        self.assertIn("veredito: INCONCLUSIVE", text)
        self.assertIn("verificador indisponível", text)
        # Ledger filled
        ledger = self.repo / ".git" / "delpi-verifier" / "verdicts.jsonl"
        self.assertTrue(ledger.exists())
        last = json.loads(ledger.read_text(encoding="utf-8").strip().splitlines()[-1])
        self.assertEqual(last["verdict"], "INCONCLUSIVE")
        self.assertEqual(last.get("recorded_by"), "verify.py")

    def test_report_without_verdict_inconclusive(self):
        self.write_install()
        self.stub("devin", 'echo "relatório sem linha de veredito"')
        code = verify.main(
            ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "devin"]
        )
        self.assertEqual(code, 0)
        reports = list((self.repo / ".git" / "delpi-verifier" / "reports").glob("*.md"))
        self.assertTrue(any("relatório fora do formato" in r.read_text(encoding="utf-8") for r in reports))

    def test_marker_active_during_run_and_cleared(self):
        """AK-3: marker with PIDs + DELPI_VERIFIER_ACTIVE during run; cleared in finally."""
        self.write_install()
        marker_log = self.root / "marker-log.txt"
        self.stub(
            "devin",
            f'''
python3 - <<'PY'
import json, os
from pathlib import Path
home = Path(os.environ["DELPI_AGENT_KIT_HOME"])
marker = home / "state" / "verifier-active.json"
env = os.environ.get("DELPI_VERIFIER_ACTIVE")
payload = {{}}
if marker.exists():
    payload = json.loads(marker.read_text(encoding="utf-8"))
Path("{marker_log}").write_text(json.dumps({{
  "marker": marker.exists(),
  "env": env,
  "pids": payload.get("pids") or [],
  "self_pid": os.getpid(),
}}))
print("# Relatório")
print("veredito: ACCEPT")
PY
''',
        )
        code = verify.main(
            ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "devin"]
        )
        self.assertEqual(code, 0)
        data = json.loads(marker_log.read_text(encoding="utf-8"))
        self.assertTrue(data["marker"])
        self.assertEqual(data["env"], "1")
        self.assertTrue(isinstance(data["pids"], list) and len(data["pids"]) >= 1)
        self.assertIn(data["self_pid"], data["pids"])
        self.assertFalse((self.kit / "state" / "verifier-active.json").exists())

    def test_marker_cleared_on_timeout(self):
        self.write_install()
        self.stub("devin", "sleep 30")
        code = verify.main(
            [
                "--request-file",
                str(self.request_file()),
                "--repo",
                str(self.repo),
                "--engine",
                "devin",
                "--timeout",
                "1",
            ]
        )
        self.assertIn(code, (0, 1))
        self.assertFalse((self.kit / "state" / "verifier-active.json").exists())

    def test_sibling_session_allowed_while_verify_runs(self):
        """AK-3: marker may exist during verify; sibling without env/lineage still writes."""
        self.write_install()
        ready = self.root / "ready"
        done = self.root / "done"
        self.stub(
            "devin",
            f'''
touch "{ready}"
while [ ! -f "{done}" ]; do sleep 0.05; done
printf "%s\\n" "# Relatório" "veredito: ACCEPT"
''',
        )
        import threading

        result: dict = {}

        def run():
            result["code"] = verify.main(
                [
                    "--request-file",
                    str(self.request_file()),
                    "--repo",
                    str(self.repo),
                    "--engine",
                    "devin",
                    "--timeout",
                    "15",
                ]
            )

        thread = threading.Thread(target=run)
        thread.start()
        for _ in range(200):
            if ready.exists():
                break
            time.sleep(0.05)
        self.assertTrue(ready.exists(), "motor falso não sinalizou ready")
        # AK-3: marker present with PIDs; sibling without env/lineage still allowed
        self.assertTrue((self.kit / "state" / "verifier-active.json").exists())

        hooks = KIT / "hooks" / "verifier_hooks.py"
        base_env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"DELPI_VERIFIER_ACTIVE"}
        }
        base_env["DELPI_AGENT_KIT_HOME"] = str(self.kit)
        base_env["PATH"] = self._safe_path
        payload = json.dumps(
            {"hook_event_name": "beforeShellExecution", "command": "touch x"}
        )
        other = subprocess.run(
            [sys.executable, str(hooks), "guard", "--host", "cursor"],
            input=payload,
            capture_output=True,
            text=True,
            env=base_env,
            check=False,
        )
        self.assertEqual(other.returncode, 0, other.stdout + other.stderr)

        blocked_env = {**base_env, "DELPI_VERIFIER_ACTIVE": "1"}
        blocked = subprocess.run(
            [sys.executable, str(hooks), "guard", "--host", "cursor"],
            input=payload,
            capture_output=True,
            text=True,
            env=blocked_env,
            check=False,
        )
        self.assertEqual(blocked.returncode, 2, blocked.stdout + blocked.stderr)

        done.write_text("1", encoding="utf-8")
        thread.join(timeout=20)
        self.assertEqual(result.get("code"), 0)
        self.assertFalse((self.kit / "state" / "verifier-active.json").exists())

    def test_env_active_makes_guard_block(self):
        os.environ["DELPI_VERIFIER_ACTIVE"] = "1"
        self.assertTrue(vh.marker_active())
        reason = vh.classify_command("touch probe.txt")
        self.assertIsNotNone(reason)

    def test_normalize_agent_path_unc_and_drive(self):
        cases = [
            (r"\\wsl.localhost\Ubuntu\home\u\proj", "/home/u/proj"),
            (r"\\wsl$\Ubuntu\home\u\proj", "/home/u/proj"),
            ("//wsl.localhost/Ubuntu/home/u/proj", "/home/u/proj"),
            (r"C:\Users\u\proj", "/mnt/c/Users/u/proj"),
            ("C:/Users/u/proj", "/mnt/c/Users/u/proj"),
            ("/home/u/proj", "/home/u/proj"),
            ("D:\\data\\x", "/mnt/d/data/x"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(vh.normalize_agent_path(raw).as_posix(), expected)

    def test_request_file_unc_path(self):
        """OC-3: --request-file in UNC form that maps to a real Linux path under /home."""
        self.write_install()
        self.stub(
            "devin",
            'printf "%s\\n" "# Relatório" "veredito: ACCEPT" "resumo: unc"',
        )
        pedido = self.request_file()
        # Build a synthetic UNC that normalize_agent_path turns into the real pedido path.
        # \\wsl.localhost\Ubuntu + absolute linux path without leading slash in rest.
        rel = str(pedido.resolve()).lstrip("/")
        unc = f"\\\\wsl.localhost\\Ubuntu\\{rel.replace('/', chr(92))}"
        normalized = vh.normalize_agent_path(unc)
        self.assertEqual(normalized, pedido.resolve())
        code = verify.main(
            ["--request-file", unc, "--repo", str(self.repo), "--engine", "devin"]
        )
        self.assertEqual(code, 0)


class InstallSubagentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        sys.path.insert(0, str(KIT / "scripts"))
        import install as install_mod  # noqa: WPS433

        self.install = install_mod

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_removes_kit_subagents_preserves_foreign(self):
        loc = self.install.locations(self.home, windows=False)
        loc["cursor_agent"].parent.mkdir(parents=True)
        import build as build_mod  # noqa: WPS433

        loc["cursor_agent"].write_text(
            f"---\nname: delpi-verifier\n---\n{build_mod.AGENT_FILE_MARKER}\n",
            encoding="utf-8",
        )
        foreign = loc["cursor_agent"].parent / "other-agent.md"
        foreign.write_text("mine\n", encoding="utf-8")
        loc["cursor_hooks"].parent.mkdir(parents=True, exist_ok=True)
        loc["cursor_hooks"].write_text(
            json.dumps(
                {
                    "version": 1,
                    "hooks": {
                        "stop": [{"command": "my-lint.sh"}],
                        "subagentStart": [
                            {
                                "command": f'"{sys.executable}" "{self.home}/.delpi-agent-kit/verifier_hooks.py" mark-start --host cursor',
                                "matcher": "delpi-verifier",
                            }
                        ],
                    },
                }
            ),
            encoding="utf-8",
        )
        loc["devin_config"].parent.mkdir(parents=True, exist_ok=True)
        loc["devin_config"].write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
        code = self.install.main(
            [
                "--home",
                str(self.home),
                "--python",
                "/usr/bin/python3",
                "--devin-model",
                "swe-2-high",
                "--cursor-model",
                "composer-2.5",
            ]
        )
        self.assertEqual(code, 0)
        self.assertFalse(loc["cursor_agent"].exists())
        self.assertTrue(foreign.exists())
        hooks = json.loads(loc["cursor_hooks"].read_text(encoding="utf-8"))
        self.assertNotIn("subagentStart", hooks.get("hooks", {}))
        self.assertTrue((loc["kit_home"] / "verify.py").exists())
        manifest = json.loads((loc["kit_home"] / "install.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["models"]["devin"], "swe-2-high")
        self.assertFalse(manifest["with_subagents"])

    def test_with_subagents_installs_agent_file(self):
        code = self.install.main(
            [
                "--home",
                str(self.home),
                "--python",
                "/usr/bin/python3",
                "--with-subagents",
                "--cursor-model",
                "a",
                "--devin-model",
                "b",
            ]
        )
        self.assertEqual(code, 0)
        loc = self.install.locations(self.home, windows=False)
        self.assertTrue(loc["cursor_agent"].exists())
        hooks = json.loads(loc["cursor_hooks"].read_text(encoding="utf-8"))
        self.assertIn("subagentStart", hooks["hooks"])


if __name__ == "__main__":
    unittest.main()
