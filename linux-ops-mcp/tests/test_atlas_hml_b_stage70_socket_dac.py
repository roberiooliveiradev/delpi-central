"""ATLAS stage 70: signer:bridge DAC and tmpfiles drift denial.

Never touches /run, systemd, Docker, production, operational keys or host users.
"""
from __future__ import annotations

import os
import socket
import stat

import pytest

from linux_ops_mcp import atlas_hml_b_signer_listen as candidate
from linux_ops_mcp.atlas_hml_b_candidate_unit_review import (
    HMLCandidateUnitError, review_candidate_unit_sources,
)


@pytest.fixture
def socket_dir(tmp_path):
    directory = tmp_path / "signer"
    directory.mkdir(mode=0o700)
    os.chmod(directory, 0o2750)
    return directory


@pytest.mark.skipif(os.getuid() == 0, reason="disposable nonroot fixture only")
def test_signer_socket_inherits_exact_group_without_chown(socket_dir, monkeypatch):
    def forbid_chown(*args, **kwargs):
        raise AssertionError("attempt to chown signer socket")
    monkeypatch.setattr(candidate.os, "chown", forbid_chown)
    path = socket_dir / "sign.sock"
    listener = candidate.bind_signer_owned_socket(
        socket_path=path, owner_uid=os.getuid(), socket_gid=os.getgid(),
    )
    try:
        st = os.stat(path, follow_symlinks=False)
        assert stat.S_ISSOCK(st.st_mode)
        assert st.st_uid == os.getuid() and st.st_gid == os.getgid()
        assert stat.S_IMODE(st.st_mode) == 0o660
        assert not candidate.HMLSignerListenResult(1, path).can_execute
    finally:
        listener.close()
        path.unlink(missing_ok=True)


@pytest.mark.skipif(os.getuid() == 0, reason="disposable nonroot fixture only")
@pytest.mark.parametrize("mode", [0o750, 0o700, 0o2770, 0o2755, 0o3750])
def test_parent_requires_exact_setgid_02750(socket_dir, mode):
    os.chmod(socket_dir, mode)
    path = socket_dir / "sign.sock"
    with pytest.raises(candidate.HMLSignerListenError) as exc:
        candidate.bind_signer_owned_socket(
            socket_path=path, owner_uid=os.getuid(), socket_gid=os.getgid(),
        )
    assert exc.value.code == "HML_SIGNER_LISTEN_PARENT_DENIED"
    assert not path.exists()


@pytest.mark.skipif(os.getuid() == 0, reason="disposable nonroot fixture only")
def test_wrong_expected_gid_does_not_fall_back_to_primary(socket_dir):
    path = socket_dir / "sign.sock"
    with pytest.raises(candidate.HMLSignerListenError) as exc:
        candidate.bind_signer_owned_socket(
            socket_path=path, owner_uid=os.getuid(), socket_gid=os.getgid() + 1,
        )
    assert exc.value.code == "HML_SIGNER_LISTEN_PARENT_DENIED"
    assert not path.exists()


@pytest.mark.skipif(os.getuid() == 0, reason="disposable nonroot fixture only")
def test_parent_symlink_denied(socket_dir, tmp_path):
    link = tmp_path / "link"
    link.symlink_to(socket_dir, target_is_directory=True)
    with pytest.raises(candidate.HMLSignerListenError) as exc:
        candidate.bind_signer_owned_socket(
            socket_path=link / "sign.sock",
            owner_uid=os.getuid(), socket_gid=os.getgid(),
        )
    assert exc.value.code == "HML_SIGNER_LISTEN_PARENT_DENIED"


@pytest.mark.skipif(os.getuid() == 0, reason="disposable nonroot fixture only")
def test_dangling_socket_symlink_not_deleted(socket_dir):
    path = socket_dir / "sign.sock"
    path.symlink_to(socket_dir / "missing")
    with pytest.raises(candidate.HMLSignerListenError) as exc:
        candidate.bind_signer_owned_socket(
            socket_path=path, owner_uid=os.getuid(), socket_gid=os.getgid(),
        )
    assert exc.value.code == "HML_SIGNER_LISTEN_PATH_EXISTS"
    assert path.is_symlink()


@pytest.mark.skipif(os.getuid() == 0, reason="disposable nonroot fixture only")
def test_preexisting_file_is_not_unlinked(socket_dir):
    path = socket_dir / "sign.sock"
    path.write_text("not-owned-by-this-listener")
    with pytest.raises(candidate.HMLSignerListenError) as exc:
        candidate.bind_signer_owned_socket(
            socket_path=path, owner_uid=os.getuid(), socket_gid=os.getgid(),
        )
    assert exc.value.code == "HML_SIGNER_LISTEN_PATH_EXISTS"
    assert path.read_text() == "not-owned-by-this-listener"


@pytest.mark.skipif(os.getuid() == 0, reason="disposable nonroot fixture only")
def test_extended_or_unverifiable_directory_acl_denied(socket_dir, monkeypatch):
    monkeypatch.setattr(candidate, "has_no_extended_posix_acl",
                        lambda fd, *, directory: False)
    with pytest.raises(candidate.HMLSignerListenError) as exc:
        candidate.bind_signer_owned_socket(
            socket_path=socket_dir / "sign.sock",
            owner_uid=os.getuid(), socket_gid=os.getgid(),
        )
    assert exc.value.code == "HML_SIGNER_LISTEN_PARENT_DENIED"


@pytest.mark.parametrize("replacement", [
    " :0750 :atlas-hml-signer :atlas-hml-bridge -",
    " :02750 :atlas-hml-signer :docker -",
    " :02770 :atlas-hml-signer :atlas-hml-bridge -",
    " :02750 :root :atlas-hml-bridge -",
])
def test_tmpfiles_mutated_mode_or_identity_denied(replacement):
    from linux_ops_mcp.atlas_hml_b_candidate_unit_review import _DIR
    sources = {p.name: p.read_text(encoding="utf-8") for p in _DIR.glob("*.candidate")}
    name = "atlas-hml-runtime-layout.tmpfiles.candidate"
    old = " :02750 :atlas-hml-signer :atlas-hml-bridge -"
    assert old in sources[name]
    sources[name] = sources[name].replace(old, replacement, 1)
    with pytest.raises(HMLCandidateUnitError, match="HML_CANDIDATE_TMPFILES_DENIED"):
        review_candidate_unit_sources(sources)


def test_extra_tmpfiles_directive_denied():
    from linux_ops_mcp.atlas_hml_b_candidate_unit_review import _DIR
    sources = {p.name: p.read_text(encoding="utf-8") for p in _DIR.glob("*.candidate")}
    name = "atlas-hml-runtime-layout.tmpfiles.candidate"
    sources[name] += "\nd /run/docker.sock 0666 root docker -\n"
    with pytest.raises(HMLCandidateUnitError, match="HML_CANDIDATE_TMPFILES_DENIED"):
        review_candidate_unit_sources(sources)


def test_candidate_still_blocked_and_noninstallable():
    checked = review_candidate_unit_sources()
    assert checked.status == "blocked"
    assert checked.files_reviewed == 6
    assert not checked.auto_enable_possible
    assert not checked.can_execute
    assert not checked.prepare_eligible
