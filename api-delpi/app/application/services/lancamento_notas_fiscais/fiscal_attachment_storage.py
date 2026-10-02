"""XML fiscal persistido no mesmo volume do DANFE. O bytes original não é reescrito."""

from __future__ import annotations

from pathlib import Path

from app.config import settings

MAX_FISCAL_XML_BYTES = 10_485_760
_ATTACHMENT_TYPES = frozenset({"xml_original", "xml_standard"})


class LancamentoFiscalAttachmentStorageError(ValueError):
    pass


class LancamentoFiscalAttachmentStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.LNF_DANFE_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, *, request_id: str, attachment_type: str, content: bytes) -> str:
        stored_name = _stored_name(request_id, attachment_type)
        _validate_xml(content)
        target = self._resolve(stored_name)
        target.write_bytes(content)
        return stored_name

    def read(self, stored_name: str) -> bytes:
        path = self._resolve(stored_name)
        if not path.is_file():
            raise LancamentoFiscalAttachmentStorageError("Arquivo fiscal não encontrado.")
        return path.read_bytes()

    def delete(self, stored_name: str) -> None:
        path = self._resolve(stored_name)
        if path.is_file():
            path.unlink()

    def _resolve(self, stored_name: str) -> Path:
        safe = Path(stored_name).name
        if safe != stored_name or not safe.endswith(".xml"):
            raise LancamentoFiscalAttachmentStorageError("Nome de arquivo inválido.")
        target = (self.base_dir / safe).resolve()
        if self.base_dir.resolve() not in target.parents:
            raise LancamentoFiscalAttachmentStorageError("Nome de arquivo inválido.")
        return target


def _stored_name(request_id: str, attachment_type: str) -> str:
    normalized = str(request_id or "").strip().lower()
    kind = str(attachment_type or "").strip()
    if len(normalized) != 36 or normalized.count("-") != 4:
        raise LancamentoFiscalAttachmentStorageError("Solicitação inválida para gravar o XML.")
    if kind not in _ATTACHMENT_TYPES:
        raise LancamentoFiscalAttachmentStorageError("Tipo de anexo fiscal inválido.")
    return f"{normalized}-{kind}.xml"


def _validate_xml(content: bytes) -> None:
    if not content or len(content) > MAX_FISCAL_XML_BYTES:
        raise LancamentoFiscalAttachmentStorageError("O XML excede o tamanho permitido.")
    sample = _xml_inspection_sample(content)[:240].lower()
    if sample.startswith(b"<html") or sample.startswith(b"<!doctype") or sample.startswith(b"%pdf"):
        raise LancamentoFiscalAttachmentStorageError("O anexo não é um XML fiscal.")
    folded = content.upper()
    if b"<!DOCTYPE" in folded or b"<!ENTITY" in folded:
        raise LancamentoFiscalAttachmentStorageError("O XML fiscal foi recusado por segurança.")
    if not sample.startswith(b"<"):
        raise LancamentoFiscalAttachmentStorageError("O anexo não é um XML fiscal.")


def _xml_inspection_sample(payload: bytes) -> bytes:
    sample = payload.lstrip(b" \t\r\n\x0b\x0c")
    for bom in (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff"):
        if sample.startswith(bom):
            return sample[len(bom) :].lstrip(b" \t\r\n\x0b\x0c")
    return sample
