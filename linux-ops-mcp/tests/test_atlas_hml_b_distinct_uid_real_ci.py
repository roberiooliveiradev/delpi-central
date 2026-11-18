"""ATLAS 65. Linux UID split in disposable GitHub CI ONLY; not a deploy test."""
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from linux_ops_mcp.atlas_hml_b_key_lifecycle import (
    generate_ephemeral_keypair, write_ephemeral_private_key,
)
from linux_ops_mcp.atlas_hml_snapshot_publisher_candidate import (
    _publish_in_review_directory, build_hml_snapshot_claim,
)
from linux_ops_mcp.deploy_host_source import RuntimeContainer

ENABLED = (
    sys.platform.startswith("linux") and os.getuid() == 0
    and os.environ.get("GITHUB_ACTIONS") == "true"
    and os.environ.get("ATLAS_DISPOSABLE_DOCKER") == "true"
    and os.environ.get("ATLAS_REAL_HML_CHAIN_CI") == "true"
)
pytestmark = pytest.mark.skipif(not ENABLED, reason="elevated ephemeral GitHub runner only")
SUID, SGID, BUID, BGID = 61021, 61021, 61022, 61022
CONTAINER = RuntimeContainer(
    container_id="a"*64, image_id="sha256:"+"b"*64, running=True, healthy=True,
)
SIGNER = r"""
import base64, os, socket, sys
from pathlib import Path
from datetime import datetime
from linux_ops_mcp.atlas_hml_b_continuity_store import HMLContinuityStore
from linux_ops_mcp.atlas_hml_b_local_signer import HMLLocalSigner, _serve_one_local_sign_request
key, pub, sock, state, now, gen, genesis, buid, bgid = sys.argv[1:]
signer = HMLLocalSigner.from_key_file(
    Path(key), public_key=base64.b64decode(pub),
    owner_uid=os.getuid(), expected_gid=os.getgid(),
    allowed_peer_uids=frozenset({int(buid)}),
    checkpoint_store=HMLContinuityStore(
        Path(state), owner_uid=os.getuid(), expected_gid=os.getgid(),
    ),
    disposable_genesis=(genesis == "true"),
)
listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    listener.bind(sock)  # CRITICAL: bind after subprocess drops UID
    os.chmod(sock, 0o660)
    listener.listen(1)   # CRITICAL: listen after UID drop
    st = os.stat(sock, follow_symlinks=False)
    assert st.st_uid == os.getuid() and st.st_gid == int(bgid)
    assert (st.st_mode & 0o7777) == 0o660
    result = _serve_one_local_sign_request(
        listener=listener, signer=signer, expected_path=Path(sock),
        now=datetime.fromisoformat(now), expected_generation=int(gen),
    )
    assert result is not None and not result.can_execute
finally:
    listener.close()
"""
BRIDGE = r"""
import base64, json, os, socket, sys
from pathlib import Path
from datetime import datetime
from linux_ops_mcp.atlas_hml_b_nonroot_sign_bridge import (
    build_nonroot_signing_intent, request_signature_via_nonroot_uds,
)
from linux_ops_mcp.atlas_hml_b_snapshot_trust import build_keyring
handoff, sockpath, key, pub, kid, now, gen, suid, bgid = sys.argv[1:]
assert os.getuid() != 0 and os.getgroups() == []
try:
    open(key, "rb").read(1)
except PermissionError:
    pass
else:
    raise AssertionError("BRIDGE_PRIVATE_KEY_LEAK")
for endpoint in ("/run/docker.sock", "/var/run/docker.sock"):
    if os.path.exists(endpoint):
        s = socket.socket(socket.AF_UNIX)
        try:
            s.connect(endpoint)
        except PermissionError:
            pass
        else:
            raise AssertionError("BRIDGE_DOCKER_SOCKET_ACCESS")
        finally:
            s.close()
intent = build_nonroot_signing_intent(
    directory=Path(handoff), owner_uid=0, expected_gid=int(bgid),
    generation=int(gen), key_id=kid, now=datetime.fromisoformat(now),
)
out = request_signature_via_nonroot_uds(
    intent, socket_path=Path(sockpath),
    expected_socket_owner_uid=int(suid), expected_socket_gid=int(bgid),
    expected_signer_uid=int(suid),
    keyring=build_keyring(active=((kid, base64.b64decode(pub)),)),
    now=datetime.fromisoformat(now),
)
assert out.status == "blocked" and not out.can_execute and not out.prepare_eligible
assert not out.host_isolation_attested
print(json.dumps({"generation":out.generation,"status":out.status}))
"""
ROOT_PREBOUND = r"""
import socket, struct, sys
s=socket.socket(socket.AF_UNIX);s.connect(sys.argv[1])
print(struct.unpack("3i",s.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))[1])
s.close()
"""

