"""P2.2h.2ab-ad: real disposable Git + GET-only Docker, OS gates, CLI.

No raw Docker socket, external network, Keycloak, database or deploy actions.
All Git writes are scoped to pytest tmp_path; the probe itself is read-only.
"""
from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
from dataclasses import asdict, replace
from datetime import datetime, timezone

import httpx
import pytest

from linux_ops_mcp import atlas_hml_local_probe as probe
from linux_ops_mcp.deploy_git_checkout_readonly import GitCheckoutReadOnlyObserver
from linux_ops_mcp.deploy_host_source import DockerReadOnlyInspect

NOW = datetime(2026,11,16,23,0,tzinfo=timezone.utc)
IMAGE="sha256:"+"d"*64
CONTAINER="a"*64
IDENTITY=probe.LocalOSObservation(
    uid=1001,euid=1001,groups=("atlas-hml-collector",),
    checkout_writable=False,
)


def git(root,*args):
    env={
        "PATH":"/usr/bin:/bin", "HOME":"/nonexistent", "LC_ALL":"C",
        "GIT_CONFIG_NOSYSTEM":"1", "GIT_CONFIG_GLOBAL":"/dev/null",
        "GIT_TERMINAL_PROMPT":"0",
    }
    return subprocess.run(
        ["git","-C",str(root),*args], env=env,
        capture_output=True,text=True,check=True,timeout=10,
    ).stdout.strip()


@pytest.fixture
def checkout(tmp_path):
    root=tmp_path/"one-disposable-readonly-repository"
    root.mkdir()
    git(root,"init","-q","-b","main")
    (root/"doc.txt").write_text("hml preflight fixture\n",encoding="utf-8")
    git(root,"add","doc.txt")
    git(root,"-c","user.name=Test","-c","user.email=test@example.invalid",
        "commit","-q","-m","initial disposable commit")
    return root


def observer(checkout):
    return GitCheckoutReadOnlyObserver(checkout_root=checkout,clock=lambda:NOW)


def docker(*, running=True,health="healthy",image=IMAGE,labels=True):
    seen=[]
    def respond(request):
        seen.append((request.method,request.url.path,request.url.host))
        name="delpi-hml-public-hub"
        project="delpi-hml" if labels else "infra"
        return httpx.Response(200,json={
            "Id":CONTAINER,"Image":image,"Name":"/"+name,
            "Config":{"Labels":{
                "com.docker.compose.service":"public-hub",
                "com.docker.compose.project":project,
            }},
            "State":{"Running":running,"Health":{"Status":health}},
        })
    return DockerReadOnlyInspect(transport=httpx.MockTransport(respond)),seen


def run(checkout, *, ident=IDENTITY,inspector=None,proxy_error=None):
    if inspector is None:
        inspector,_=docker()
    return asyncio.run(probe.inspect_hml_local(
        identity=ident,observer=observer(checkout),inspector=inspector,
        proxy_error=proxy_error,clock=lambda:NOW,
    ))


def test_real_git_and_bounded_docker_get_are_reported_not_authorized(checkout):
    inspector,seen=docker()
    result=run(checkout,inspector=inspector)
    sha=git(checkout,"rev-parse","HEAD")
    assert result.status=="blocked"
    assert result.git_head==sha
    assert result.git_branch=="main"
    assert result.git_clean_nonignored is True
    assert result.docker_image_id==IMAGE
    assert result.docker_running and result.docker_healthy
    assert seen==[("GET","/containers/delpi-hml-public-hub/json","docker.local")]
    assert result.environment=="hml" and result.service_id=="public-hub"
    assert not result.collector_identity_attested
    assert not result.docker_proxy_readonly_attested
    assert not result.checkout_integrity_attested
    assert not result.challenge_consumed
    assert not result.prepare_eligible and not result.can_execute
    assert {"PREPARE_DISABLED","ACT_DISABLED",
            "HML_PROXY_POLICY_NOT_INDEPENDENTLY_ATTESTED",
            "BACKUP_RESTORE_AND_ROLLBACK_NOT_ATTESTED"}.issubset(result.blocks)
    assert "ATLAS_HML" not in json.dumps(asdict(result))


