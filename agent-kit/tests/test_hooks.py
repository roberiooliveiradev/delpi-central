"""Tests for agent-kit/hooks/verifier_hooks.py (stdlib unittest)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
SCRIPT = KIT / "hooks" / "verifier_hooks.py"
sys.path.insert(0, str(KIT / "hooks"))

import verifier_hooks as vh  # noqa: E402

ALLOWED = [
    "pytest -q 2>&1 | tail -20",
    "python -m pytest tests/ -x",
    "python -m unittest discover -s tests",
    "cd api && python -m unittest -v",
    "npm test",
    "npm run test:unit",
    "pnpm run lint",
    "npx tsc --noEmit",
    "git status --short",
    "git diff HEAD~1..HEAD --stat",
    "git log --oneline -5",
    "git show abc123:src/a.py",
    "git -C /repo diff --name-only",
    "git branch --show-current",
    "git stash list",
    "git worktree list",
    "git config --get user.name",
    "grep -rn foo src | head",
    "find . -name '*.py' -exec grep -l foo {} +",
    "curl -s http://localhost/health",
    "curl -X GET http://x",
    "psql -c 'select count(*) from t'",
    "docker compose ps",
    "docker logs api --tail 50",
    "make test",
    "gh pr view 12",
    "gh api repos/o/r/pulls",
    "echo ok >/dev/null",
    "ls -la; wc -l README.md",
    "alembic current",
    '"/usr/bin/python3" "/home/u/.delpi-agent-kit/verifier_hooks.py" record --verdict ACCEPT --round 1 --summary "tudo ok"',
    '"/usr/bin/python3" "/home/u/.delpi-agent-kit/verifier_hooks.py" clear',
    '"/usr/bin/python3" "/home/u/.delpi-agent-kit/verify.py" --request-file /tmp/pedido.md',
]

BLOCKED = [
    "rm -rf build",
    "mv a b",
    "touch probe.txt",
    "python3 verify.py --request-file r.md > /tmp/out.txt",
    "cp /home/u/.delpi-agent-kit/verify.py /tmp/copy.py",
    "echo hi > f.txt",
    "echo hi >> f.txt",
    "cat <<EOF > f.txt",
    "git commit -m wip",
    "git push origin main",
    "git checkout -b x",
    "git reset --hard",
    "git stash",
    "git add -A",
    "git branch novo",
    "git config user.name x",
    "sed -i s/a/b/ f.py",
    "perl -pi -e 's/a/b/' f",
    "npm install",
    "npm ci",
    "npm run deploy:prod",
    "pip install requests",
    "python -m pip install x",
    "python -c \"open('f','w').write('x')\"",
    "node -e \"require('fs').writeFileSync('f','x')\"",
    "bash -c 'rm x'",
    "find . -name '*.tmp' -delete",
    "find . -exec rm {} +",
    "xargs rm < list.txt",
    "curl -X POST http://x",
    "curl -d a=1 http://x",
    "curl -o out.bin http://x",
    "wget http://x",
    "psql -c 'delete from t'",
    "psql -f migrate.sql",
    "docker compose up -d",
    "docker run --rm img",
    "alembic upgrade head",
    "python manage.py migrate",
    "make deploy",
    "gh pr merge 3",
    "gh api -X POST repos/o/r/issues",
    "ssh operador@host 'ls'",
    "./infra/scripts/up-prod-sequential.sh --build api",
    "echo $(rm x)",
    "echo `rm x`",
    "ls; mv a b",
    "sudo apt-get install x",
    "eval 'rm x'",
    "echo 'unbalanced",
]


class ClassifierTests(unittest.TestCase):
    def test_allowed_commands(self):
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertIsNone(vh.classify_command(command))

    def test_blocked_commands(self):
        for command in BLOCKED:
            with self.subTest(command=command):
                self.assertIsNotNone(vh.classify_command(command))

    def test_tool_calls(self):
        cases = [
            ({"tool_name": "Write", "tool_input": {"path": "a"}}, True),
            ({"tool_name": "StrReplace", "tool_input": {}}, True),
            ({"tool_name": "Delete", "tool_input": {}}, True),
            ({"tool_name": "Read", "tool_input": {"path": "a"}}, False),
            ({"tool_name": "Grep", "tool_input": {}}, False),
            ({"tool_name": "Task", "tool_input": {}}, True),
            ({"tool_name": "Shell", "tool_input": {"command": "pytest"}}, False),
            ({"tool_name": "Shell", "tool_input": {"command": "rm x"}}, True),
            ({"tool_name": "exec", "tool_input": {"command": "git status", "shell_id": "main"}}, False),
            ({"tool_name": "edit", "tool_input": {}}, True),
            ({"tool_name": "apply_patch", "tool_input": {}}, True),
            ({"tool_name": "Bash", "tool_input": {"command": "git push"}}, True),
            ({"tool_name": "mcp__clara__execute", "tool_input": {}}, True),
            ({"tool_name": "mcp__clara__read", "tool_input": {}}, False),
            ({"hook_event_name": "beforeShellExecution", "command": "npm install"}, True),
            ({"hook_event_name": "beforeShellExecution", "command": "npm test"}, False),
        ]
        for payload, blocked in cases:
            with self.subTest(payload=payload):
                self.assertEqual(vh.classify_tool_call(payload) is not None, blocked)

    def test_targets_verifier(self):
        self.assertTrue(vh.targets_verifier({"subagent_type": "delpi-verifier"}))
        self.assertFalse(vh.targets_verifier({"subagent_type": "explore"}))
        self.assertTrue(vh.targets_verifier({"tool_input": {"profile": "delpi-verifier", "prompt": "x"}}))
        self.assertFalse(vh.targets_verifier({"tool_input": {"profile": "general", "prompt": "chame o delpi-verifier depois"}}))
        self.assertTrue(vh.targets_verifier({"tool_input": {"prompt": "delpi-verifier"}}))


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class HookProcessTests(unittest.TestCase):
    """Run the script as the hosts do: JSON on stdin, decision on stdout/exit code."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.kit_home = base / "kit"
        self.repo = base / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "t@t")
        git(self.repo, "config", "user.name", "t")
        (self.repo / "AGENTS.md").write_text("# x\n\n<!-- delpi-verifier:contract v1 -->\n", encoding="utf-8")
        (self.repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        self.env = {**os.environ, "DELPI_AGENT_KIT_HOME": str(self.kit_home)}
        self.env.pop("DEVIN_PROJECT_DIR", None)
        self.env.pop("CLAUDE_PROJECT_DIR", None)
        # Hermetic to verify.py sessions: the launcher exports DELPI_VERIFIER_ACTIVE=1.
        self.env.pop("DELPI_VERIFIER_ACTIVE", None)

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, *args: str, payload: dict | None = None, cwd: Path | None = None):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=json.dumps(payload or {}),
            capture_output=True,
            text=True,
            env=self.env,
            cwd=str(cwd or self.repo),
        )
        return result

    def test_guard_inactive_allows_everything(self):
        r = self.run_hook("guard", "--host", "cursor", payload={"hook_event_name": "beforeShellExecution", "command": "rm -rf x"})
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout), {})

    def test_mark_start_records_parent_pid(self):
        """Legacy mark-start must record a durable host PID (getppid), not an empty list."""
        start = self.run_hook(
            "mark-start", "--host", "cursor", payload={"subagent_type": "delpi-verifier"}
        )
        self.assertEqual(start.returncode, 0)
        marker = self.kit_home / "state" / "verifier-active.json"
        self.assertTrue(marker.exists())
        data = json.loads(marker.read_text(encoding="utf-8"))
        # run_hook is a child of this test process → parent pid == test pid
        self.assertEqual(data.get("pids"), [os.getpid()])
        self.run_hook("mark-stop", "--host", "cursor", payload={"subagent_type": "delpi-verifier"})

    def test_mark_start_locks_lineage_frees_sibling(self):
        """OC R1: subagent lineage blocked by mark-start; unrelated session stays free."""
        if not vh.ancestry_check_available():
            self.skipTest("/proc ancestry unavailable")
        payload = json.dumps({"subagent_type": "delpi-verifier"})
        guard_payload = json.dumps(
            {"hook_event_name": "beforeShellExecution", "command": "touch probe"}
        )
        ready = self.repo / "mark-ready"
        done = self.repo / "mark-done"
        result = self.repo / "mark-guard-rc"
        for path in (ready, done, result):
            if path.exists():
                path.unlink()
        host_code = f"""
import json, os, subprocess, sys, time
from pathlib import Path
script = {str(SCRIPT)!r}
kit = {str(self.kit_home)!r}
ready, done, result = Path({str(ready)!r}), Path({str(done)!r}), Path({str(result)!r})
env = dict(os.environ)
env["DELPI_AGENT_KIT_HOME"] = kit
env.pop("DELPI_VERIFIER_ACTIVE", None)
r = subprocess.run(
    [sys.executable, script, "mark-start", "--host", "cursor"],
    input={payload!r},
    capture_output=True,
    text=True,
    env=env,
)
assert r.returncode == 0, r.stderr
ready.write_text(str(os.getpid()), encoding="utf-8")
for _ in range(400):
    if done.exists():
        break
    time.sleep(0.05)
g = subprocess.run(
    [sys.executable, script, "guard", "--host", "cursor"],
    input={guard_payload!r},
    capture_output=True,
    text=True,
    env=env,
)
result.write_text(str(g.returncode), encoding="utf-8")
"""
        host = subprocess.Popen([sys.executable, "-c", host_code], env=self.env)
        try:
            for _ in range(400):
                if ready.exists():
                    break
                time.sleep(0.05)
            self.assertTrue(ready.exists(), "host não sinalizou mark-start")
            host_pid = int(ready.read_text(encoding="utf-8").strip())
            marker = json.loads(
                (self.kit_home / "state" / "verifier-active.json").read_text(encoding="utf-8")
            )
            self.assertEqual(marker.get("pids"), [host_pid])
            # Sibling (this test process): not a descendant of host → allow
            sibling = self.run_hook(
                "guard",
                "--host",
                "cursor",
                payload={"hook_event_name": "beforeShellExecution", "command": "touch probe"},
            )
            self.assertEqual(sibling.returncode, 0, sibling.stdout + sibling.stderr)
            done.write_text("1", encoding="utf-8")
            host.wait(timeout=20)
            self.assertEqual(host.returncode, 0)
            self.assertEqual(result.read_text(encoding="utf-8").strip(), "2")
        finally:
            if host.poll() is None:
                host.kill()
                host.wait(timeout=5)
            self.run_hook("mark-stop", "--host", "cursor", payload={"subagent_type": "delpi-verifier"})

    def test_other_subagent_does_not_set_marker(self):
        self.run_hook("mark-start", "--host", "cursor", payload={"subagent_type": "explore"})
        r = self.run_hook("guard", "--host", "cursor", payload={"hook_event_name": "beforeShellExecution", "command": "touch probe"})
        self.assertEqual(r.returncode, 0)

    def test_mark_start_devin_locks_lineage_frees_sibling(self):
        """Same scoped lock for Devin host mark-start (legacy --with-subagents)."""
        if not vh.ancestry_check_available():
            self.skipTest("/proc ancestry unavailable")
        payload = json.dumps(
            {"tool_name": "run_subagent", "tool_input": {"profile": "delpi-verifier"}}
        )
        guard_payload = json.dumps(
            {"tool_name": "exec", "tool_input": {"command": "git commit -m x"}}
        )
        ready = self.repo / "devin-mark-ready"
        done = self.repo / "devin-mark-done"
        result = self.repo / "devin-mark-guard-rc"
        for path in (ready, done, result):
            if path.exists():
                path.unlink()
        host_code = f"""
import json, os, subprocess, sys, time
from pathlib import Path
script = {str(SCRIPT)!r}
kit = {str(self.kit_home)!r}
ready, done, result = Path({str(ready)!r}), Path({str(done)!r}), Path({str(result)!r})
env = dict(os.environ)
env["DELPI_AGENT_KIT_HOME"] = kit
env.pop("DELPI_VERIFIER_ACTIVE", None)
r = subprocess.run(
    [sys.executable, script, "mark-start", "--host", "devin"],
    input={payload!r},
    capture_output=True,
    text=True,
    env=env,
)
assert r.returncode == 0, r.stderr
ready.write_text(str(os.getpid()), encoding="utf-8")
for _ in range(400):
    if done.exists():
        break
    time.sleep(0.05)
g = subprocess.run(
    [sys.executable, script, "guard", "--host", "devin"],
    input={guard_payload!r},
    capture_output=True,
    text=True,
    env=env,
)
result.write_text(str(g.returncode), encoding="utf-8")
"""
        host = subprocess.Popen([sys.executable, "-c", host_code], env=self.env)
        try:
            for _ in range(400):
                if ready.exists():
                    break
                time.sleep(0.05)
            self.assertTrue(ready.exists())
            sibling = self.run_hook(
                "guard",
                "--host",
                "devin",
                payload={"tool_name": "exec", "tool_input": {"command": "git commit -m x"}},
            )
            self.assertEqual(sibling.returncode, 0, sibling.stdout + sibling.stderr)
            done.write_text("1", encoding="utf-8")
            host.wait(timeout=20)
            self.assertEqual(host.returncode, 0)
            self.assertEqual(result.read_text(encoding="utf-8").strip(), "2")
        finally:
            if host.poll() is None:
                host.kill()
                host.wait(timeout=5)
            self.run_hook(
                "mark-stop",
                "--host",
                "devin",
                payload={"tool_name": "run_subagent", "tool_input": {"profile": "delpi-verifier"}},
            )

    def test_stale_marker_expires(self):
        (self.kit_home / "state").mkdir(parents=True)
        (self.kit_home / "state" / "verifier-active.json").write_text(
            json.dumps({"started_at": time.time() - 99999, "pids": [os.getpid()]})
        )
        r = self.run_hook("guard", "--host", "cursor", payload={"hook_event_name": "beforeShellExecution", "command": "touch x"})
        self.assertEqual(r.returncode, 0)

    def test_guard_always_claude(self):
        r = self.run_hook("guard", "--host", "claude", "--always", payload={"tool_name": "Bash", "tool_input": {"command": "git push"}})
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_guard_unreadable_payload_fails_closed_when_active(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "guard", "--host", "claude", "--always"], input="not json",
                           capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 2)

    def test_env_active_blocks_with_or_without_marker(self):
        env = {**self.env, "DELPI_VERIFIER_ACTIVE": "1"}
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "guard", "--host", "cursor"],
            input=json.dumps({"hook_event_name": "beforeShellExecution", "command": "touch probe"}),
            capture_output=True,
            text=True,
            env=env,
            cwd=str(self.repo),
        )
        self.assertEqual(r.returncode, 2)
        out = json.loads(r.stdout)
        self.assertEqual(out["permission"], "deny")
        self.assertIn("DELPI_VERIFIER_ACTIVE", out["agent_message"])

    def test_lineage_pid_blocks_descendant_sibling_free(self):
        """Marker with live PID: descendants blocked; non-descendants free."""
        if not vh.ancestry_check_available():
            self.skipTest("/proc ancestry unavailable")
        parent_pid = os.getpid()
        vh_env = {**self.env}
        act = subprocess.run(
            [sys.executable, str(SCRIPT), "activate", "--host", "verify", "--pids", str(parent_pid)],
            capture_output=True,
            text=True,
            env=vh_env,
        )
        self.assertEqual(act.returncode, 0, act.stderr)
        child_script = (
            "import json, os, sys\n"
            f"sys.path.insert(0, {str(SCRIPT.parent)!r})\n"
            "import verifier_hooks as vh\n"
            "blocked, why = vh.guard_decision()\n"
            "print(json.dumps({'blocked': blocked, 'why': why}))\n"
        )
        child = subprocess.run(
            [sys.executable, "-c", child_script],
            capture_output=True,
            text=True,
            env=vh_env,
        )
        self.assertEqual(child.returncode, 0, child.stderr)
        data = json.loads(child.stdout.strip().splitlines()[-1])
        self.assertTrue(data["blocked"], data)
        self.assertIn("ancestralidade", data["why"])
        sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], env=vh_env)
        try:
            subprocess.run(
                [sys.executable, str(SCRIPT), "activate", "--host", "verify", "--pids", str(sleeper.pid)],
                capture_output=True,
                text=True,
                env=vh_env,
                check=False,
            )
            sibling_guard = self.run_hook(
                "guard",
                "--host",
                "cursor",
                payload={"hook_event_name": "beforeShellExecution", "command": "touch probe"},
            )
            self.assertEqual(sibling_guard.returncode, 0, sibling_guard.stdout + sibling_guard.stderr)
        finally:
            sleeper.kill()
            sleeper.wait(timeout=5)
            subprocess.run([sys.executable, str(SCRIPT), "clear"], capture_output=True, env=vh_env)

    def test_dead_pid_clears_marker_and_allows(self):
        (self.kit_home / "state").mkdir(parents=True, exist_ok=True)
        dead_pid = 2_000_000_001
        (self.kit_home / "state" / "verifier-active.json").write_text(
            json.dumps(
                {
                    "started_at": time.time(),
                    "host": "verify",
                    "session": "verify.py",
                    "pids": [dead_pid],
                }
            ),
            encoding="utf-8",
        )
        r = self.run_hook(
            "guard",
            "--host",
            "cursor",
            payload={"hook_event_name": "beforeShellExecution", "command": "touch probe"},
        )
        self.assertEqual(r.returncode, 0)
        self.assertFalse((self.kit_home / "state" / "verifier-active.json").exists())

    def test_status_reports_session_block_state(self):
        env = {**self.env, "DELPI_VERIFIER_ACTIVE": "1"}
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "status", "--repo", str(self.repo)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(self.repo),
        )
        self.assertEqual(r.returncode, 0)
        info = json.loads(r.stdout)
        self.assertTrue(info["env_DELPI_VERIFIER_ACTIVE"])
        self.assertTrue(info["this_session_blocked"])
        self.assertIn("DELPI_VERIFIER_ACTIVE", info["this_session_reason"] or "")

    def session(self, host: str):
        key = "conversation_id" if host == "cursor" else "session_id"
        payload = {key: "s1", "workspace_roots": [str(self.repo)]} if host == "cursor" else {key: "s1", "cwd": str(self.repo)}
        return payload

    def test_stop_gate_flow_cursor(self):
        payload = self.session("cursor")
        self.run_hook("session-start", "--host", "cursor", payload=payload)
        self.run_hook("track-edit", "--host", "cursor", payload=payload)
        self.assertEqual(json.loads(self.run_hook("stop-gate", "--host", "cursor", payload=payload).stdout), {})
        (self.repo / "app.py").write_text("x = 2\n", encoding="utf-8")
        nag = json.loads(self.run_hook("stop-gate", "--host", "cursor", payload=payload).stdout)
        self.assertIn("followup_message", nag)
        self.assertIn("delpi-verifier", nag["followup_message"])
        rec = self.run_hook("record", "--verdict", "REWORK", "--round", "1", "--summary", "falta AC-2")
        self.assertEqual(rec.returncode, 0, rec.stderr)
        nag = json.loads(self.run_hook("stop-gate", "--host", "cursor", payload=payload).stdout)
        self.assertIn("rodada 2", nag["followup_message"])
        self.run_hook("record", "--verdict", "ACCEPT", "--round", "2")
        self.assertEqual(json.loads(self.run_hook("stop-gate", "--host", "cursor", payload=payload).stdout), {})
        (self.repo / "app.py").write_text("x = 3\n", encoding="utf-8")
        self.assertIn("followup_message", json.loads(self.run_hook("stop-gate", "--host", "cursor", payload=payload).stdout))
        looped = {**payload, "loop_count": 2}
        self.assertEqual(json.loads(self.run_hook("stop-gate", "--host", "cursor", payload=looped).stdout), {})

    def test_stop_gate_rework_round_three_releases(self):
        payload = self.session("cursor")
        self.run_hook("session-start", "--host", "cursor", payload=payload)
        self.run_hook("track-edit", "--host", "cursor", payload=payload)
        (self.repo / "app.py").write_text("x = 9\n", encoding="utf-8")
        self.run_hook("record", "--verdict", "REWORK", "--round", "3")
        self.assertEqual(json.loads(self.run_hook("stop-gate", "--host", "cursor", payload=payload).stdout), {})

    def test_stop_gate_devin(self):
        payload = self.session("devin")
        self.run_hook("session-start", "--host", "devin", payload=payload)
        self.run_hook("track-edit", "--host", "devin", payload=payload)
        (self.repo / "new.py").write_text("y = 1\n", encoding="utf-8")
        r = self.run_hook("stop-gate", "--host", "devin", payload=payload)
        self.assertEqual(json.loads(r.stdout)["decision"], "block")
        r = self.run_hook("stop-gate", "--host", "devin", payload={**payload, "stop_hook_active": True})
        self.assertEqual(r.stdout.strip(), "")
        self.run_hook("record", "--verdict", "SKIPPED", "--round", "0", "--summary", "só docs")
        r = self.run_hook("stop-gate", "--host", "devin", payload=payload)
        self.assertEqual(r.stdout.strip(), "")

    def test_stop_gate_needs_contract(self):
        (self.repo / "AGENTS.md").write_text("# sem contrato\n", encoding="utf-8")
        git(self.repo, "commit", "-qam", "drop contract")
        payload = self.session("cursor")
        self.run_hook("session-start", "--host", "cursor", payload=payload)
        self.run_hook("track-edit", "--host", "cursor", payload=payload)
        (self.repo / "app.py").write_text("x = 5\n", encoding="utf-8")
        self.assertEqual(json.loads(self.run_hook("stop-gate", "--host", "cursor", payload=payload).stdout), {})

    def test_stop_gate_ignores_changes_from_other_agents(self):
        payload = self.session("cursor")
        self.run_hook("session-start", "--host", "cursor", payload=payload)
        (self.repo / "app.py").write_text("x = 8\n", encoding="utf-8")  # changed outside this session's tools
        self.assertEqual(json.loads(self.run_hook("stop-gate", "--host", "cursor", payload=payload).stdout), {})

    def test_stop_gate_without_baseline_passes(self):
        (self.repo / "app.py").write_text("x = 7\n", encoding="utf-8")
        self.assertEqual(json.loads(self.run_hook("stop-gate", "--host", "cursor", payload=self.session("cursor")).stdout), {})

    def test_cache_dirs_do_not_change_fingerprint(self):
        before = vh.fingerprint(self.repo)
        (self.repo / ".pytest_cache").mkdir()
        (self.repo / ".pytest_cache" / "v").write_text("x", encoding="utf-8")
        self.assertEqual(before, vh.fingerprint(self.repo))
        (self.repo / "novo.py").write_text("z = 1\n", encoding="utf-8")
        self.assertNotEqual(before, vh.fingerprint(self.repo))

    def test_record_rejects_unknown_verdict(self):
        r = self.run_hook("record", "--verdict", "LGTM")
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
