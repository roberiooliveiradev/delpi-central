"""Real disposable Git metadata tests, no Git execution by the ATLAS peek.

Git CLI is used ONLY by test fixture setup in pytest tmp_path. The source
under test never executes Git, touches Docker or grants PREPARE / ACT.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
from dataclasses import asdict
from pathlib import Path

import pytest

from linux_ops_mcp import atlas_hml_local_probe as probe
from linux_ops_mcp import atlas_hml_git_head_peek as peek
from linux_ops_mcp.deploy_git_checkout_readonly import GitCheckoutReadOnlyObserver


def git(root: Path, *args: str) -> str:
    env={
        "PATH":"/usr/bin:/bin", "HOME":"/nonexistent", "LC_ALL":"C",
        "GIT_CONFIG_NOSYSTEM":"1", "GIT_CONFIG_GLOBAL":"/dev/null",
        "GIT_TERMINAL_PROMPT":"0",
    }
    return subprocess.run(
        ["git","-C",str(root),*args],env=env,
        capture_output=True,check=True,text=True,timeout=10,
    ).stdout.strip()


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    root=tmp_path/"shared-checkout"
    root.mkdir()
    git(root,"init","-q","-b","main")
    (root/"app.txt").write_text("safe fixture only\n",encoding="utf-8")
    git(root,"add","app.txt")
    git(root,"-c","user.name=Test",
        "-c","user.email=test@example.invalid",
        "commit","-q","-m","test snapshot")
    return root


def test_only_main_sha_exposed_without_status_or_authorization(checkout):
    current=git(checkout,"rev-parse","HEAD")
    observation=peek.GitHeadMetadataPeek(checkout_root=checkout).read()
    assert observation.branch=="main" and observation.head_sha==current
    assert observation.source=="filesystem_head_only_untrusted"
    assert not observation.checkout_attested
    assert not observation.clean_status_observed
    assert not observation.challenge_bound
    assert not observation.prepare_eligible
    assert not observation.can_execute


def test_packed_refs_main_is_supported_without_running_git(checkout):
    expected=git(checkout,"rev-parse","HEAD")
    git(checkout,"pack-refs","--all")
    observed=peek.GitHeadMetadataPeek(checkout_root=checkout).read()
    assert observed.head_sha==expected


def test_genuine_git_execution_is_not_triggered_by_metadata_peek(
    checkout,monkeypatch,
):
    expected=git(checkout,"rev-parse","HEAD")
    def forbid_git(*args,**kwargs):
        raise AssertionError("ATLAS metadata observation must not run Git")
    monkeypatch.setattr(subprocess,"run",forbid_git)
    observation=peek.GitHeadMetadataPeek(checkout_root=checkout).read()
    assert observation.head_sha==expected


def test_untrusted_local_config_can_contain_hooks_without_execution(
    checkout,monkeypatch,
):
    # The test intentionally does not run Git after writing this config.
    marker=checkout.parent/"must-never-be-created"
    config=checkout/".git"/"config"
    config.write_text(
        config.read_text()+
        '\n[core]\n\thooksPath = '+str(marker)+
        '\n\tfsmonitor = '+str(marker)+"\n",encoding="utf-8",
    )
    def forbid_git(*args,**kwargs):
        raise AssertionError("Unsafe repository config must never execute")
    monkeypatch.setattr(subprocess,"run",forbid_git)
    assert peek.GitHeadMetadataPeek(checkout_root=checkout).read().branch=="main"
    assert not marker.exists()


def test_symlink_head_and_ref_are_rejected(checkout):
    metadata=checkout/".git"
    head=metadata/"HEAD"
    ref=metadata/"refs"/"heads"/"main"
    for source in (head,ref):
        copy=source.with_name(source.name+"-safe")
        source.rename(copy)
        source.symlink_to(copy)
        try:
            with pytest.raises(peek.GitHeadPeekError,match="GIT_HEAD_UNAVAILABLE"):
                peek.GitHeadMetadataPeek(checkout_root=checkout).read()
        finally:
            source.unlink()
            copy.rename(source)


def test_git_directory_symlink_is_rejected(checkout):
    hidden=checkout/".git"
    original=checkout/".git-backup"
    hidden.rename(original)
    hidden.symlink_to(original, target_is_directory=True)
    try:
        with pytest.raises(peek.GitHeadPeekError,match="GIT_HEAD_UNAVAILABLE"):
            peek.GitHeadMetadataPeek(checkout_root=checkout).read()
    finally:
        hidden.unlink()
        original.rename(hidden)


def test_checkout_root_symlink_is_rejected(checkout):
    link=checkout.parent/"indirect-checkout"
    link.symlink_to(checkout,target_is_directory=True)
    with pytest.raises(peek.GitHeadPeekError,match="GIT_HEAD_PATH_INVALID"):
        peek.GitHeadMetadataPeek(checkout_root=link).read()


@pytest.mark.parametrize("invalid",[
    b"ref: refs/heads/feature\n",
    b"ref: refs/heads/../secrets\n",
    b"ref: refs/heads/main/../../secret\n",
    b"ref: refs/heads/main\x00\n",
    b"ref: refs/heads/main\n"+b"A"*200,
    b"not-a-ref\n",
    b"0"*40+b"\n",
])
def test_non_main_detached_or_malicious_head_is_rejected(
    checkout,invalid,
):
    (checkout/".git"/"HEAD").write_bytes(invalid)
    with pytest.raises(peek.GitHeadPeekError,match="GIT_HEAD_NOT_MAIN|GIT_HEAD_METADATA_INVALID"):
        peek.GitHeadMetadataPeek(checkout_root=checkout).read()


def test_packed_ref_not_found_or_duplicate_is_rejected(checkout):
    gitdir=checkout/".git"
    loose=gitdir/"refs"/"heads"/"main"
    sha=loose.read_text().strip().encode()
    loose.unlink()
    packed=gitdir/"packed-refs"
    packed.write_bytes(b"# pack-refs with: peeled fully-peeled\n"+
                       sha+b" refs/heads/other\n")
    with pytest.raises(peek.GitHeadPeekError,match="GIT_HEAD_REF_UNAVAILABLE"):
        peek.GitHeadMetadataPeek(checkout_root=checkout).read()
    packed.write_bytes(sha+b" refs/heads/main\n"+sha+b" refs/heads/main\n")
    with pytest.raises(peek.GitHeadPeekError,match="GIT_HEAD_REF_UNAVAILABLE"):
        peek.GitHeadMetadataPeek(checkout_root=checkout).read()


def test_non_hex_or_oversized_sha_is_rejected(checkout):
    ref=checkout/".git"/"refs"/"heads"/"main"
    for payload in (b"not-a-sha\n",b"f"*129+b"\n"):
        ref.write_bytes(payload)
        with pytest.raises(peek.GitHeadPeekError,match="GIT_HEAD_METADATA_INVALID"):
            peek.GitHeadMetadataPeek(checkout_root=checkout).read()


def test_mid_observation_ref_change_does_not_claim_consistency(
    checkout,monkeypatch,
):
    original=peek._bounded_file
    calls=[0]
    def reader(fd,parts,limit):
        result=original(fd,parts,limit)
        if parts==("refs","heads","main"):
            calls[0]+=1
            if calls[0]==2:
                return b"a"*40+b"\n"
        return result
    monkeypatch.setattr(peek,"_bounded_file",reader)
    with pytest.raises(peek.GitHeadPeekError,match="GIT_HEAD_CHANGED_DURING_READ"):
        peek.GitHeadMetadataPeek(checkout_root=checkout).read()


def test_hml_preflight_metadata_mode_never_runs_git(
    checkout,monkeypatch,
):
    def forbid_git(*args,**kwargs):
        raise AssertionError("Group-writable checkout must not run Git")
    monkeypatch.setattr(GitCheckoutReadOnlyObserver,"read",forbid_git)
    identity=probe.LocalOSObservation(
        uid=995,euid=995,groups=("atlas-hml",),checkout_writable=False,
    )
    result=asyncio.run(probe.inspect_hml_local(
        identity=identity,
        observer=GitCheckoutReadOnlyObserver(checkout_root=checkout),
        inspector=None,
        proxy_error="HML_PROXY_UNAVAILABLE",
        metadata_only=True,
        metadata_reader=peek.GitHeadMetadataPeek(checkout_root=checkout),
    ))
    assert result.git_head==git(checkout,"rev-parse","HEAD")
    assert result.git_branch=="main"
    assert result.git_clean_nonignored is None
    assert result.git_observation_method=="filesystem_head_only_untrusted"
    assert "HML_GIT_METADATA_ONLY_UNTRUSTED" in result.blocks
    assert "HML_GIT_STATUS_NOT_CHECKED" in result.blocks
    assert "HML_PROXY_UNAVAILABLE" in result.blocks
    assert result.status=="blocked"
    assert not result.prepare_eligible and not result.can_execute
    assert not result.checkout_integrity_attested
    assert not result.collector_identity_attested


def test_unsafe_account_skips_git_even_in_metadata_only_mode(checkout):
    result=asyncio.run(probe.inspect_hml_local(
        identity=probe.LocalOSObservation(
            uid=1004,euid=1004,
            groups=("sudo","docker","projetos"),checkout_writable=True,
        ),
        observer=object(),inspector=object(),metadata_only=True,
        metadata_reader=object(),
    ))
    assert "HOST_OBSERVATION_REFUSED_UNSAFE_ACCOUNT" in result.blocks
    assert result.git_head is None and result.git_observation_method is None


def test_cli_default_uses_metadata_only_under_atlas_hml(
    checkout,monkeypatch,capsys,
):
    monkeypatch.setattr(probe,"_CHECKOUT",checkout)
    monkeypatch.setattr(probe,"read_local_os",lambda:probe.LocalOSObservation(
        uid=995,euid=995,groups=("atlas-hml",),checkout_writable=False,
    ))
    def not_installed():
        raise probe.HMLProbeError("HML_PROXY_UNAVAILABLE")
    monkeypatch.setattr(probe,"fixed_proxy_inspector",not_installed)
    monkeypatch.setattr(GitCheckoutReadOnlyObserver,"read",
                        lambda self,**_:(_ for _ in ()).throw(
                            AssertionError("No Git allowed from CLI")
                        ))
    assert probe.main()==0
    outcome=json.loads(capsys.readouterr().out)
    assert outcome["status"]=="blocked"
    assert outcome["git_head"]==git(checkout,"rev-parse","HEAD")
    assert outcome["git_clean_nonignored"] is None
    assert outcome["git_observation_method"]=="filesystem_head_only_untrusted"
    assert outcome["prepare_eligible"] is False
    assert outcome["can_execute"] is False


def test_invalid_peek_does_not_expose_raw_paths_or_read_docker(
    tmp_path,
):
    root=tmp_path/"missing-checkout"
    with pytest.raises(peek.GitHeadPeekError) as exc:
        peek.GitHeadMetadataPeek(checkout_root=root).read()
    assert str(root) not in str(exc.value)
    assert not hasattr(peek,"main")


def test_source_has_no_git_process_or_shared_repo_trust_bypass():
    source=Path(__file__).resolve().parents[1]/"linux_ops_mcp"/"atlas_hml_git_head_peek.py"
    text=source.read_text()
    for forbidden in (
        "import subprocess","subprocess.run(","os.system(","os.chmod(",
        "os.chown(","safe.directory=", "create_subprocess","shell=True",
        "docker.sock", "mcp.tool(", "@router.",
    ):
        assert forbidden not in text
