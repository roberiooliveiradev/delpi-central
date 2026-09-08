from __future__ import annotations

from pathlib import Path

from production_pulse_app.infrastructure.storage.firmware_artifact_storage import (
    FirmwareArtifactStorage,
    FirmwareArtifactStorageError,
)


def test_firmware_artifact_storage_save_read_and_sha(tmp_path: Path):
    storage = FirmwareArtifactStorage(base_dir=str(tmp_path), max_bytes=1024)
    raw = b"firmware-bytes-v1"
    saved = storage.save(
        firmware_key="esp8266_counter_v1",
        version="1.2.0",
        raw=raw,
        filename_hint="counter.bin",
    )
    assert saved.size_bytes == len(raw)
    assert len(saved.sha256) == 64
    assert saved.relative_path.endswith(".bin")
    assert storage.read(saved.relative_path) == raw
    assert storage.open_path(saved.relative_path).is_file()


def test_firmware_artifact_storage_rejects_empty_and_traversal(tmp_path: Path):
    storage = FirmwareArtifactStorage(base_dir=str(tmp_path), max_bytes=16)
    try:
        storage.save(firmware_key="k", version="1.0.0", raw=b"")
        assert False, "expected empty_artifact"
    except FirmwareArtifactStorageError as exc:
        assert str(exc) == "empty_artifact"

    try:
        storage.save(firmware_key="k", version="1.0.0", raw=b"x" * 32)
        assert False, "expected artifact_too_large"
    except FirmwareArtifactStorageError as exc:
        assert str(exc) == "artifact_too_large"

    try:
        storage.read("../outside.bin")
        assert False, "expected invalid_artifact_path"
    except FirmwareArtifactStorageError as exc:
        assert str(exc) == "invalid_artifact_path"