@pytest.mark.parametrize("ident,reason",[
    (replace(IDENTITY,uid=0,euid=0),"ACCOUNT_ROOT_OR_SETUID"),
    (replace(IDENTITY,uid=1001,euid=0),"ACCOUNT_ROOT_OR_SETUID"),
    (replace(IDENTITY,uid=1001,euid=1002),"ACCOUNT_ROOT_OR_SETUID"),
    (replace(IDENTITY,groups=("docker",)),"ACCOUNT_PRIVILEGED_GROUP"),
    (replace(IDENTITY,groups=("wheel",)),"ACCOUNT_PRIVILEGED_GROUP"),
    (replace(IDENTITY,groups=("sudo",)),"ACCOUNT_PRIVILEGED_GROUP"),
    (replace(IDENTITY,checkout_writable=True),"ACCOUNT_CAN_MODIFY_CHECKOUT"),
])
def test_privileged_or_mutable_account_never_touches_git_or_socket(ident,reason):
    result=asyncio.run(probe.inspect_hml_local(
        identity=ident,observer=object(),inspector=object(),clock=lambda:NOW,
    ))
    assert reason in result.blocks
    assert "HOST_OBSERVATION_REFUSED_UNSAFE_ACCOUNT" in result.blocks
    assert result.git_head is None and result.docker_image_id is None
    assert not result.can_execute


def test_dirty_or_wrong_branch_is_diagnosed_with_real_git(checkout):
    (checkout/"untracked.txt").write_text("test only\n")
    result=run(checkout)
    assert result.git_clean_nonignored is False
    assert "HML_CHECKOUT_DIRTY" in result.blocks
    (checkout/"untracked.txt").unlink()
    git(checkout,"switch","-q","-c","feat/test")
    result=run(checkout)
    assert result.git_branch=="feat/test"
    assert "HML_CHECKOUT_NOT_MAIN" in result.blocks
    assert result.status=="blocked"


def test_optional_proxy_missing_still_observes_git_without_network(checkout):
    result=asyncio.run(probe.inspect_hml_local(
        identity=IDENTITY,observer=observer(checkout),
        inspector=None,proxy_error="HML_PROXY_UNAVAILABLE",clock=lambda:NOW,
    ))
    assert result.git_head==git(checkout,"rev-parse","HEAD")
    assert "HML_PROXY_UNAVAILABLE" in result.blocks
    assert result.docker_image_id is None
    assert not result.prepare_eligible


def test_proxy_returned_wrong_project_does_not_get_image_trust(checkout):
    inspector,seen=docker(labels=False)
    result=run(checkout,inspector=inspector)
    assert seen==[("GET","/containers/delpi-hml-public-hub/json","docker.local")]
    assert "HML_DOCKER_READ_UNAVAILABLE" in result.blocks
    assert result.docker_image_id is None


def test_unhealthy_or_stopped_container_reported_without_promotion(checkout):
    for kwargs in ({"running":False},{"health":"unhealthy"}):
        inspector,_=docker(**kwargs)
        result=run(checkout,inspector=inspector)
        assert "HML_CONTAINER_NOT_HEALTHY" in result.blocks
        assert not result.can_execute


def test_invalid_git_root_keeps_docker_read_only_but_reports_missing_git(tmp_path):
    inspector,seen=docker()
    result=asyncio.run(probe.inspect_hml_local(
        identity=IDENTITY,
        observer=GitCheckoutReadOnlyObserver(
            checkout_root=tmp_path/"missing",
            clock=lambda:NOW,
        ),
        inspector=inspector,clock=lambda:NOW,
    ))
    assert "HML_GIT_OBSERVATION_UNAVAILABLE" in result.blocks
    assert result.docker_image_id==IMAGE
    assert len(seen)==1


def test_bad_clock_and_os_claims_are_refused_before_any_inspector():
    with pytest.raises(probe.HMLProbeError,match="HML_PROBE_CLOCK_INVALID"):
        asyncio.run(probe.inspect_hml_local(
            identity=IDENTITY,observer=object(),inspector=object(),
            clock=lambda:NOW.replace(tzinfo=None),
        ))
    with pytest.raises(probe.HMLProbeError,match="OS_INSPECTION_INVALID"):
        probe.account_blocks({"uid":1001})
    with pytest.raises(probe.HMLProbeError,match="OS_INSPECTION_INVALID"):
        probe.account_blocks(replace(IDENTITY,checkout_writable=1))


