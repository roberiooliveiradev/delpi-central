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
]

BLOCKED = [
    "rm -rf build",
    "mv a b",
    "touch probe.txt",
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

    def test_marker_lifecycle_cursor(self):
        start = self.run_hook("mark-start", "--host", "cursor", payload={"subagent_type": "delpi-verifier"})
        self.assertEqual(start.returncode, 0)
        blocked = self.run_hook("guard", "--host", "cursor", payload={"hook_event_name": "beforeShellExecution", "command": "touch probe"})
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(json.loads(blocked.stdout)["permission"], "deny")
        allowed = self.run_hook("guard", "--host", "cursor", payload={"hook_event_name": "beforeShellExecution", "command": "pytest -q"})
        self.assertEqual(allowed.returncode, 0)
        self.run_hook("mark-stop", "--host", "cursor", payload={"subagent_type": "delpi-verifier"})
        after = self.run_hook("guard", "--host", "cursor", payload={"hook_event_name": "beforeShellExecution", "command": "touch probe"})
        self.assertEqual(after.returncode, 0)

    def test_other_subagent_does_not_set_marker(self):
        self.run_hook("mark-start", "--host", "cursor", payload={"subagent_type": "explore"})
        r = self.run_hook("guard", "--host", "cursor", payload={"hook_event_name": "beforeShellExecution", "command": "touch probe"})
        self.assertEqual(r.returncode, 0)

    def test_marker_lifecycle_devin(self):
        self.run_hook("mark-start", "--host", "devin", payload={"tool_name": "run_subagent", "tool_input": {"profile": "delpi-verifier"}})
        r = self.run_hook("guard", "--host", "devin", payload={"tool_name": "exec", "tool_input": {"command": "git commit -m x"}})
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["decision"], "block")
        self.run_hook("mark-stop", "--host", "devin", payload={"tool_name": "run_subagent", "tool_input": {"profile": "delpi-verifier"}})
        r = self.run_hook("guard", "--host", "devin", payload={"tool_name": "exec", "tool_input": {"command": "git commit -m x"}})
        self.assertEqual(r.returncode, 0)

    def test_stale_marker_expires(self):
        (self.kit_home / "state").mkdir(parents=True)
        (self.kit_home / "state" / "verifier-active.json").write_text(json.dumps({"started_at": time.time() - 99999}))
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
