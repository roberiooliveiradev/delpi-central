"""Gravação atômica do XML no diretório monitorado pelo importador.

O temporário fica no mesmo filesystem do destino. O nome final só aparece
depois do rename. O importador não deve ver um `.xml` incompleto.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from uuid import uuid4

from financial_app.domain.errors import NfeExportConfigurationError

_FINAL_NAME = re.compile(r"^NFe-\d{44}\.xml$")


class NfeXmlExportStorage:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def filename(self, access_key: str) -> str:
        key = _access_key(access_key)
        return f"NFe-{key}.xml"

    def exists(self, access_key: str) -> bool:
        path = self._final_path(access_key)
        return path.is_file() and not path.is_symlink()

    def read(self, access_key: str) -> bytes:
        path = self._final_path(access_key)
        if path.is_symlink() or not path.is_file():
            raise NfeExportConfigurationError("Arquivo final da NF-e indisponível.")
        return path.read_bytes()

    def remove(self, access_key: str) -> None:
        path = self._final_path(access_key)
        if path.is_symlink():
            raise NfeExportConfigurationError("Arquivo final da NF-e indisponível.")
        if path.is_file():
            path.unlink()

    def write_atomic(self, access_key: str, payload: bytes) -> str:
        final_name = self.filename(access_key)
        final_path = self._final_path(access_key)
        if final_path.exists() or final_path.is_symlink():
            raise NfeExportConfigurationError("O XML final já existe e não será sobrescrito.")
        temporary = self._directory / f".NFe-{_access_key(access_key)}.{uuid4().hex}.part"
        if temporary.suffix == ".xml" or temporary.name.endswith(".xml"):
            raise NfeExportConfigurationError("Nome temporário inválido.")
        try:
            with temporary.open("wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, final_path)
            _fsync_directory(self._directory)
        except Exception:
            if temporary.exists():
                temporary.unlink()
            raise
        return final_name

    def _final_path(self, access_key: str) -> Path:
        name = self.filename(access_key)
        if not _FINAL_NAME.fullmatch(name):
            raise NfeExportConfigurationError("Nome final da NF-e inválido.")
        path = self._directory / name
        if path.parent != self._directory:
            raise NfeExportConfigurationError("Caminho final da NF-e inválido.")
        return path


def validate_export_directory(path: str, *, application_root: Path) -> Path:
    raw = (path or "").strip()
    if not raw:
        raise NfeExportConfigurationError("Diretório de exportação ausente.")
    candidate = Path(raw)
    if not candidate.is_absolute():
        raise NfeExportConfigurationError("Diretório de exportação precisa ser absoluto.")
    resolved = candidate.resolve()
    if resolved == Path("/"):
        raise NfeExportConfigurationError("Diretório de exportação inválido.")
    application = application_root.resolve()
    if resolved == application or _is_relative_to(resolved, application) or _is_relative_to(application, resolved):
        raise NfeExportConfigurationError("Diretório de exportação inválido.")
    if not resolved.exists() or not resolved.is_dir():
        raise NfeExportConfigurationError("Diretório de exportação inexistente.")
    if not os.access(resolved, os.W_OK):
        raise NfeExportConfigurationError("Diretório de exportação sem permissão de escrita.")
    return resolved


def _access_key(value: str) -> str:
    key = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(key) != 44:
        raise NfeExportConfigurationError("Chave da NF-e inválida para o arquivo.")
    return key


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return path != parent
