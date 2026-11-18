"""Stage74 read-only tmpfiles inventory + real disposable no-clobber regression."""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys

import pytest

from linux_ops_mcp import atlas_hml_b_stage74_tmpfiles_audit as stage74

_SRC = "atlas-hml-runtime-layout.conf"


def conf(tmp_path, content, *, directory="etc/tmpfiles.d", name="other.conf"):
    folder = tmp_path / directory
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    target.write_text(content, encoding="utf-8")
    return target


def report(tmp_path):
    return stage74.audit_stage74_boot_config(root=tmp_path)


def test_candidate_is_create_only_for_five_paths():
    assert stage74.review_no_clobber_candidate() is True
    preview = stage74.render_stage73_tmpfiles_payload()
    lines = [s for s in preview.splitlines() if s.startswith("d ")]
    assert len(lines) == 5
    for item in lines:
        fields = item.split()
        assert len(fields) == 6
        assert fields[2].startswith(":")
        assert fields[3].startswith(":")
        assert fields[4].startswith(":")
    assert all("ExecStart=" not in line for line in preview.splitlines())


def test_empty_fixture_is_untrusted_not_install_approval(tmp_path):
    result = report(tmp_path)
    assert result.config_files_scanned == 0
    assert result.config_dirs_present == 0
    assert result.candidate_no_clobber
    assert result.finding_codes == ("HOST_ATTESTATION_NOT_INDEPENDENT",)
    assert result.status == "blocked"
    assert not result.host_attested and not result.boot_recreated
    assert not result.installation_authorized
    assert not result.prepare_eligible and not result.can_execute
    assert "SEC_01_TO_10_PENDING" in result.blocks


def test_conflicting_exact_target_is_detected(tmp_path):
    conf(tmp_path, "d /run/atlas-hml-signer-socket 0777 root docker -\n")
    result = report(tmp_path)
    assert "TMPFILES_ATLAS_PATH_ALREADY_DECLARED" in result.finding_codes
    assert result.config_files_scanned == 1
    assert not result.can_execute


@pytest.mark.parametrize("content,code", [
    ("z /run/atlas-hml-signer-keys 0777 root root -\n",
     "TMPFILES_ATLAS_PATH_ALREADY_DECLARED"),
    ("a+ /run/atlas-hml-* - - - - user:1000:rwx\n",
     "TMPFILES_DYNAMIC_RULE_REQUIRES_REVIEW"),
    ("R /run/atlas-hml-* - - - -\n",
     "TMPFILES_DYNAMIC_RULE_REQUIRES_REVIEW"),
    ("Z /var/lib - - - -\n",
     "TMPFILES_PARENT_RULE_REQUIRES_REVIEW"),
    ("d /run 0755 root root -\n",
     "TMPFILES_PARENT_RULE_REQUIRES_REVIEW"),
    ("d /%T/atlas-hml-signer - - - -\n",
     "TMPFILES_DYNAMIC_RULE_REQUIRES_REVIEW"),
])
def test_config_can_collide_even_without_same_basename(tmp_path, content, code):
    conf(tmp_path, content)
    assert code in report(tmp_path).finding_codes


def test_unrelated_config_is_counted_without_false_atlas_target(tmp_path):
    conf(tmp_path, "d /run/other-app 0750 root root -\n")
    result = report(tmp_path)
    assert result.config_files_scanned == 1
    assert result.finding_codes == ("HOST_ATTESTATION_NOT_INDEPENDENT",)


def test_our_conf_basename_is_reserved_even_if_content_harmless(tmp_path):
    conf(tmp_path, "d /run/other-app 0750 root root -\n", name=_SRC)
    assert "ATLAS_TMPFILES_CONF_NAME_ALREADY_PRESENT" in report(tmp_path).finding_codes


def test_same_basename_multiple_search_paths_requires_review(tmp_path):
    conf(tmp_path, "d /run/other-app - - - -\n", directory="etc/tmpfiles.d")
    conf(tmp_path, "d /run/other-app - - - -\n", directory="usr/lib/tmpfiles.d")
    result = report(tmp_path)
    assert result.config_files_scanned == 2
    assert "TMPFILES_BASENAME_PRECEDENCE_REVIEW" in result.finding_codes


