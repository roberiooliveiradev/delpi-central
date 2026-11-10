"""PRC-REF-023 — domínio de documentos opcionais de apoio técnico.

Regras puras: validação de nome, MIME por conteúdo (magic bytes),
tamanho e estados documentais. Nenhuma dependência de framework,
storage SDK ou infraestrutura.

Limites (proposta v1 pendente de ratificação PO — ver contrato REF-023
no MVP-TECHNICAL-CONTRACT): 10 MB por arquivo, 10 arquivos por caso,
tipos PDF/PNG/JPEG/WebP comprovados por magic bytes.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB por arquivo
ATTACHMENT_MAX_PER_REQUEST = 10
ATTACHMENT_FILENAME_MAX = 120

ATTACHMENT_STATES = frozenset(
    {"PENDING_SCAN", "AVAILABLE", "REJECTED", "QUARANTINED", "DELETED"}
)

# Estados em que o solicitante pode anexar documentos ao caso.
# needs_correction/completed/rejected = PENDING_OWNER (contrato REF-023).
ATTACHMENT_UPLOAD_STATUSES = frozenset({"submitted", "in_progress"})

# MIME oficial por assinatura binária — a extensão/Content-Type do
# cliente nunca é prova. (magic, media_type, extensão canônica)
_SIGNATURES: tuple[tuple[bytes, str, str], ...] = (
    (b"%PDF-", "application/pdf", ".pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"RIFF", "image/webp", ".webp"),  # refinado abaixo (bytes 8-12 WEBP)
)

_ATTACHMENT_ERRORS = {
    "empty": "Arquivo vazio não é permitido.",
    "too_large": "Arquivo excede o limite de 10 MB por documento.",
    "too_many": "Limite de 10 documentos por solicitação atingido.",
    "media_type": "Tipo de arquivo não permitido. Envie PDF ou imagem (PNG, JPEG, WebP).",
    "fake_type": "O conteúdo do arquivo não corresponde a um tipo permitido (PDF/PNG/JPEG/WebP).",
    "corrupt": "Arquivo corrompido ou estrutura inválida para o tipo detectado.",
}


def attachment_error(code: str) -> str:
    return _ATTACHMENT_ERRORS.get(code, "Documento inválido.")


def sanitize_filename(name: str | None) -> str:
    """Nome original seguro para exibição/Content-Disposition.

    Remove path traversal, controles e normaliza Unicode; nunca usado
    como chave de storage (a chave é opaca: request_id/attachment_id.ext).
    """
    raw = (name or "documento").strip() or "documento"
    base = raw.replace("\\", "/").rsplit("/", 1)[-1]
    base = unicodedata.normalize("NFC", base)
    base = re.sub(r"[\x00-\x1f\x7f]", "", base)
    base = base.strip(" .")
    if not base:
        base = "documento"
    return base[:ATTACHMENT_FILENAME_MAX]


def detect_media_type(content: bytes) -> tuple[str, str] | None:
    """(media_type, ext) por magic bytes ou ``None`` se não suportado."""
    if content[:5] == b"%PDF-":
        return "application/pdf", ".pdf"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png", ".png"
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg", ".jpg"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp", ".webp"
    return None


def validate_attachment(
    *,
    filename: str | None,
    content: bytes,
    current_count: int,
) -> dict[str, object]:
    """Valida upload e retorna metadados canônicos.

    Levanta ``ValueError(code)`` — o service mapeia para erro tipado.
    """
    if current_count >= ATTACHMENT_MAX_PER_REQUEST:
        raise ValueError("too_many")
    if not content:
        raise ValueError("empty")
    if len(content) > ATTACHMENT_MAX_BYTES:
        raise ValueError("too_large")
    detected = detect_media_type(content)
    if detected is None:
        raise ValueError("media_type")
    media_type, ext = detected
    # Checagens estruturais mínimas por tipo (anti-corrompido óbvio).
    if media_type == "application/pdf" and b"%%EOF" not in content[-4096:]:
        raise ValueError("corrupt")
    if media_type == "image/png" and len(content) < 33:
        raise ValueError("corrupt")
    if media_type == "image/jpeg" and not content.endswith(b"\xff\xd9"):
        raise ValueError("corrupt")
    if media_type == "image/webp":
        declared = int.from_bytes(content[4:8], "little") + 8
        if declared != len(content):
            raise ValueError("corrupt")
    return {
        "original_file_name": sanitize_filename(filename),
        "media_type": media_type,
        "extension": ext,
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def attachment_to_api(row: dict) -> dict:
    """DTO de saída — nunca expõe storage_key/path físico.

    ``inspection`` registra HONESTAMENTE o nível de inspeção aplicado:
    hoje só validação estrutural (magic bytes + estrutura do tipo) —
    NÃO há antivírus na plataforma (PENDING_MALWARE_SCAN_OWNER). Nunca
    apresentar ``AVAILABLE`` como «scan antimalware aprovado».
    """
    return {
        "inspection": "structural",
        "attachmentId": row["id"],
        "requestId": row["request_id"],
        "originalFileName": row["original_file_name"],
        "mediaType": row["media_type"],
        "sizeBytes": row["size_bytes"],
        "sha256": row["sha256"],
        "state": row["state"],
        "uploadedBySubject": row.get("uploaded_by_subject"),
        "uploadedByDisplayName": row.get("uploaded_by_display_name"),
        "createdAt": row["created_at"],
    }