def test_dedicated_unix_socket_path_is_required_and_raw_alias_denied(tmp_path,monkeypatch):
    folder=tmp_path/"atlas-hml-readonly"
    folder.mkdir()
    path=folder/"inspect.sock"
    monkeypatch.setattr(probe,"_PROXY_SOCKET",path)
    with pytest.raises(probe.HMLProbeError,match="HML_PROXY_UNAVAILABLE"):
        probe._stat_fixed_proxy(_test_owner_uid=os.getuid(),_test_socket_gid=os.getgid())
    unix=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    unix.bind(str(path))
    try:
        os.chmod(path,0o660)
        probe._stat_fixed_proxy(_test_owner_uid=os.getuid(),_test_socket_gid=os.getgid())
        with pytest.raises(probe.HMLProbeError,match="HML_RAW_DOCKER_SOCKET_DENIED"):
            probe._stat_fixed_proxy(_test_owner_uid=os.getuid(),_test_socket_gid=os.getgid(),_test_raw_sockets=(path,))
    finally:
        unix.close()
        path.unlink()


def test_proxy_symlink_world_writable_parent_and_node_denied(tmp_path,monkeypatch):
    folder=tmp_path/"proxy-safe"
    folder.mkdir()
    path=folder/"inspect.sock"
    unix=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    unix.bind(str(path))
    monkeypatch.setattr(probe,"_PROXY_SOCKET",path)
    try:
        os.chmod(folder,0o777)
        with pytest.raises(probe.HMLProbeError,match="HML_PROXY_PATH_UNSAFE"):
            probe._stat_fixed_proxy(_test_owner_uid=os.getuid(),_test_socket_gid=os.getgid())
        os.chmod(folder,0o700)
        os.chmod(path,0o777)
        with pytest.raises(probe.HMLProbeError,match="HML_PROXY_PATH_UNSAFE"):
            probe._stat_fixed_proxy(_test_owner_uid=os.getuid(),_test_socket_gid=os.getgid())
        os.chmod(path,0o660)
        link=folder/"alias.sock"
        link.symlink_to(path)
        monkeypatch.setattr(probe,"_PROXY_SOCKET",link)
        with pytest.raises(probe.HMLProbeError,match="HML_PROXY_PATH_UNSAFE"):
            probe._stat_fixed_proxy(_test_owner_uid=os.getuid(),_test_socket_gid=os.getgid())
    finally:
        unix.close()
        path.unlink()


def test_diagnostic_main_is_explicit_read_only_sanitized_json(monkeypatch,capsys):
    monkeypatch.setattr(probe,"read_local_os",lambda:replace(
        IDENTITY,checkout_writable=True,
    ))
    def fail_if_socket_accessed():
        raise AssertionError("unsafe identity may not probe UNIX socket")
    monkeypatch.setattr(probe,"fixed_proxy_inspector",fail_if_socket_accessed)
    code=probe.main()
    assert code==0
    payload=json.loads(capsys.readouterr().out)
    assert payload["status"]=="blocked"
    assert "ACCOUNT_CAN_MODIFY_CHECKOUT" in payload["blocks"]
    assert payload["prepare_eligible"] is False
    assert payload["can_execute"] is False
    assert payload["docker_image_id"] is None
    assert payload["git_head"] is None


def test_cli_failures_do_not_echo_exception_path_or_credentials(monkeypatch,capsys):
    def fail_os():
        raise OSError("/private/var/run/docker.sock secret")
    monkeypatch.setattr(probe,"read_local_os",fail_os)
    assert probe.main()==2
    printed=capsys.readouterr().out
    assert "/private/" not in printed
    assert "secret" not in printed
    assert json.loads(printed)=={
        "status":"blocked",
        "code":"HML_PREFLIGHT_UNAVAILABLE",
        "prepare_eligible":False,
        "can_execute":False,
    }


def test_preflight_module_contains_no_exec_shell_mutating_database_or_mcp_route():
    from pathlib import Path
    text=(Path(__file__).resolve().parents[1]/
          "linux_ops_mcp/atlas_hml_local_probe.py").read_text()
    for forbidden in (
        "@router.","@mcp.","subprocess.run","CREATE ROLE",
        "docker compose", "psycopg.connect(", "UPDATE it_portal",
        "INSERT INTO it_portal", "os.system(", "os.chmod(", "os.chown(",
    ):
        assert forbidden not in text
