"""Tests for agent-kit/scope/session_scope.py (stdlib unittest)."""

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
SCRIPT = KIT / "scope" / "session_scope.py"
sys.path.insert(0, str(KIT / "scope"))

import session_scope as ss  # noqa: E402


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, timeout=30,
    )


def make_repo(base: Path, name: str = "repo") -> Path:
    repo = base / name
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    (repo / "agent-scope.json").write_text(
        json.dumps({"require_lease": True, "overlap": "block",
                    "lease_ttl_hours": 1,
                    "contexts_file": "contexts.json"}), encoding="utf-8")
    (repo / "contexts.json").write_text(json.dumps({"contexts": {
        "app:a": {"globs": ["app-a/**"]},
        "app:b": {"globs": ["app-b/**"]},
        "sec": {"globs": ["sec/**"], "restricted": True},
    }}), encoding="utf-8")
    (repo / "seed.txt").write_text("seed", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "seed", "--no-verify")
    return repo


def cli(repo: Path, *args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("AGENT_SESSION", None)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=60,
        cwd=str(repo), env=env,
    )


class TestGlobMatching(unittest.TestCase):
    def m(self, pattern: str, path: str) -> bool:
        return bool(ss.glob_to_regex(pattern).match(path))

    def test_double_star(self):
        self.assertTrue(self.m("app/**", "app/a/b/c.py"))
        self.assertTrue(self.m("app/**", "app/a.py"))
        self.assertFalse(self.m("app/**", "app"))
        self.assertFalse(self.m("app/**", "app2/x.py"))

    def test_single_star_no_slash(self):
        self.assertTrue(self.m("*.md", "README.md"))
        self.assertFalse(self.m("*.md", "docs/x.md"))
        self.assertTrue(self.m("plugins/*/src/**", "plugins/tv/src/a/b.tsx"))
        self.assertFalse(self.m("plugins/*/src/**", "plugins/a/b/src/x.tsx"))

    def test_question_mark(self):
        self.assertTrue(self.m("a?c.py", "abc.py"))
        self.assertFalse(self.m("a?c.py", "a/c.py"))

    def test_overlap_heuristic(self):
        self.assertTrue(ss.globs_overlap("app/**", "app/x/**"))
        self.assertTrue(ss.globs_overlap("app/x/**", "app/**"))
        self.assertFalse(ss.globs_overlap("app/**", "other/**"))
        self.assertTrue(ss.globs_overlap("**", "app/**"))


class TestLeaseLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(Path(self.tmp.name))

    def test_register_and_status(self):
        r = cli(self.repo, "register", "--session", "s1",
                "--context", "app:a", "--path", "extra/**")
        self.assertEqual(r.returncode, 0, r.stderr)
        lease_file = self.repo / ".git" / "agent-scope" / "sessions" / "s1.json"
        self.assertTrue(lease_file.is_file())
        lease = json.loads(lease_file.read_text())
        self.assertEqual(sorted(lease["globs"]), ["app-a/**", "extra/**"])
        self.assertEqual(lease["worktree"], str(self.repo))

        r = cli(self.repo, "status")
        self.assertIn("s1", r.stdout)

    def test_register_restricted_requires_flag(self):
        r = cli(self.repo, "register", "--session", "s1", "--context", "sec")
        self.assertEqual(r.returncode, 2)
        self.assertIn("restrito", r.stderr)
        r = cli(self.repo, "register", "--session", "s1",
                "--context", "sec", "--allow-restricted")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_register_unknown_context(self):
        r = cli(self.repo, "register", "--session", "s1", "--context", "nope")
        self.assertEqual(r.returncode, 2)
        self.assertIn("desconhecido", r.stderr)

    def test_register_refuses_overwrite_without_amend(self):
        cli(self.repo, "register", "--session", "s1", "--context", "app:a")
        r = cli(self.repo, "register", "--session", "s1", "--context", "app:b")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--amend", r.stderr)
        r = cli(self.repo, "register", "--session", "s1",
                "--context", "app:b", "--amend")
        self.assertEqual(r.returncode, 0, r.stderr)
        lease = json.loads(
            (self.repo / ".git" / "agent-scope" / "sessions" / "s1.json").read_text())
        self.assertEqual(lease["globs"], ["app-b/**"])

    def test_register_expired_lease_can_be_taken(self):
        cli(self.repo, "register", "--session", "s1", "--context", "app:a")
        path = self.repo / ".git" / "agent-scope" / "sessions" / "s1.json"
        lease = json.loads(path.read_text())
        lease["expires"] = time.time() - 10
        path.write_text(json.dumps(lease))
        r = cli(self.repo, "register", "--session", "s1", "--context", "app:b")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_register_path_glob_respects_restricted(self):
        r = cli(self.repo, "register", "--session", "s1", "--path", "sec/x/**")
        self.assertEqual(r.returncode, 2)
        self.assertIn("restrita", r.stderr)
        r = cli(self.repo, "register", "--session", "s1",
                "--path", "sec/x/**", "--allow-restricted")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_release(self):
        cli(self.repo, "register", "--session", "s1", "--context", "app:a")
        r = cli(self.repo, "release", "--session", "s1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(cli(self.repo, "release", "--session", "s1").returncode, 1)

    def test_expire_removes_old_leases(self):
        cli(self.repo, "register", "--session", "s1", "--context", "app:a")
        path = self.repo / ".git" / "agent-scope" / "sessions" / "s1.json"
        lease = json.loads(path.read_text())
        lease["expires"] = time.time() - 10
        path.write_text(json.dumps(lease))
        r = cli(self.repo, "expire")
        self.assertEqual(r.returncode, 0)
        self.assertFalse(path.exists())

    def test_find_lease_by_env_session(self):
        cli(self.repo, "register", "--session", "a", "--context", "app:a")
        cli(self.repo, "register", "--session", "b", "--context", "app:b")
        lease = ss.find_lease(self.repo, self.repo, "b")
        self.assertEqual(lease["session"], "b")

    def test_register_warns_on_overlap(self):
        cli(self.repo, "register", "--session", "a", "--context", "app:a")
        r = cli(self.repo, "register", "--session", "b",
                "--path", "app-a/sub/**")
        self.assertEqual(r.returncode, 0)
        self.assertIn("AVISO", r.stderr)


class TestPreCommitHook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(Path(self.tmp.name))
        r = cli(self.repo, "install-hook")
        self.assertEqual(r.returncode, 0, r.stderr)
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        self.assertTrue(hook.is_file())
        self.assertTrue(os.access(hook, os.X_OK))

    def commit(self, path: str, content: str = "x") -> subprocess.CompletedProcess:
        f = self.repo / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        git(self.repo, "add", path)
        return git(self.repo, "commit", "-qm", "c")

    def test_disabled_without_config(self):
        (self.repo / "agent-scope.json").unlink()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "cfg")
        r = self.commit("anywhere/x.txt")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_blocks_without_lease(self):
        r = self.commit("app-a/x.txt")
        self.assertEqual(r.returncode, 1)
        self.assertIn("COMMIT BLOQUEADO", r.stderr)

    def test_allows_in_scope(self):
        cli(self.repo, "register", "--session", "s1", "--context", "app:a")
        r = self.commit("app-a/x.txt")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_blocks_out_of_scope(self):
        cli(self.repo, "register", "--session", "s1", "--context", "app:a")
        r = self.commit("app-b/x.txt")
        self.assertEqual(r.returncode, 1)
        self.assertIn("fora de qualquer escopo", r.stderr)

    def test_blocks_foreign_scope(self):
        cli(self.repo, "register", "--session", "s1", "--context", "app:a")
        cli(self.repo, "register", "--session", "s2", "--context", "app:b",
              "--worktree", str(self.repo / "wt2"))
        r = self.commit("app-b/x.txt")
        self.assertEqual(r.returncode, 1)
        self.assertIn("'s2'", r.stderr)

    def test_env_session_selects_lease(self):
        cli(self.repo, "register", "--session", "s1", "--context", "app:a")
        cli(self.repo, "register", "--session", "s2", "--context", "app:b",
              "--worktree", str(self.repo))
        env = {"AGENT_SESSION": "s2"}
        f = self.repo / "app-b" / "y.txt"
        f.parent.mkdir(exist_ok=True)
        f.write_text("y")
        git(self.repo, "add", "app-b/y.txt")
        r = subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-qm", "c"],
            capture_output=True, text=True,
            env={**os.environ, **env},
        )
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_uninstall_hook(self):
        r = cli(self.repo, "uninstall-hook")
        self.assertEqual(r.returncode, 0)
        self.assertFalse((self.repo / ".git" / "hooks" / "pre-commit").exists())
        self.assertEqual(self.commit("anywhere/x.txt").returncode, 0)


class TestAuditAndCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(Path(self.tmp.name))

    def test_check_flags_out_of_scope(self):
        (self.repo / "app-b").mkdir()
        (self.repo / "app-b" / "x.txt").write_text("x")
        cli(self.repo, "register", "--session", "s1", "--context", "app:a")
        r = cli(self.repo, "check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FORA", r.stdout)

    def test_audit_reports_unregistered_dirty(self):
        (self.repo / "app-a").mkdir()
        (self.repo / "app-a" / "x.txt").write_text("x")
        r = cli(self.repo, "audit", "--json")
        self.assertEqual(r.returncode, 1)
        report = json.loads(r.stdout)
        kinds = {v["kind"] for v in report["violations"]}
        self.assertIn("unregistered_dirty", kinds)

    def test_audit_clean_repo(self):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "all", "--no-verify")
        r = cli(self.repo, "audit", "--json")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_audit_linked_worktree(self):
        wt = Path(self.tmp.name) / "wt2"
        r = git(self.repo, "worktree", "add", "-q", str(wt), "-b", "wt2")
        self.assertEqual(r.returncode, 0, r.stderr)
        cli(wt, "register", "--session", "s-wt", "--context", "app:b")
        (wt / "app-b").mkdir()
        (wt / "app-b" / "ok.txt").write_text("x")
        (wt / "app-a").mkdir()
        (wt / "app-a" / "bad.txt").write_text("x")
        r = cli(self.repo, "audit", "--json")
        report = json.loads(r.stdout)
        rec = next(w for w in report["worktrees"] if w["worktree"] == str(wt))
        self.assertEqual(rec["session"], "s-wt")
        self.assertIn("app-a/bad.txt", rec["out_of_scope"])
        self.assertNotIn("app-b/ok.txt", rec["out_of_scope"])


if __name__ == "__main__":
    unittest.main()
