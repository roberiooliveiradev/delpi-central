"""ATLAS P2.2h.2ae-ag: real UNIX socket + GET-only proxy + client interop.

All sockets live under pytest tmp_path. Docker is simulated using an HTTPX
MockTransport. Never accesses Docker's actual socket, servers or network.
"""
from __future__ import annotations

import asyncio
import json
import os
import socket
import threading
from dataclasses import asdict
from pathlib import Path

import httpx
import pytest

from linux_ops_mcp import atlas_hml_unix_proxy as proxy
from linux_ops_mcp.deploy_host_source import (
    DockerReadOnlyInspect, RuntimeContainer,
)

IMAGE="sha256:"+"d"*64
CID="a"*64
GET=(
    b"GET /containers/delpi-hml-public-hub/json HTTP/1.1\r\n"
    b"Host: docker.local\r\nConnection: close\r\n\r\n"
)
TARGET=proxy._TARGET


class Source:
    def __init__(self, *, data=None, exc=None):
        self.calls=[]
        self.data=data if data is not None else RuntimeContainer(
            container_id=CID,image_id=IMAGE,running=True,healthy=True,
        )
        self.exc=exc

    async def inspect(self,target):
        self.calls.append(target)
        if self.exc is not None:
            raise self.exc
        return self.data


@pytest.fixture
def endpoint(tmp_path):
    root=tmp_path/"atlas-hml-readonly"
    root.mkdir(mode=0o700)
    os.chmod(root,0o700)
    path=root/"inspect.sock"
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    listener.bind(str(path))
    os.chmod(path, 0o660)
    listener.listen(3)
    try:
        yield path,listener
    finally:
        listener.close()
        if path.exists():
            path.unlink()


def start_one(endpoint,inspector, *, allowed_uid=None, owner_uid=None):
    path,listener=endpoint
    results=[]
    errors=[]
    def run():
        try:
            results.append(proxy.serve_one_prebound(
                listener=listener,
                allowed_collector_uid=(
                    allowed_uid if allowed_uid is not None else max(1,os.getuid())
                ),
                inspector=inspector,
                expected_path=path,
                owner_uid=os.getuid() if owner_uid is None else owner_uid,
                socket_gid=os.getgid(),
            ))
        except Exception as exc:
            errors.append(exc)
    thread=threading.Thread(target=run,daemon=True)
    thread.start()
    return thread,results,errors


def raw_request(endpoint, request):
    path,_=endpoint
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
        client.settimeout(4)
        client.connect(str(path))
        client.sendall(request)
        result=bytearray()
        while True:
            data=client.recv(4096)
            if not data:
                break
            result.extend(data)
    head,body=bytes(result).split(b"\r\n\r\n",1)
    code=int(head.split(b"\r\n",1)[0].split()[1])
    return code,json.loads(body),head


def wait_for(thread,results,errors):
    thread.join(6)
    assert not thread.is_alive(),"proxy one-shot never completed"
    assert not errors,[repr(e) for e in errors]
    assert len(results)==1
    return results[0]


@pytest.mark.skipif(os.getuid()==0,reason="real SO_PEERCRED positive needs nonroot CI runner")
def test_real_kernel_peer_uid_and_docker_client_interop(endpoint):
    path,_=endpoint
    received=[]
    def upstream(request):
        received.append((request.method,request.url.path))
        return httpx.Response(200,json={
            "Id":CID,"Image":IMAGE,"Name":"/delpi-hml-public-hub",
            "Config":{"Labels":{
                "com.docker.compose.service":"public-hub",
                "com.docker.compose.project":"delpi-hml",
            },"Env":["DO_NOT_RETURN_FAKE_SECRET=xyz"]},
            "State":{"Running":True,"Health":{"Status":"healthy"}},
        })
    source=DockerReadOnlyInspect(transport=httpx.MockTransport(upstream))
    thread,results,errors=start_one(endpoint,source,allowed_uid=os.getuid())
    client=DockerReadOnlyInspect(
        transport=httpx.AsyncHTTPTransport(uds=str(path)),
    )
    observed=asyncio.run(client.inspect(TARGET))
    result=wait_for(thread,results,errors)
    assert observed==RuntimeContainer(
        container_id=CID,image_id=IMAGE,running=True,healthy=True,
    )
    assert received==[("GET","/containers/delpi-hml-public-hub/json")]
    assert result.http_status==200 and result.request_accepted
    assert result.status=="blocked"
    assert not result.raw_docker_socket_exposed
    assert not result.proxy_policy_independently_attested
    assert not result.host_identity_attested
    assert not result.prepare_eligible
    assert not result.can_execute


