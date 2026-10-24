"""Storage de evidências P2-Upload — binário em volume persistente.

Sequência C2 (doc 103): write `.part` em chunks com cap mid-stream →
sha256 durante a gravação → `os.replace()` atômico no mesmo mount →
metadados em transação Postgres (feita pelo caller). Falha na
persistência ⇒ `remove()` como compensação; falha na compensação é
registrada em log — nunca sucesso falso.

Nenhuma atomicidade distribuída é reivindicada: `.part` e binários
órfãos (sem linha em `document_file`) são identificáveis por varredura
e pertencem a housekeeping futura especificada separadamente.
"""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import Iterable

from controllership_finance_app.config import settings
from controllership_finance_app.domain.closing_checklist.errors import (
    FileMissing,
    FileTooLarge,
)
from controllership_finance_app.domain.closing_documents.file_validation import (
    MAX_FILE_BYTES,
)

logger = logging.getLogger(__name__)

_TMP_DIRNAME = ".tmp"


class ClosingDocumentStorage:
    """Adapter de filesystem — layout `{competence_id}/{uuid}{ext}`."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.CF_DOCUMENT_UPLOAD_DIR)
        self.tmp_dir = self.base_dir / _TMP_DIRNAME
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    # -- escrita C2 -----------------------------------------------------------

    def write_temp(
        self, file_uuid: uuid.UUID, chunks: Iterable[bytes]
    ) -> tuple[Path, str, int]:
        """Grava `.part` em chunks com cap 25 MB *durante* o stream.

        Retorna ``(tmp_path, sha256_hex, size_bytes)``. Qualquer falha
        remove o parcial — `.part` nunca é publicado.
        """
        tmp_path = self.tmp_dir / f"{file_uuid.hex}.part"
        digest = hashlib.sha256()
        size = 0
        try:
            with tmp_path.open("wb") as out:
                for chunk in chunks:
                    if not chunk:
                        continue
                    size += len(chunk)
                    if size > MAX_FILE_BYTES:
                        raise FileTooLarge(
                            "O arquivo excede o limite de 25 MB."
                        )
                    digest.update(chunk)
                    out.write(chunk)
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise
        return tmp_path, digest.hexdigest(), size

    def publish(
        self,
        tmp_path: Path,
        *,
        competence_id: str,
        file_uuid: uuid.UUID,
        extension: str,
    ) -> tuple[str, str, Path]:
        """Publica o `.part` como arquivo final via `os.replace` atômico.

        Retorna ``(storage_key, stored_name, final_path)``.
        """
        safe_extension = extension if extension.startswith(".") else ".bin"
        stored_name = f"{file_uuid.hex}{safe_extension}"
        rel_dir = Path(competence_id)
        target_dir = self.base_dir / rel_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        final_path = target_dir / stored_name
        os.replace(tmp_path, final_path)
        return f"{competence_id}/{stored_name}", stored_name, final_path

    # -- leitura / compensação -------------------------------------------------

    def resolve(self, storage_key: str) -> Path:
        """Resolve key → path existente; traversal ⇒ erro, ausente ⇒ 503."""
        base = self.base_dir.resolve()
        normalized = (storage_key or "").strip().lstrip("/")
        if (
            not normalized
            or ".." in normalized.split("/")
            or normalized.startswith(_TMP_DIRNAME + "/")
        ):
            raise FileMissing("Referência de arquivo inválida.")
        path = (self.base_dir / normalized).resolve()
        if not str(path).startswith(str(base)):
            raise FileMissing("Referência de arquivo inválida.")
        if not path.is_file():
            raise FileMissing(
                "O conteúdo do documento não está disponível."
            )
        return path

    def remove(self, storage_key: str) -> bool:
        """Compensação: remove binário final. Falha ⇒ log + False."""
        try:
            path = self.resolve(storage_key)
        except FileMissing:
            return True
        try:
            path.unlink(missing_ok=True)
            return True
        except OSError:
            logger.warning(
                "compensation_unlink_failed storage_key=%s", storage_key
            )
            return False

    def discard_temp(self, file_uuid: uuid.UUID) -> None:
        (self.tmp_dir / f"{file_uuid.hex}.part").unlink(missing_ok=True)
