"""PRC-REF-023 — adapters de armazenamento de bytes de anexos.

``LocalVolumeAttachmentStorage`` implementa o padrão canônico
``persistent-upload-storage``: metadado no banco + binário em volume
montado (``DELPI_DATA_HOST_DIR`` → ``ENG_PRC_ATTACHMENTS_DIR``).
``MemoryAttachmentStorage`` serve a dev/testes sem filesystem.
"""

from __future__ import annotations

from pathlib import Path


class AttachmentStorageError(RuntimeError):
    """Falha de I/O no storage — mapeada a 503 pela API."""


class LocalVolumeAttachmentStorage:
    def __init__(self, root: str):
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # storage_key é gerado internamente (uuid), mas blinda traversal.
        if ".." in key or key.startswith("/"):
            raise AttachmentStorageError("storage key inválida")
        return self._root / key

    def save(self, key: str, content: bytes) -> None:
        path = self._path(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(content)
            tmp.replace(path)
        except OSError as exc:
            raise AttachmentStorageError(
                f"falha ao gravar anexo: {exc.__class__.__name__}"
            ) from exc

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def open_path(self, key: str) -> Path:
        path = self._path(key)
        if not path.is_file():
            raise AttachmentStorageError("arquivo não encontrado no storage")
        return path

    def delete(self, key: str) -> None:
        try:
            self._path(key).unlink(missing_ok=True)
        except OSError:
            pass


class MemoryAttachmentStorage:
    """Storage volátil — testes e modo ENG_PRC_REPOSITORY=memory."""

    def __init__(self):
        self._blobs: dict[str, bytes] = {}

    def save(self, key: str, content: bytes) -> None:
        if ".." in key or key.startswith("/"):
            raise AttachmentStorageError("storage key inválida")
        self._blobs[key] = content

    def exists(self, key: str) -> bool:
        return key in self._blobs

    def open_path(self, key: str):
        if key not in self._blobs:
            raise AttachmentStorageError("arquivo não encontrado no storage")
        import io

        return io.BytesIO(self._blobs[key])

    def delete(self, key: str) -> None:
        self._blobs.pop(key, None)
