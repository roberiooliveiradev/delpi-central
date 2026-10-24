"""Validação defensiva de arquivos — D-U2=A (doc 103 §D).

Três camadas: extensão/allowlist → assinatura (magic bytes) → estrutura
coerente do formato. Nunca confia na declaração do cliente: extensão,
MIME declarado e conteúdo real devem convergir para o mesmo tipo.

Allowlist V1: PDF, JPEG, PNG, WebP, XLS (CFB), XLSX (ZIP OOXML), CSV.
OFX/QIF/TXT bancário e demais formatos são rejeitados (não aprovados).

Domínio puro: stdlib apenas — sem FastAPI, sem banco, sem filesystem.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import PurePosixPath

from controllership_finance_app.domain.closing_checklist.errors import (
    ContentTypeMismatch,
    EmptyFile,
    FileTooLarge,
    InvalidFileContent,
    UnsupportedMediaType,
)

MAX_FILE_BYTES = 25 * 1024 * 1024  # 25 MB — D-U2=A

# Guarda anti zip-bomb: metadados apenas, nenhuma descompressão real.
_XLSX_MAX_ENTRIES = 2000
_XLSX_MAX_UNCOMPRESSED = 256 * 1024 * 1024

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")

# extensão → (canonical kind, mimes aceitos na declaração)
_ALLOWED: dict[str, tuple[str, frozenset[str]]] = {
    ".pdf": ("pdf", frozenset({"application/pdf"})),
    ".jpg": ("jpeg", frozenset({"image/jpeg", "image/jpg", "image/pjpeg"})),
    ".jpeg": ("jpeg", frozenset({"image/jpeg", "image/jpg", "image/pjpeg"})),
    ".png": ("png", frozenset({"image/png", "image/x-png"})),
    ".webp": ("webp", frozenset({"image/webp"})),
    ".xls": (
        "xls",
        frozenset({"application/vnd.ms-excel", "application/msexcel"}),
    ),
    ".xlsx": (
        "xlsx",
        frozenset(
            {
                "application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet",
                "application/zip",
                "application/x-zip-compressed",
            }
        ),
    ),
    ".csv": (
        "csv",
        frozenset(
            {"text/csv", "text/plain", "application/csv", "application/vnd.ms-excel"}
        ),
    ),
}

_CANONICAL_MIME = {
    "pdf": "application/pdf",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "xls": "application/vnd.ms-excel",
    "xlsx": (
        "application/vnd.openxmlformats-officedocument"
        ".spreadsheetml.sheet"
    ),
    "csv": "text/csv",
}


def sanitize_original_name(raw: str | None) -> str:
    """Basename seguro para exibição — nunca caminho, nunca separador."""
    name = (raw or "").strip().replace("\\", "/")
    name = PurePosixPath(name).name
    name = _SAFE_NAME.sub("_", name).strip("._") or "evidencia"
    return name[:200]


def extension_of(original_name: str) -> str:
    return PurePosixPath(original_name.lower()).suffix


def _detect_kind(content: bytes) -> str | None:
    """Detecta o tipo real pelo conteúdo (assinatura + estrutura)."""
    if content.startswith(b"%PDF-"):
        # Estrutura: trailer %%EOF deve existir nos últimos bytes.
        return "pdf" if b"%%EOF" in content[-2048:] and len(content) > 1024 else None
    if content.startswith(b"\xff\xd8"):
        return "jpeg" if content.endswith(b"\xff\xd9") else None
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png" if content.endswith(b"IEND\xaeB`\x82") else None
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "webp"
    if content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "xls"  # CFB/OLE2 — contêiner esperado do XLS binário.
    if content.startswith(b"PK\x03\x04"):
        return "xlsx" if _is_valid_xlsx(content) else None
    if _is_text(content):
        return "csv"
    return None


def _is_valid_xlsx(content: bytes) -> bool:
    """ZIP estrutural válido com membros OOXML obrigatórios.

    Inspeciona somente o diretório central — nenhuma entrada é
    descompactada, então zip-bomb não explode aqui; a guarda de
    entradas/tamanho declarado reduz a superfície residual.
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except (zipfile.BadZipFile, ValueError):
        return False
    try:
        infos = zf.infolist()
    except zipfile.BadZipFile:
        return False
    if len(infos) > _XLSX_MAX_ENTRIES:
        return False
    if sum(i.file_size for i in infos) > _XLSX_MAX_UNCOMPRESSED:
        return False
    names = {i.filename for i in infos}
    return {"xl/workbook.xml", "[Content_Types].xml"} <= names


def _is_text(content: bytes) -> bool:
    if b"\x00" in content[:8192]:
        return False
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            content.decode(encoding)
            return True
        except UnicodeDecodeError:
            continue
    return False


def validate_upload_content(
    *,
    original_name: str,
    declared_mime: str | None,
    content: bytes,
) -> tuple[str, str]:
    """Valida extensão + assinatura + estrutura + MIME declarado.

    Retorna ``(extension, canonical_mime)`` quando o conteúdo real
    corresponde ao tipo aprovado; caso contrário levanta erro tipado.
    """
    if not content:
        raise EmptyFile("O arquivo enviado está vazio.")
    if len(content) > MAX_FILE_BYTES:
        raise FileTooLarge("O arquivo excede o limite de 25 MB.")

    ext = extension_of(original_name)
    expected = _ALLOWED.get(ext)
    if expected is None:
        raise UnsupportedMediaType(
            "Formato não permitido. Aceitos: PDF, JPEG, PNG, WebP, "
            "XLS, XLSX e CSV."
        )
    expected_kind, allowed_mimes = expected

    # CSV é detectado como "texto": garantir que o conteúdo não carrega
    # a assinatura de outro formato (poliglota/extensão falsificada).
    detected = _detect_kind(content)
    if expected_kind == "csv":
        if detected != "csv":
            raise ContentTypeMismatch(
                "O conteúdo do arquivo não corresponde a um CSV de texto."
            )
    elif detected is None:
        raise InvalidFileContent(
            "Arquivo corrompido, truncado ou com estrutura inválida."
        )
    elif detected != expected_kind:
        raise ContentTypeMismatch(
            "O conteúdo real do arquivo diverge da extensão declarada."
        )

    declared = (declared_mime or "").split(";")[0].strip().lower()
    if declared and declared not in allowed_mimes:
        raise ContentTypeMismatch(
            "O tipo MIME declarado diverge do formato do arquivo."
        )
    return ext, _CANONICAL_MIME[expected_kind]
