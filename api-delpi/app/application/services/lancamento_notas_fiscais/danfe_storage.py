"""DANFE persistido do lançamento de notas. Metadado fica no banco."""
from __future__ import annotations

from pathlib import Path

from app.config import settings

MAX_DANFE_BYTES = 10_485_760


class LancamentoDanfeStorageError(ValueError):
    pass


class LancamentoDanfeStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.LNF_DANFE_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, *, request_id: str, content: bytes) -> str:
        stored_name = _stored_name(request_id)
        if not content.startswith(b"%PDF"):
            raise LancamentoDanfeStorageError("O DANFE não é um PDF válido.")
        if len(content) > MAX_DANFE_BYTES:
            raise LancamentoDanfeStorageError("O DANFE excede o tamanho permitido.")
        target = self._resolve(stored_name)
        target.write_bytes(content)
        return stored_name

    def read(self, stored_name: str) -> bytes:
        path = self._resolve(stored_name)
        if not path.is_file():
            raise LancamentoDanfeStorageError("Arquivo do DANFE não encontrado.")
        return path.read_bytes()

    def delete(self, stored_name: str) -> None:
        path = self._resolve(stored_name)
        if path.is_file():
            path.unlink()

    def _resolve(self, stored_name: str) -> Path:
        safe = Path(stored_name).name
        if safe != stored_name or not safe.endswith(".pdf"):
            raise LancamentoDanfeStorageError("Nome de arquivo inválido.")
        target = (self.base_dir / safe).resolve()
        if self.base_dir.resolve() not in target.parents:
            raise LancamentoDanfeStorageError("Nome de arquivo inválido.")
        return target


def _stored_name(request_id: str) -> str:
    normalized = str(request_id or "").strip().lower()
    if len(normalized) != 36 or normalized.count("-") != 4:
        raise LancamentoDanfeStorageError("Solicitação inválida para gravar o DANFE.")
    return f"{normalized}.pdf"