def test_symlink_config_does_not_get_followed(tmp_path):
    real = conf(tmp_path, "d /run/other-app - - - -\n", name="safe.conf")
    (real.parent / "link.conf").symlink_to(real)
    assert "TMPFILES_CONFIG_UNREADABLE_OR_UNSTABLE" in report(tmp_path).finding_codes


def test_symlinked_tmpfiles_directory_is_denied(tmp_path):
    directory = tmp_path / "etc"
    directory.mkdir()
    target = tmp_path / "real"
    target.mkdir()
    (directory / "tmpfiles.d").symlink_to(target, target_is_directory=True)
    assert "TMPFILES_CONFIG_DIRECTORY_UNVERIFIABLE" in report(tmp_path).finding_codes


def test_oversized_config_denied(tmp_path):
    conf(tmp_path, "a" * 262145)
    assert "TMPFILES_CONFIG_UNREADABLE_OR_UNSTABLE" in report(tmp_path).finding_codes


def test_existing_systemd_unit_is_reported_even_if_broken_symlink(tmp_path):
    unit_dir = tmp_path / "etc/systemd/system"
    unit_dir.mkdir(parents=True)
    (unit_dir / "atlas-hml-local-signer.service").symlink_to("/nonexistent")
    assert "ATLAS_SYSTEMD_UNIT_ALREADY_PRESENT" in report(tmp_path).finding_codes


def test_cli_requires_explicit_scope_and_reports_only_blocked(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        stage74.main([])
    assert exc.value.code == 2
    assert stage74.main(["--fixture-root", str(tmp_path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["schema"] == "atlas.hml.stage74.boot-audit.v1"
    assert result["status"] == "blocked"
    assert result["observation_kind"] == "operator_self_observation"
    assert result["candidate_no_clobber"] is True
    assert not result["host_attested"]
    assert not result["can_execute"] and not result["prepare_eligible"]


def test_cli_does_not_change_fixture_files(tmp_path, capsys):
    original = conf(tmp_path, "d /run/other-app 0750 root root -\n")
    before = [(p.relative_to(tmp_path), p.stat().st_mtime_ns)
              for p in tmp_path.rglob("*")]
    assert stage74.main(["--fixture-root", str(tmp_path)]) == 0
    capsys.readouterr()
    after = [(p.relative_to(tmp_path), p.stat().st_mtime_ns)
             for p in tmp_path.rglob("*")]
    assert after == before
    assert original.read_text().startswith("d /run/other-app")


def test_root_requires_explicit_host_readonly_flag():
    with pytest.raises(stage74.Stage74AuditError, match="STAGE74_EXPLICIT_ROOT_REQUIRED"):
        stage74.audit_stage74_boot_config(root=stage74.Path("/"))


@pytest.mark.skipif(
    not sys.platform.startswith("linux") or not shutil.which("systemd-tmpfiles"),
    reason="disposable Linux fixture only",
)
def test_systemd_tmpfiles_create_only_cannot_silently_repair_preexisting_drift(tmp_path):
    """Real systemd invocation is restricted to an isolated --root fixture."""
    dirname = "/run/atlas-hml-stage74-disposable-test"
    root = tmp_path
    folder = root / "etc/tmpfiles.d"
    folder.mkdir(parents=True)
    (root / "run").mkdir()
    (folder / "atlas-stage74-fixture.conf").write_text(
        f"d {dirname} :0750 :{os.getuid()} :{os.getgid()} -\n",
        encoding="utf-8",
    )
    command = [
        shutil.which("systemd-tmpfiles"), f"--root={root}",
        "--create", f"--prefix={dirname}",
    ]
    subprocess.run(command, check=True, capture_output=True, timeout=15)
    actual = root / dirname.lstrip("/")
    assert stat.S_IMODE(actual.stat().st_mode) == 0o750
    os.chmod(actual, 0o777)
    subprocess.run(command, check=True, capture_output=True, timeout=15)
    # Actual systemd's colon semantics: do not repair unexpected drift.
    assert stat.S_IMODE(actual.stat().st_mode) == 0o777
    # This MUST fail subsequent policy verification rather than auto-correct.
    assert stage74.audit_stage74_boot_config(root=root).status == "blocked"