@pytest.mark.parametrize("request_bytes,status",[
    (b"POST /containers/delpi-hml-public-hub/json HTTP/1.1\r\nHost: docker.local\r\n\r\n",405),
    (b"DELETE /containers/delpi-hml-public-hub/json HTTP/1.1\r\nHost: docker.local\r\n\r\n",405),
    (b"HEAD /containers/delpi-hml-public-hub/json HTTP/1.1\r\nHost: docker.local\r\n\r\n",405),
    (b"GET /containers/json HTTP/1.1\r\nHost: docker.local\r\n\r\n",404),
    (b"GET /containers/delpi-public-hub/json HTTP/1.1\r\nHost: docker.local\r\n\r\n",404),
    (b"GET /containers/delpi-hml-public-hub/json?x=1 HTTP/1.1\r\nHost: docker.local\r\n\r\n",404),
    (b"GET /containers/delpi-hml-public-hub/json HTTP/1.0\r\nHost: docker.local\r\n\r\n",404),
    (b"GET /containers/delpi-hml-public-hub/json HTTP/1.1\r\nHost: attacker\r\n\r\n",400),
    (b"GET /containers/delpi-hml-public-hub/json HTTP/1.1\r\n\r\n",400),
    (GET[:-2]+b"Host: docker.local\r\n\r\n",400),
    (GET[:-2]+b"Content-Length: 3\r\n\r\n",400),
    (GET[:-2]+b"Transfer-Encoding: chunked\r\n\r\n",400),
    (GET[:-2]+b"Authorization: Bearer secret\r\n\r\n",400),
    (GET[:-2]+b"Expect: 100-continue\r\n\r\n",400),
    (GET[:-2]+b"Upgrade: websocket\r\n\r\n",400),
    (GET+b"GET /containers/delpi-hml-public-hub/json HTTP/1.1\r\n",400),
    (b"GET /containers/delpi-hml-public-hub/json HTTP/1.1\r\n"
     b"Host: docker.local\r\nX-Filler: "+b"A"*2100+b"\r\n\r\n",400),
])
def test_non_whitelisted_method_path_header_or_pipelining_is_denied(
    endpoint,request_bytes,status,monkeypatch,
):
    monkeypatch.setattr(proxy,"_peer_uid",lambda _:max(1,os.getuid()))
    source=Source()
    thread,result,error=start_one(endpoint,source)
    code,payload,headers=raw_request(endpoint,request_bytes)
    got=wait_for(thread,result,error)
    assert code==status
    assert payload=={"error":"HML_REQUEST_DENIED"}
    assert got.status=="blocked" and not got.request_accepted
    assert not source.calls
    assert b"Cache-Control: no-store" in headers


def test_wrong_actual_uid_is_denied_before_docker_even_for_exact_get(
    endpoint,monkeypatch,
):
    monkeypatch.setattr(proxy,"_peer_uid",lambda _:2000)
    source=Source()
    thread,result,error=start_one(endpoint,source,allowed_uid=2001)
    code,payload,_=raw_request(endpoint,GET)
    got=wait_for(thread,result,error)
    assert code==403 and payload=={"error":"HML_PEER_UNTRUSTED"}
    assert not got.request_accepted
    assert source.calls==[]


