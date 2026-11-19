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
from typing import Optional
from unittest import mock
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
        self._safe_path = f"{self.bin}{os.pathsep}/usr/bin{os.pathsep}/bin"
        os.environ["PATH"] = self._safe_path
        self.kit = Path(os.environ["DELPI_AGENT_KIT_HOME"])
        self.kit.mkdir(parents=True)
        (self.kit / "verifier_hooks.py").write_text(
            (KIT / "hooks" / "verifier_hooks.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (self.kit / "VERSION").write_text("0.3.1\n", encoding="utf-8")
        (self.kit / "protocol.headless.md").write_text(
            "# headless protocol\n\n## Formato do relatório (obrigatório)\n\nveredito: PLACEHOLDER\n",
            encoding="utf-8",
        )
        (self.kit / "report-format.md").write_text(
            "## Formato do relatório (obrigatório)\n\nDuplicata se anexado.\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "t@example.com"], cwd=self.repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "t"], cwd=self.repo, check=True, capture_output=True
        )
        (self.repo / "AGENTS.md").write_text(
            "## Verificação\n\n<!-- delpi-verifier:contract v1 -->\n", encoding="utf-8"
        )
        (self.repo / "a.txt").write_text("a\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.repo, check=True, capture_output=True)
        (self.repo / "a.txt").write_text("a2\n", encoding="utf-8")

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
            "version": "0.3.1",
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

    def orphan_marker_path(self) -> Path:
        return self.kit / "state" / ("verifier" + "-active.json")

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
        self._stub_devin_acp(self._write_fake_acp(chunk="veredito: ACCEPT\nresumo: ok"))
        self.stub("agent", "echo cursor-should-not-run; exit 1")
        with self._patch_devin_creds():
            code = verify.main(
                ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "auto"]
            )
        self.assertEqual(code, 0)

    def test_fallback_when_devin_absent(self):
        self.write_install(engines=["devin", "cursor"])
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
        ledger = self.repo / ".git" / "delpi-verifier" / "verdicts.jsonl"
        self.assertTrue(ledger.exists())
        last = json.loads(ledger.read_text(encoding="utf-8").strip().splitlines()[-1])
        self.assertEqual(last["verdict"], "INCONCLUSIVE")
        self.assertEqual(last.get("recorded_by"), "verify.py")

    def test_report_without_verdict_retries_then_inconclusive(self):
        self.write_install()
        counter = self.root / "calls.txt"
        self._stub_devin_acp(
            self._write_fake_acp(chunk="relatório sem linha de veredito"), count_file=counter
        )
        with self._patch_devin_creds():
            code = verify.main(
                ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "devin"]
            )
        self.assertEqual(code, 0)
        self.assertEqual(len(counter.read_text(encoding="utf-8").strip().splitlines()), 2)
        reports = list((self.repo / ".git" / "delpi-verifier" / "reports").glob("*.md"))
        text = reports[0].read_text(encoding="utf-8")
        self.assertIn("relatório fora do formato (2 tentativas)", text)
        self.assertIn("tentativas: 2", text)

    def test_retry_invalid_then_valid_uses_second(self):
        self.write_install()
        counter = self.root / "calls2.txt"
        fake = self._write_fake_acp(
            chunk=None,
            on_prompt=(
                f"n = len(Path('{counter}').read_text().splitlines()) if Path('{counter}').exists() else 0\n"
                "text = 'veredito: PASS\\nresumo: errado' if n < 2 else 'veredito: ACCEPT\\nresumo: ok'\n"
                "emit({'jsonrpc': '2.0', 'method': 'session/update', 'params': {'update': {'sessionUpdate': 'agent_message_chunk', 'content': {'text': text}}}})"
            ),
        )
        self._stub_devin_acp(fake, count_file=counter)
        with self._patch_devin_creds():
            code = verify.main(
                ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "devin"]
            )
        self.assertEqual(code, 0)
        self.assertEqual(len(counter.read_text(encoding="utf-8").strip().splitlines()), 2)
        reports = list((self.repo / ".git" / "delpi-verifier" / "reports").glob("*.md"))
        text = reports[0].read_text(encoding="utf-8")
        self.assertIn("veredito: ACCEPT", text)
        self.assertIn("tentativas: 2", text)

    def test_first_valid_verdict_single_launch(self):
        self.write_install()
        counter = self.root / "calls3.txt"
        self._stub_devin_acp(
            self._write_fake_acp(chunk="veredito: ACCEPT\nresumo: ok"), count_file=counter
        )
        with self._patch_devin_creds():
            code = verify.main(
                ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "devin"]
            )
        self.assertEqual(code, 0)
        self.assertEqual(len(counter.read_text(encoding="utf-8").strip().splitlines()), 1)
        reports = list((self.repo / ".git" / "delpi-verifier" / "reports").glob("*.md"))
        text = reports[0].read_text(encoding="utf-8")
        self.assertIn("veredito: ACCEPT", text)
        self.assertNotIn("tentativas:", text)

    def _write_fake_acp(
        self,
        name: str = "fake_acp.py",
        chunk: Optional[str] = "veredito: ACCEPT\nresumo: via acp",
        on_prompt: str = "",
    ) -> Path:
        chunk_emit = (
            "        emit({'jsonrpc': '2.0', 'method': 'session/update', 'params': {'update': "
            "{'sessionUpdate': 'agent_message_chunk', 'content': {'text': " + repr(chunk) + "}}}})\n"
            if chunk is not None
            else ""
        )
        extra = "".join("        " + line + "\n" for line in on_prompt.splitlines())
        path = self.root / name
        path.write_text(
            "import sys, json, os, time\n"
            "from pathlib import Path\n"
            "def emit(o): print(json.dumps(o), flush=True)\n"
            "for line in sys.stdin:\n"
            "    try: m = json.loads(line)\n"
            "    except json.JSONDecodeError: continue\n"
            "    req_id = m.get('id')\n"
            "    if req_id is None: continue\n"
            "    method = m.get('method')\n"
            "    result = {}\n"
            "    if method == 'session/new':\n"
            "        result = {'sessionId': 'fake-sess'}\n"
            "    elif method == 'session/prompt':\n"
            + extra
            + chunk_emit
            + "        result = {'stopReason': 'end_turn'}\n"
            "    emit({'jsonrpc': '2.0', 'id': req_id, 'result': result})\n",
            encoding="utf-8",
        )
        return path

    def _stub_devin_acp(self, fake: Path, count_file: Optional[Path] = None) -> Path:
        count = f'echo x >> "{count_file}"; ' if count_file else ""
        return self.stub(
            "devin",
            f'{count}if [ "$1" = "acp" ]; then exec python3 "{fake}"; fi\n'
            'echo "unexpected devin invocation" 1>&2; exit 1',
        )

    def _patch_devin_creds(self):
        return mock.patch.object(
            verify,
            "_devin_credentials",
            return_value={"api_key": "k", "api_server_url": "https://server.codeium.com"},
        )

    def test_devin_uses_acp_engine(self):
        self.write_install()
        self._stub_devin_acp(self._write_fake_acp())
        with self._patch_devin_creds():
            code = verify.main(
                ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "devin"]
            )
        self.assertEqual(code, 0)
        reports = list((self.repo / ".git" / "delpi-verifier" / "reports").glob("*.md"))
        text = reports[0].read_text(encoding="utf-8")
        self.assertIn("veredito: ACCEPT", text)
        self.assertIn("resumo: via acp", text)

    def test_devin_acp_engine_failure_inconclusive(self):
        self.write_install()
        fake_acp = self.root / "fake_acp_fail.py"
        fake_acp.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
        self._stub_devin_acp(fake_acp)
        with self._patch_devin_creds():
            verify.main(
                ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "devin"]
            )
        reports = list((self.repo / ".git" / "delpi-verifier" / "reports").glob("*.md"))
        text = reports[0].read_text(encoding="utf-8")
        self.assertIn("veredito: INCONCLUSIVE", text)
        self.assertIn("devin acp", text)

    def test_prompt_contains_report_format_once(self):
        self.write_install()
        fields = verify.parse_request(COMPLETE_REQUEST)
        prompt = verify.build_prompt(fields, self.repo, COMPLETE_REQUEST)
        self.assertEqual(prompt.count("## Formato do relatório"), 1)
        self.assertIn("PASS/FAIL são status de item, nunca veredito", prompt)
        self.assertIn("ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE", prompt)

    def test_env_active_during_run_without_global_marker(self):
        self.write_install()
        marker_log = self.root / "marker-log.txt"
        orphan_name = "verifier" + "-active.json"
        fake = self._write_fake_acp(
            on_prompt=(
                "home = Path(os.environ['DELPI_AGENT_KIT_HOME'])\n"
                f"marker = home / 'state' / '{orphan_name}'\n"
                f"Path('{marker_log}').write_text(json.dumps({{'marker': marker.exists(), 'env': os.environ.get('DELPI_VERIFIER_ACTIVE'), 'self_pid': os.getpid()}}))"
            ),
        )
        self._stub_devin_acp(fake)
        with self._patch_devin_creds():
            code = verify.main(
                ["--request-file", str(self.request_file()), "--repo", str(self.repo), "--engine", "devin"]
            )
        self.assertEqual(code, 0)
        data = json.loads(marker_log.read_text(encoding="utf-8"))
        self.assertFalse(data["marker"])
        self.assertEqual(data["env"], "1")
        self.assertFalse(self.orphan_marker_path().exists())

    def test_marker_not_written_on_timeout(self):
        self.write_install()
        self._stub_devin_acp(self._write_fake_acp(on_prompt="time.sleep(30)"))
        with self._patch_devin_creds():
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
        self.assertFalse(self.orphan_marker_path().exists())

    def test_sibling_session_allowed_while_verify_runs(self):
        self.write_install()
        ready = self.root / "ready"
        done = self.root / "done"
        fake = self._write_fake_acp(
            on_prompt=(
                f"Path('{ready}').touch()\n"
                f"while not Path('{done}').exists(): time.sleep(0.05)"
            ),
        )
        self._stub_devin_acp(fake)
        import threading

        result: dict = {}

        def run():
            with self._patch_devin_creds():
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
        self.assertFalse(self.orphan_marker_path().exists())

        hooks = KIT / "hooks" / "verifier_hooks.py"
        base_env = {k: v for k, v in os.environ.items() if k not in {"DELPI_VERIFIER_ACTIVE"}}
        base_env["DELPI_AGENT_KIT_HOME"] = str(self.kit)
        base_env["PATH"] = self._safe_path
        payload = json.dumps({"hook_event_name": "beforeShellExecution", "command": "touch x"})
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
        self.assertFalse(self.orphan_marker_path().exists())

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
        self.write_install()
        self._stub_devin_acp(self._write_fake_acp(chunk="veredito: ACCEPT\nresumo: unc"))
        pedido = self.request_file()
        rel = str(pedido.resolve()).lstrip("/")
        unc = f"\\\\wsl.localhost\\Ubuntu\\{rel.replace('/', chr(92))}"
        normalized = vh.normalize_agent_path(unc)
        self.assertEqual(normalized, pedido.resolve())
        with self._patch_devin_creds():
            code = verify.main(["--request-file", unc, "--repo", str(self.repo), "--engine", "devin"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
