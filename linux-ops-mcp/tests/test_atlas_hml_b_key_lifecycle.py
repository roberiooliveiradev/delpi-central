"""Ephemeral key lifecycle tests; no real keys, no GLPI, no host writes outside tmp."""
from __future__ import annotations

import os

import pytest

from linux_ops_mcp.atlas_hml_b_key_lifecycle import (
    GLPI_RECOVERY_ID,
    HMLKeyLifecycleError,
    build_encrypted_recovery_copy,
    clear_secret,
    generate_ephemeral_keypair,
    load_private_key_file,
    recover_private_from_encrypted,
    rotate_keyring,
    validate_key_store_directory,
    write_ephemeral_private_key,
    write_ephemeral_public_key,
)


@pytest.fixture
def keydir(tmp_path):
    root = tmp_path / "keys"
    root.mkdir()
    os.chmod(root, 0o700)
    return root


def test_generate_export_encrypt_recover_and_wipe(keydir):
    material = generate_ephemeral_keypair()
    assert material.status == "blocked"
    assert not material.custody_independent
    assert not material.can_execute
    assert len(material.private_key) == 32 and len(material.public_key) == 32
    passphrase = b"atlas-hml-recovery-passphrase"
    recovery = build_encrypted_recovery_copy(material, passphrase=passphrase)
    assert recovery.glpi_identifier == GLPI_RECOVERY_ID
    assert not recovery.passphrase_in_artifact
    assert b"PRIVATE KEY" in recovery.pkcs8_encrypted
    assert b"ENCRYPTED" in recovery.pkcs8_encrypted
    restored = recover_private_from_encrypted(
        recovery.pkcs8_encrypted,
        passphrase=passphrase,
        expected_key_id=material.key_id,
    )
    assert restored.private_key == material.private_key
    assert restored.key_id == material.key_id
    buf = bytearray(material.private_key)
    clear_secret(buf)
    assert buf == bytearray(32)


def test_private_key_file_dac_and_unsafe_mode_denied(keydir):
    material = generate_ephemeral_keypair()
    path = write_ephemeral_private_key(
        keydir, material, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    write_ephemeral_public_key(
        keydir, material, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    loaded = load_private_key_file(
        path, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    assert loaded == material.private_key
    os.chmod(path, 0o644)
    with pytest.raises(HMLKeyLifecycleError) as err:
        load_private_key_file(
            path, owner_uid=os.getuid(), expected_gid=os.getgid(),
        )
    assert err.value.code == "HML_KEY_LOAD_UNSAFE"


def test_missing_key_and_bad_directory_modes(tmp_path):
    bad = tmp_path / "open"
    bad.mkdir()
    os.chmod(bad, 0o755)
    with pytest.raises(HMLKeyLifecycleError) as err:
        validate_key_store_directory(
            bad, owner_uid=os.getuid(), expected_gid=os.getgid(),
        )
    assert err.value.code == "HML_KEY_STORE_UNSAFE"
    missing = tmp_path / "keys" / "missing.priv"
    with pytest.raises(HMLKeyLifecycleError):
        load_private_key_file(
            missing, owner_uid=os.getuid(), expected_gid=os.getgid(),
        )


def test_rotation_revokes_previous_key():
    first = generate_ephemeral_keypair()
    second = generate_ephemeral_keypair()
    ring = rotate_keyring(previous=first, successor=second)
    assert ring.active_public(second.key_id) == second.public_key
    with pytest.raises(Exception) as err:
        ring.active_public(first.key_id)
    assert "REVOKED" in str(err.value) or getattr(err.value, "code", "") == "HML_TRUST_KEY_REVOKED"


def test_wrong_passphrase_and_short_passphrase_fail(keydir):
    material = generate_ephemeral_keypair()
    with pytest.raises(HMLKeyLifecycleError) as err:
        build_encrypted_recovery_copy(material, passphrase=b"short")
    assert err.value.code == "HML_KEY_PASSPHRASE_INVALID"
    recovery = build_encrypted_recovery_copy(
        material, passphrase=b"atlas-hml-recovery-passphrase",
    )
    with pytest.raises(HMLKeyLifecycleError) as err:
        recover_private_from_encrypted(
            recovery.pkcs8_encrypted,
            passphrase=b"atlas-hml-wrong-passphrase!",
            expected_key_id=material.key_id,
        )
    assert err.value.code == "HML_KEY_RECOVERY_FAILED"