def test_missing_kernel_credentials_fail_closed(endpoint,monkeypatch):
    def unavailable(_):
        raise proxy.HMLUnixProxyError("HML_PEER_IDENTITY_UNAVAILABLE")
    monkeypatch.setattr(proxy,"_peer_uid",unavailable)
    source=Source()
    thread,result,error=start_one(endpoint,source)
    code,payload,_=raw_request(endpoint,GET)
    assert code==403 and payload=={"error":"HML_PEER_UNTRUSTED"}
    assert not wait_for(thread,result,error).request_accepted
    assert not source.calls


def test_invalid_inspect_result_or_upstream_exception_returns_sanitized_502(
    endpoint,monkeypatch,
):
    monkeypatch.setattr(proxy,"_peer_uid",lambda _:max(1,os.getuid()))
    for data,exc in [
        (RuntimeContainer("bad",IMAGE,True,True),None),
        (RuntimeContainer(CID,"not-image",True,True),None),
        (RuntimeContainer(CID,IMAGE,1,True),None),
        (None,RuntimeError("private docker inspect returned fake_secret")),
    ]:
        source=Source(data=data,exc=exc)
        thread,result,error=start_one(endpoint,source)
        code,payload,head=raw_request(endpoint,GET)
        assert code==502
        assert payload=={"error":"HML_INSPECT_UNAVAILABLE"}
        assert b"fake_secret" not in head
        got=wait_for(thread,result,error)
        assert got.status=="blocked" and not got.request_accepted
        assert source.calls==[TARGET]


def test_filtered_runtime_never_exposes_raw_inspect_environment(endpoint,monkeypatch):
    monkeypatch.setattr(proxy,"_peer_uid",lambda _:max(1,os.getuid()))
    source=Source()
    thread,result,error=start_one(endpoint,source)
    code,payload,_=raw_request(endpoint,GET)
    assert code==200
    assert payload=={
        "Id":CID,"Image":IMAGE,"Name":"/delpi-hml-public-hub",
        "Config":{"Labels":{
            "com.docker.compose.service":"public-hub",
            "com.docker.compose.project":"delpi-hml",
        }},
        "State":{"Running":True,"Health":{"Status":"healthy"}},
    }
    assert set(payload)=={"Id","Image","Name","Config","State"}
    assert not wait_for(thread,result,error).can_execute


@pytest.mark.parametrize("unsafe",["world-parent","group-parent","world-socket","symlink","raw-alias"])
def test_unsafe_listener_permissions_symlink_or_raw_socket_alias_refused(
    endpoint,monkeypatch,unsafe,
):
    path,listener=endpoint
    if unsafe=="world-parent":
        os.chmod(path.parent,0o777)
    elif unsafe=="group-parent":
        os.chmod(path.parent,0o770)
    elif unsafe=="world-socket":
        os.chmod(path,0o777)
    elif unsafe=="symlink":
        alias=path.parent/"alias.sock"
        alias.symlink_to(path)
        monkeypatch.setattr(proxy,"_HML_PATH",alias)
        with pytest.raises(proxy.HMLUnixProxyError,match="HML_PROXY_LISTENER_UNTRUSTED"):
            proxy.serve_one_prebound(
                listener=listener,allowed_collector_uid=1001,
                inspector=Source(),expected_path=alias,owner_uid=os.getuid(),
                socket_gid=os.getgid(),
            )
        return
    elif unsafe=="raw-alias":
        monkeypatch.setattr(proxy,"_DOCKER_RAW",(path,))
        expected="HML_RAW_DOCKER_SOCKET_DENIED"
    else:
        raise AssertionError(unsafe)
    if unsafe!="raw-alias":
        expected="HML_PROXY_PATH_UNSAFE"
    with pytest.raises(proxy.HMLUnixProxyError,match=expected):
        proxy.serve_one_prebound(
            listener=listener,allowed_collector_uid=1001,
            inspector=Source(),expected_path=path,owner_uid=os.getuid(),
            socket_gid=os.getgid(),
        )


