"""P2.2h.2l: hermetic + disposable real Git checkout observer tests.

Only scratch Git repositories under pytest tmp_path are mutated by test
setup; observer commands remain read-only, without a Docker socket, Core,
production checkout, network, journal writes or deployment.
"""
from __future__ import annotations

import subprocess
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from linux_ops_mcp.deploy_git_checkout_readonly import (
    GitCheckoutReadError, GitCheckoutReadOnlyObserver,
)
from linux_ops_mcp.deploy_host_source import RuntimeTarget

NOW = datetime(2026, 11, 16, 22, 30, tzinfo=timezone.utc)
COMMIT = "a" * 40
TARGET = RuntimeTarget(
    environment="hml", service_id="public-hub", host_id="srv-api-pilot",
    compose_project="delpi-hml", container_name="delpi-hml-public-hub",
)


def expect_failure(code, action):
    with pytest.raises(GitCheckoutReadError) as caught:
        action()
    assert caught.value.code == code
    assert "/fake/private" not in str(caught.value)


class FakeGit:
    def __init__(self, root, *, branch="main", head=COMMIT,
                 changed="", fail=None, raise_exc=None, change_head=False):
        self.root = root
        self.branch = branch
        self.head = head
        self.changed = changed
        self.fail = fail
        self.raise_exc = raise_exc
        self.change_head = change_head
        self.calls = []
        self.head_reads = 0

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), kwargs))
        if self.raise_exc:
            raise self.raise_exc
        suffix = argv[argv.index("core.hooksPath=/dev/null") + 1:]
        label = " ".join(suffix)
        if self.fail == label:
            return subprocess.CompletedProcess(argv, 1, "", "/fake/private")
        if suffix == ["rev-parse", "--show-toplevel"]:
            value = str(self.root) + "\n"
        elif suffix == ["symbolic-ref", "--quiet", "--short", "HEAD"]:
            value = self.branch + "\n"
        elif suffix == ["rev-parse", "--verify", "HEAD^{commit}"]:
            self.head_reads += 1
            value = ("b" * 40 if self.change_head and self.head_reads > 1
                     else self.head) + "\n"
        elif suffix == [
            "status", "--porcelain=v1", "-z",
            "--untracked-files=all", "--ignore-submodules=none",
        ]:
            value = self.changed
        else:
            raise AssertionError(f"Unexpected Git read command {label}")
        return subprocess.CompletedProcess(argv, 0, value, "")


def scratch(tmp_path):
    root = tmp_path / "trusted-checkout"
    root.mkdir()
    (root / ".git").mkdir()
    return root


def fake_observer(root, fake, *, clock=lambda: NOW):
    return GitCheckoutReadOnlyObserver(
        checkout_root=root, run_command=fake, clock=clock,
    )


def test_clean_checkout_is_observed_but_never_eligible_for_prepare(tmp_path):
    root = scratch(tmp_path)
    fake = FakeGit(root)
    result = fake_observer(root, fake).read(target=TARGET)
    assert result.head_sha == COMMIT
    assert result.branch == "main"
    assert result.tracked_and_untracked_clean is True
    assert result.status == "inspection_only_blocked"
    assert result.blocks == ("GIT_CHECKOUT_NOT_HOST_ATTESTED",)
    assert not result.checkout_attested
    assert not result.challenge_bound
    assert not result.rollback_ready
    assert not result.prepare_eligible
    assert result.observed_at == NOW
    assert len(fake.calls) == 7
    for argv, kwargs in fake.calls:
        assert argv[:2] == ["git", "--no-optional-locks"]
        assert argv[argv.index("-C") + 1] == str(root)
        assert "core.fsmonitor=false" in argv
        assert "core.untrackedCache=false" in argv
        assert "core.hooksPath=/dev/null" in argv
        assert "--" not in argv[:2]
        assert kwargs["check"] is False
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["timeout"] == 5
        assert "shell" not in kwargs
        assert kwargs["env"]["GIT_OPTIONAL_LOCKS"] == "0"
        assert kwargs["env"]["GIT_CONFIG_NOSYSTEM"] == "1"
        assert kwargs["env"]["GIT_CONFIG_GLOBAL"] == "/dev/null"
        assert kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"
        assert "GIT_SSH_COMMAND" not in kwargs["env"]
        assert "GH_TOKEN" not in kwargs["env"]
        assert not any(x in argv for x in ("reset", "fetch", "pull", "checkout", "push"))


