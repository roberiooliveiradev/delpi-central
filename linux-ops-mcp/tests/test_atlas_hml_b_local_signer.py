"""Local signer security tests on disposable fixtures only."""
from __future__ import annotations

import os
import socket
import threading
from datetime import datetime, timezone

import pytest

from linux_ops_mcp.atlas_hml_b_external_signing_intent import (
    prepare_signing_intent,
    seal_externally_signed_intent,
)
from linux_ops_mcp.atlas_hml_b_key_lifecycle import (
    generate_ephemeral_keypair,
    write_ephemeral_private_key,
)
from linux_ops_mcp.atlas_hml_b_local_signer import (
    HMLLocalSigner,
    HMLLocalSignerError,
    _serve_one_local_sign_request,
    encode_local_sign_request,
)
from linux_ops_mcp.atlas_hml_b_snapshot_trust import build_keyring
from linux_ops_mcp.deploy_host_source import RuntimeContainer

_NOW = datetime(2026, 11, 18, 1, 0, tzinfo=timezone.utc)
_CONTAINER = RuntimeContainer(
    container_id="a" * 64,
    image_id="sha256:" + "b" * 64,
    running=True,
    healthy=True,
)


@pytest.fixture
def material(tmp_path):
    root = tmp_path / "signer-keys"
    root.mkdir()
    os.chmod(root, 0o700)
    keys = generate_ephemeral_keypair()
    path = write_ephemeral_private_key(
        root, keys, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    return keys, path, root


def _intent(keys, generation=1, observed=_NOW):
    return prepare_signing_intent(
        _CONTAINER, observed_at=observed,
        generation=generation, key_id=keys.key_id,
    )


@pytest.mark.skipif(os.getuid() == 0, reason="peer UID fixtures require non-root")
def test_valid_sign_verify_and_no_private_key_leak(material):
    keys, path, _ = material
    signer = HMLLocalSigner.from_key_file(
        path, public_key=keys.public_key,
        owner_uid=os.getuid(), expected_gid=os.getgid(),
        allowed_peer_uids=frozenset({os.getuid()}),
    )
    intent = _intent(keys)
    result = signer.sign_intent(
        intent, now=_NOW, peer_uid=os.getuid(), expected_generation=1,
    )
    assert result.status == "blocked"
    assert not result.authenticity_independent
    assert not result.can_execute
    assert len(result.signature) == 64
    ring = build_keyring(active=((keys.key_id, keys.public_key),))
    sealed = seal_externally_signed_intent(
        intent, signature=result.signature, keyring=ring, now=_NOW,
    )
    assert sealed.signature_verified
    assert b"PRIVATE" not in sealed.envelope


def test_wrong_key_peer_prod_scope_and_generic_api_denied(material):
    keys, path, _ = material
    signer = HMLLocalSigner.from_key_file(
        path, public_key=keys.public_key,
        owner_uid=os.getuid(), expected_gid=os.getgid(),
        allowed_peer_uids=frozenset({os.getuid()}),
    )
    intent = _intent(keys)
    with pytest.raises(HMLLocalSignerError) as err:
        signer.sign_intent(
            intent, now=_NOW, peer_uid=os.getuid() + 1, expected_generation=1,
        )
    assert err.value.code == "HML_LOCAL_SIGNER_PEER_DENIED"
    with pytest.raises(HMLLocalSignerError):
        signer.refuse_arbitrary_bytes(b"sign-anything")
    # Missing key file
    missing = path.with_name("gone.priv")
    with pytest.raises(HMLLocalSignerError):
        HMLLocalSigner.from_key_file(
            missing, public_key=keys.public_key,
            owner_uid=os.getuid(), expected_gid=os.getgid(),
            allowed_peer_uids=frozenset({os.getuid()}),
        )


def test_replay_and_generation_regression_halt(material):
    keys, path, _ = material
    signer = HMLLocalSigner.from_key_file(
        path, public_key=keys.public_key,
        owner_uid=os.getuid(), expected_gid=os.getgid(),
        allowed_peer_uids=frozenset({os.getuid()}),
    )
    intent = _intent(keys, generation=1)
    signer.sign_intent(
        intent, now=_NOW, peer_uid=os.getuid(), expected_generation=1,
    )
    with pytest.raises(HMLLocalSignerError) as err:
        signer.sign_intent(
            intent, now=_NOW, peer_uid=os.getuid(), expected_generation=1,
        )
    assert err.value.code == "HML_LOCAL_SIGNER_REPLAY"
    assert signer.halted


def test_tampered_intent_signing_bytes_denied(material):
    keys, path, _ = material
    signer = HMLLocalSigner.from_key_file(
        path, public_key=keys.public_key,
        owner_uid=os.getuid(), expected_gid=os.getgid(),
        allowed_peer_uids=frozenset({os.getuid()}),
    )
    intent = _intent(keys)
    bad = type(intent)(
        payload=intent.payload,
        generation=intent.generation,
        produced_at=intent.produced_at,
        key_id=intent.key_id,
        signing_bytes=intent.signing_bytes[:-1] + bytes([intent.signing_bytes[-1] ^ 1]),
    )
    with pytest.raises(HMLLocalSignerError) as err:
        signer.sign_intent(
            bad, now=_NOW, peer_uid=os.getuid(), expected_generation=1,
        )
    assert err.value.code == "HML_SIGNING_INTENT_SCOPE_DENIED"


@pytest.mark.skipif(os.getuid() == 0, reason="peer UID fixtures require non-root")
def test_uds_sign_request_roundtrip(material, tmp_path):
    keys, path, _ = material
    signer = HMLLocalSigner.from_key_file(
        path, public_key=keys.public_key,
        owner_uid=os.getuid(), expected_gid=os.getgid(),
        allowed_peer_uids=frozenset({os.getuid()}),
    )
    sock_path = tmp_path / "signer.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(sock_path))
    os.chmod(sock_path, 0o660)
    listener.listen(1)
    intent = _intent(keys)
    result_box, errors = [], []

    def run():
        try:
            result_box.append(_serve_one_local_sign_request(
                listener=listener, signer=signer,
                expected_path=sock_path, now=_NOW, expected_generation=1,
            ))
        except BaseException as exc:
            errors.append(exc)
        finally:
            listener.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(4)
        client.connect(str(sock_path))
        client.sendall(encode_local_sign_request(intent))
        client.shutdown(socket.SHUT_WR)
        response = client.recv(4096)
    thread.join(6)
    assert not errors, repr(errors)
    assert b"signature_b64" in response
    assert b'"status":"blocked"' in response
    assert result_box and result_box[0].status == "blocked"