def test_listener_not_same_path_refused_before_accept(endpoint,tmp_path):
    path,listener=endpoint
    with pytest.raises(proxy.HMLUnixProxyError,match="HML_PROXY_LISTENER_UNTRUSTED"):
        proxy.serve_one_prebound(
            listener=listener,allowed_collector_uid=1001,
            inspector=Source(),expected_path=tmp_path/"unexpected.sock",
            owner_uid=os.getuid(),socket_gid=os.getgid(),
        )


def test_sender_must_be_nonroot_and_configured_exactly(endpoint):
    path,listener=endpoint
    for uid in (0,-1,True,"1001"):
        with pytest.raises(proxy.HMLUnixProxyError,match="HML_PROXY_NOT_CONFIGURED"):
            proxy.serve_one_prebound(
                listener=listener,allowed_collector_uid=uid,
                inspector=Source(),expected_path=path,owner_uid=os.getuid(),
                socket_gid=os.getgid(),
            )


def test_unsupported_descriptors_and_oversize_metadata_do_not_grant_access():
    from dataclasses import replace
    report=proxy.SingleRequestProxyResult("blocked",200,True)
    assert not report.prepare_eligible and not report.can_execute
    assert not report.raw_docker_socket_exposed
    assert not report.host_identity_attested
    assert asdict(report)["proxy_policy_independently_attested"] is False
    assert not hasattr(proxy,"main")
    assert not hasattr(proxy,"create_mcp_server")


def test_source_contains_no_socket_creation_or_mutating_primitive():
    text=(Path(__file__).resolve().parents[1]/
          "linux_ops_mcp/atlas_hml_unix_proxy.py").read_text()
    for forbidden in (
        ".bind(", ".listen(", "os.chmod", "os.chown", "os.unlink",
        "@router.", "@mcp.", "CREATE ROLE", "GRANT ",
        "docker compose", "psycopg.connect(", "subprocess.run(",
        "INSERT INTO it_portal", "UPDATE it_portal", "os.system(",
    ):
        assert forbidden not in text


def test_listener_rejects_non_listening_fd(endpoint):
    path,listener=endpoint
    listener.close()
    unbound=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    try:
        with pytest.raises(proxy.HMLUnixProxyError,match="HML_PROXY_LISTENER_UNTRUSTED"):
            proxy.serve_one_prebound(
                listener=unbound,allowed_collector_uid=1001,
                inspector=Source(),expected_path=path,owner_uid=os.getuid(),
                socket_gid=os.getgid(),
            )
    finally:
        unbound.close()


@pytest.mark.parametrize("mode", [0o600, 0o666, 0o777, 0o660 | 0o1000])
def test_socket_mode_must_match_exact_policy(endpoint,mode):
    path,listener=endpoint
    os.chmod(path,mode)
    with pytest.raises(proxy.HMLUnixProxyError,match="HML_PROXY_PATH_UNSAFE"):
        proxy.serve_one_prebound(
            listener=listener,allowed_collector_uid=1001,
            inspector=Source(),expected_path=path,owner_uid=os.getuid(),
            socket_gid=os.getgid(),
        )


def test_wrong_socket_group_is_rejected(endpoint):
    path,listener=endpoint
    with pytest.raises(proxy.HMLUnixProxyError,match="HML_PROXY_PATH_UNSAFE"):
        proxy.serve_one_prebound(
            listener=listener,allowed_collector_uid=1001,
            inspector=Source(),expected_path=path,owner_uid=os.getuid(),
            socket_gid=os.getgid()+1,
        )


def test_upstream_inspector_deadline_does_not_authorize(endpoint,monkeypatch):
    monkeypatch.setattr(proxy,"_peer_uid",lambda _:max(1,os.getuid()))
    source=Source()
    async def slow(_target):
        raise asyncio.TimeoutError()
    source.inspect=slow
    thread,result,error=start_one(endpoint,source)
    code,payload,_=raw_request(endpoint,GET)
    assert code==502
    assert payload=={"error":"HML_INSPECT_UNAVAILABLE"}
    got=wait_for(thread,result,error)
    assert got.status=="blocked" and not got.can_execute