@pytest.mark.parametrize("branch,dirty,reasons", [
    ("feature", "", ("GIT_CHECKOUT_NOT_ON_MAIN",)),
    ("main", "?? password.txt\0", ("GIT_CHECKOUT_DIRTY",)),
    ("feature", " M app.py\0", ("GIT_CHECKOUT_NOT_ON_MAIN", "GIT_CHECKOUT_DIRTY")),
])
def test_unexpected_branch_or_tracked_untracked_changes_keep_blocked(
    tmp_path, branch, dirty, reasons,
):
    root = scratch(tmp_path)
    report = fake_observer(root, FakeGit(root, branch=branch, changed=dirty)).read(
        target=TARGET,
    )
    assert report.status == "inspection_only_blocked"
    assert report.tracked_and_untracked_clean is (not bool(dirty))
    assert report.blocks[1:] == reasons
    assert not report.checkout_attested


@pytest.mark.parametrize("changes,code", [
    ({"environment": "dev"}, "GIT_CHECKOUT_TARGET_INVALID"),
    ({"service_id": "db"}, "GIT_CHECKOUT_TARGET_NOT_ALLOWLISTED"),
    ({"container_name": "another"}, "GIT_CHECKOUT_TARGET_NOT_ALLOWLISTED"),
    ({"compose_project": "another"}, "GIT_CHECKOUT_TARGET_NOT_ALLOWLISTED"),
])
def test_unallowed_target_denied_before_git(tmp_path, changes, code):
    root = scratch(tmp_path)
    fake = FakeGit(root)
    expect_failure(
        code, lambda: fake_observer(root, fake).read(
            target=replace(TARGET, **changes),
        ),
    )
    assert fake.calls == []


def test_invalid_checkout_directory_or_external_gitdir_denied(tmp_path):
    missing = tmp_path / "missing"
    git = FakeGit(missing)
    expect_failure(
        "GIT_CHECKOUT_PATH_INVALID",
        lambda: fake_observer(missing, git).read(target=TARGET),
    )
    assert git.calls == []
    root = tmp_path / "just-folder"
    root.mkdir()
    expect_failure(
        "GIT_CHECKOUT_METADATA_INVALID",
        lambda: fake_observer(root, git).read(target=TARGET),
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / ".git").symlink_to(outside, target_is_directory=True)
    expect_failure(
        "GIT_CHECKOUT_METADATA_INVALID",
        lambda: fake_observer(root, git).read(target=TARGET),
    )
    assert git.calls == []


def test_symlink_checkout_root_denied_without_git(tmp_path):
    root = scratch(tmp_path)
    shortcut = tmp_path / "shortcut"
    shortcut.symlink_to(root, target_is_directory=True)
    fake = FakeGit(root)
    expect_failure(
        "GIT_CHECKOUT_PATH_INVALID",
        lambda: fake_observer(shortcut, fake).read(target=TARGET),
    )
    assert fake.calls == []


def test_git_head_changed_during_snapshot_is_fail_closed(tmp_path):
    root = scratch(tmp_path)
    fake = FakeGit(root, change_head=True)
    expect_failure(
        "GIT_CHECKOUT_CHANGED_DURING_READ",
        lambda: fake_observer(root, fake).read(target=TARGET),
    )


def test_unexpected_head_shape_never_returns_clean_state(tmp_path):
    root = scratch(tmp_path)
    fake = FakeGit(root, head="HEAD")
    expect_failure(
        "GIT_CHECKOUT_HEAD_INVALID",
        lambda: fake_observer(root, fake).read(target=TARGET),
    )


