"""Ed25519 key lifecycle candidate for ATLAS HML local signing (source-only).

Generates ephemeral material, exports public fingerprints, builds PKCS#8
encrypted recovery copies and validates key-store directory DAC. NEVER writes
real operational keys to Git, never logs private material, never calls GLPI.
Root on the same host can still read any local private key; this is not an
independent cryptographic trust domain.
"""
from __future__ import annotations

import os
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    PrivateFormat,
    PublicFormat,
)

from .atlas_hml_b_snapshot_trust import (
    HMLSnapshotTrustError,
    build_keyring,
    key_id_for_public_key,
)

GLPI_RECOVERY_ID = "ATLAS-HML-ED25519-PRIVATE-V1"
_DIR_MODE = 0o700
_PRIV_MODE = 0o600
_PUB_MODE = 0o644
_MAX_PASSPHRASE = 256
_MIN_PASSPHRASE = 16
_BLOCKS = (
    "LOCAL_KEY_CUSTODY_SAME_HOST_AS_ROOT",
    "GLPI_RECOVERY_COPY_IS_OPERATOR_MANAGED",
    "KEY_MATERIAL_MUST_NOT_LIVE_IN_GIT",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLKeyLifecycleError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLKeyMaterial:
    key_id: str
    public_key: bytes
    private_key: bytes
    status: str = "blocked"
    custody_independent: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


@dataclass(frozen=True, slots=True)
class HMLEncryptedRecoveryCopy:
    key_id: str
    glpi_identifier: str
    pkcs8_encrypted: bytes
    status: str = "blocked"
    passphrase_in_artifact: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


@dataclass(frozen=True, slots=True)
class HMLKeyStoreLayout:
    directory: Path
    private_name: str = "atlas-hml-ed25519.priv"
    public_name: str = "atlas-hml-ed25519.pub"
    status: str = "blocked"
    host_installed: bool = False


def generate_ephemeral_keypair() -> HMLKeyMaterial:
    """CI/tmp-only. Do not persist the returned private key outside fixtures."""
    private = Ed25519PrivateKey.generate()
    private_raw = private.private_bytes_raw()
    public_raw = private.public_key().public_bytes_raw()
    return HMLKeyMaterial(
        key_id=key_id_for_public_key(public_raw),
        public_key=public_raw,
        private_key=private_raw,
    )


def export_public_raw(public_key: bytes) -> bytes:
    """Return the canonical 32-byte public key after format validation."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if type(public_key) is not bytes or len(public_key) != 32:
        raise HMLKeyLifecycleError("HML_KEY_PUBLIC_INVALID")
    try:
        return Ed25519PublicKey.from_public_bytes(public_key).public_bytes(
            Encoding.Raw, PublicFormat.Raw,
        )
    except (ValueError, TypeError):
        raise HMLKeyLifecycleError("HML_KEY_PUBLIC_INVALID") from None


def build_encrypted_recovery_copy(
    material: HMLKeyMaterial, *, passphrase: bytes,
) -> HMLEncryptedRecoveryCopy:
    """PKCS#8 encrypted recovery blob for offline GLPI custody (operator-managed)."""
    if type(material) is not HMLKeyMaterial:
        raise HMLKeyLifecycleError("HML_KEY_INPUT_INVALID")
    if (
        type(passphrase) is not bytes
        or not _MIN_PASSPHRASE <= len(passphrase) <= _MAX_PASSPHRASE
        or b"\x00" in passphrase
    ):
        raise HMLKeyLifecycleError("HML_KEY_PASSPHRASE_INVALID")
    if type(material.private_key) is not bytes or len(material.private_key) != 32:
        raise HMLKeyLifecycleError("HML_KEY_PRIVATE_INVALID")
    try:
        private = Ed25519PrivateKey.from_private_bytes(material.private_key)
        encrypted = private.private_bytes(
            Encoding.PEM,
            PrivateFormat.PKCS8,
            BestAvailableEncryption(passphrase),
        )
    except (ValueError, TypeError):
        raise HMLKeyLifecycleError("HML_KEY_ENCRYPT_FAILED") from None
    return HMLEncryptedRecoveryCopy(
        key_id=material.key_id,
        glpi_identifier=GLPI_RECOVERY_ID,
        pkcs8_encrypted=encrypted,
    )


def recover_private_from_encrypted(
    encrypted: bytes, *, passphrase: bytes, expected_key_id: str,
) -> HMLKeyMaterial:
    """Fixture/recovery drill only. Never used by the presenter or MCP."""
    if (
        type(encrypted) is not bytes or not 64 <= len(encrypted) <= 8192
        or type(passphrase) is not bytes
        or not _MIN_PASSPHRASE <= len(passphrase) <= _MAX_PASSPHRASE
        or type(expected_key_id) is not str
    ):
        raise HMLKeyLifecycleError("HML_KEY_RECOVERY_INPUT_INVALID")
    try:
        private = serialization.load_pem_private_key(encrypted, password=passphrase)
        if not isinstance(private, Ed25519PrivateKey):
            raise TypeError("not ed25519")
        private_raw = private.private_bytes_raw()
        public_raw = private.public_key().public_bytes_raw()
    except (ValueError, TypeError):
        raise HMLKeyLifecycleError("HML_KEY_RECOVERY_FAILED") from None
    key_id = key_id_for_public_key(public_raw)
    if key_id != expected_key_id:
        raise HMLKeyLifecycleError("HML_KEY_RECOVERY_IDENTITY_MISMATCH")
    return HMLKeyMaterial(
        key_id=key_id, public_key=public_raw, private_key=private_raw,
    )


def validate_key_store_directory(
    directory: Path, *, owner_uid: int, expected_gid: int,
) -> HMLKeyStoreLayout:
    """Fail-closed DAC check for a disposable key directory."""
    if (
        type(directory) is not type(Path("/")) or not directory.is_absolute()
        or type(owner_uid) is not int or owner_uid < 0
        or type(expected_gid) is not int or expected_gid < 0
    ):
        raise HMLKeyLifecycleError("HML_KEY_STORE_INPUT_INVALID")
    try:
        st = os.stat(directory, follow_symlinks=False)
    except OSError:
        raise HMLKeyLifecycleError("HML_KEY_STORE_UNAVAILABLE") from None
    if (
        not stat.S_ISDIR(st.st_mode)
        or st.st_uid != owner_uid
        or st.st_gid != expected_gid
        or stat.S_IMODE(st.st_mode) != _DIR_MODE
        or st.st_nlink < 2
    ):
        raise HMLKeyLifecycleError("HML_KEY_STORE_UNSAFE")
    return HMLKeyStoreLayout(directory=directory)


def write_ephemeral_private_key(
    directory: Path, material: HMLKeyMaterial, *,
    owner_uid: int, expected_gid: int,
) -> Path:
    """Write private key into a disposable directory with 0600. Fixture only."""
    layout = validate_key_store_directory(
        directory, owner_uid=owner_uid, expected_gid=expected_gid,
    )
    if type(material) is not HMLKeyMaterial or len(material.private_key) != 32:
        raise HMLKeyLifecycleError("HML_KEY_PRIVATE_INVALID")
    path = layout.directory / layout.private_name
    staged = layout.directory / (".stage-" + secrets.token_hex(8))
    try:
        fd = os.open(
            staged, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
        )
        try:
            if os.fstat(fd).st_gid != expected_gid:
                os.fchown(fd, owner_uid, expected_gid)
            os.fchmod(fd, _PRIV_MODE)
            os.write(fd, material.private_key)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(staged, path)
    except OSError:
        try:
            staged.unlink(missing_ok=True)
        except OSError:
            pass
        raise HMLKeyLifecycleError("HML_KEY_WRITE_FAILED") from None
    return path


def write_ephemeral_public_key(
    directory: Path, material: HMLKeyMaterial, *,
    owner_uid: int, expected_gid: int,
) -> Path:
    layout = validate_key_store_directory(
        directory, owner_uid=owner_uid, expected_gid=expected_gid,
    )
    path = layout.directory / layout.public_name
    try:
        path.write_bytes(material.public_key + b"\n" + material.key_id.encode("ascii") + b"\n")
        os.chmod(path, _PUB_MODE)
    except OSError:
        raise HMLKeyLifecycleError("HML_KEY_WRITE_FAILED") from None
    return path


def load_private_key_file(
    path: Path, *, owner_uid: int, expected_gid: int,
) -> bytes:
    """Load 32-byte raw private key with strict DAC. Never log the bytes."""
    if (
        type(path) is not type(Path("/")) or not path.is_absolute()
        or type(owner_uid) is not int or owner_uid < 0
        or type(expected_gid) is not int or expected_gid < 0
    ):
        raise HMLKeyLifecycleError("HML_KEY_LOAD_INPUT_INVALID")
    fd = -1
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        st = os.fstat(fd)
        if (
            not stat.S_ISREG(st.st_mode)
            or st.st_uid != owner_uid
            or st.st_gid != expected_gid
            or stat.S_IMODE(st.st_mode) != _PRIV_MODE
            or st.st_nlink != 1
            or st.st_size != 32
        ):
            raise HMLKeyLifecycleError("HML_KEY_LOAD_UNSAFE")
        data = os.read(fd, 33)
        if len(data) != 32:
            raise HMLKeyLifecycleError("HML_KEY_LOAD_UNSAFE")
        return data
    except HMLKeyLifecycleError:
        raise
    except OSError:
        raise HMLKeyLifecycleError("HML_KEY_LOAD_UNAVAILABLE") from None
    finally:
        if fd >= 0:
            os.close(fd)


def rotate_keyring(
    *, previous: HMLKeyMaterial, successor: HMLKeyMaterial,
):
    """Public keyring with previous revoked and successor active."""
    if type(previous) is not HMLKeyMaterial or type(successor) is not HMLKeyMaterial:
        raise HMLKeyLifecycleError("HML_KEY_INPUT_INVALID")
    if previous.key_id == successor.key_id:
        raise HMLKeyLifecycleError("HML_KEY_ROTATION_IDENTITY_COLLISION")
    try:
        return build_keyring(
            active=((successor.key_id, successor.public_key),),
            revoked=((previous.key_id, previous.public_key),),
        )
    except HMLSnapshotTrustError as exc:
        raise HMLKeyLifecycleError(exc.code) from None


def clear_secret(buffer: bytearray | bytes) -> None:
    """Best-effort wipe for temporary bytearrays; bytes are immutable."""
    if type(buffer) is bytearray:
        for index in range(len(buffer)):
            buffer[index] = 0