def child(script, args, uid, gid, source=None):
    child_env = {**os.environ, "PYTHONDONTWRITEBYTECODE":"1"}
    if source is not None:
        child_env["PYTHONPATH"] = str(source)
    return subprocess.Popen(
        [sys.executable, "-B", "-c", script, *map(str, args)],
        user=uid, group=gid, extra_groups=[], close_fds=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=child_env,
    )

def done(proc):
    out, err = proc.communicate(timeout=10)
    assert proc.returncode == 0, err.decode(errors="replace")[-1500:]
    return out.decode().strip()

def make_dir(path, uid, gid, mode):
    path.mkdir()
    os.chown(path, uid, gid)
    os.chmod(path, mode)

def sandbox():
    p=Path(tempfile.mkdtemp(prefix="atlas65-",dir="/tmp"))
    p.chmod(0o755)
    return p

def test_root_listen_is_reported_as_root_even_with_nonroot_client():
    root=sandbox()
    try:
        parent=root/"root-listener"
        make_dir(parent, 0, BGID, 0o750)
        path=parent/"sign.sock"
        sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        try:
            sock.bind(str(path))
            os.chown(path,0,BGID)
            os.chmod(path,0o660)
            sock.listen(1)
            assert done(child(ROOT_PREBOUND,[path],BUID,BGID))=="0"
        finally:
            sock.close()
    finally:
        shutil.rmtree(root)

def test_signer_owned_socket_two_real_uids_replay_safe_restart():
    root=sandbox()
    try:
        handoff=root/"handoff"
        keydir=root/"keys"
        state=root/"state"
        sockdir=root/"sockdir"
        make_dir(handoff,0,BGID,0o750)
        make_dir(keydir,SUID,SGID,0o700)
        make_dir(state,SUID,SGID,0o750)
        make_dir(sockdir,SUID,BGID,0o2750)
        source=root/"source"
        source.mkdir(mode=0o755)
        shutil.copytree(
            Path(__file__).resolve().parents[1]/"linux_ops_mcp",
            source/"linux_ops_mcp",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        for location, subdirs, files in os.walk(source):
            os.chmod(location, 0o755)
            for filename in files:
                os.chmod(Path(location)/filename, 0o644)
        keys=generate_ephemeral_keypair()
        key=write_ephemeral_private_key(
            keydir,keys,owner_uid=SUID,expected_gid=SGID,
        )
        pub=base64.b64encode(keys.public_key).decode("ascii")
        socketpath=sockdir/"sign.sock"
        first=datetime.now(timezone.utc).replace(microsecond=0)
        for gen in (1,2):
            when=first+timedelta(seconds=gen-1)
            _publish_in_review_directory(
                handoff, raw=build_hml_snapshot_claim(CONTAINER,observed_at=when),
                owner_uid=0,expected_gid=BGID,now=when,
            )
            socketpath.unlink(missing_ok=True)
            signer=child(SIGNER,[
                key,pub,socketpath,state,when.isoformat(),gen,
                "true" if gen==1 else "false",BUID,BGID,
            ],SUID,SGID,source=source)
            try:
                for _ in range(200):
                    if socketpath.exists() or signer.poll() is not None:
                        break
                    time.sleep(.03)
                assert socketpath.exists() and signer.poll() is None, done(signer)
                bridge=child(BRIDGE,[
                    handoff,socketpath,key,pub,keys.key_id,when.isoformat(),
                    gen,SUID,BGID,
                ],BUID,BGID,source=source)
                assert json.loads(done(bridge))=={"generation":gen,"status":"blocked"}
                done(signer)
            finally:
                if signer.poll() is None:
                    signer.kill()
                    signer.wait(timeout=3)
        assert (state/"continuity-state.v1.json").is_file()
    finally:
        shutil.rmtree(root)