def test_git_nonzero_code_is_sanitized(tmp_path):
    root = scratch(tmp_path)
    fake = FakeGit(root, fail="rev-parse --show-toplevel")
    expect_failure(
        "GIT_CHECKOUT_COMMAND_FAILED",
        lambda: fake_observer(root, fake).read(target=TARGET),
    )


@pytest.mark.parametrize("exc", [
    FileNotFoundError("private client path"),
    subprocess.TimeoutExpired(["git"], 5),
    subprocess.SubprocessError("private configuration"),
])
def test_git_missing_timeout_or_failure_is_sanitized(tmp_path, exc):
    root = scratch(tmp_path)
    fake = FakeGit(root, raise_exc=exc)
    expect_failure(
        "GIT_CHECKOUT_COMMAND_UNAVAILABLE",
        lambda: fake_observer(root, fake).read(target=TARGET),
    )


def test_oversize_status_is_rejected_without_returning_file_list(tmp_path):
    root = scratch(tmp_path)
    fake = FakeGit(root, changed="?? file.txt\0" * 10000)
    expect_failure(
        "GIT_CHECKOUT_OUTPUT_TOO_LARGE",
        lambda: fake_observer(root, fake).read(target=TARGET),
    )


def test_unaware_clock_denied_before_git(tmp_path):
    root = scratch(tmp_path)
    fake = FakeGit(root)
    for clock in (lambda: NOW.replace(tzinfo=None), lambda: "now"):
        expect_failure(
            "GIT_CHECKOUT_CLOCK_INVALID",
            lambda: fake_observer(root, fake, clock=clock).read(target=TARGET),
        )
    assert fake.calls == []


def _isolated_git(root, *args):
    environment = {
        "PATH": "/usr/bin:/bin", "HOME": "/nonexistent",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
    }
    result = subprocess.run(
        ["git", "-C", str(root), *args], env=environment,
        check=True, capture_output=True, text=True, timeout=10,
    )
    return result.stdout


def test_real_git_clean_dirty_untracked_and_branch_in_disposable_temp_repo(tmp_path):
    root = tmp_path / "git-fixture"
    root.mkdir()
    _isolated_git(root, "init", "-q", "-b", "main")
    (root / "tracked.txt").write_text("clean\n", encoding="utf-8")
    _isolated_git(root, "add", "tracked.txt")
    _isolated_git(
        root, "-c", "user.name=Test",
        "-c", "user.email=ci@example.invalid",
        "commit", "-q", "-m", "synthetic commit",
    )
    observer = GitCheckoutReadOnlyObserver(checkout_root=root, clock=lambda: NOW)
    clean = observer.read(target=TARGET)
    assert clean.branch == "main"
    assert clean.tracked_and_untracked_clean
    assert clean.head_sha == _isolated_git(root, "rev-parse", "HEAD").strip()
    assert not clean.checkout_attested and not clean.prepare_eligible

    (root / "tracked.txt").write_text("modified\n", encoding="utf-8")
    dirty = observer.read(target=TARGET)
    assert not dirty.tracked_and_untracked_clean
    assert "GIT_CHECKOUT_DIRTY" in dirty.blocks

    _isolated_git(root, "restore", "tracked.txt")
    (root / "untracked.txt").write_text("extra\n", encoding="utf-8")
    untracked = observer.read(target=TARGET)
    assert "GIT_CHECKOUT_DIRTY" in untracked.blocks

    (root / "untracked.txt").unlink()
    _isolated_git(root, "branch", "another")
    _isolated_git(root, "switch", "another")
    other_branch = observer.read(target=TARGET)
    assert other_branch.tracked_and_untracked_clean
    assert "GIT_CHECKOUT_NOT_ON_MAIN" in other_branch.blocks


def test_module_never_exposes_mcp_or_deployment_controls():
    src = (
        Path(__file__).resolve().parents[1]
        / "linux_ops_mcp/deploy_git_checkout_readonly.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "@router.", "@mcp.", "docker compose", "psycopg.connect(",
        "subprocess.Popen", "os.system", "git pull", "git push",
    ):
        assert forbidden not in src
