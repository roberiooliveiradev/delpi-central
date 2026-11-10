/** PRC-REF-023 — helpers client-side de documentos de apoio.
 * A autoridade de validação (MIME/tamanho/conteúdo) é a Engineering
 * API; aqui apenas pré-validação UX e rótulos. */

export const PRC_ATTACHMENT_ACCEPT = ".pdf,.png,.jpg,.jpeg,.webp";
export const PRC_ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024;
export const PRC_ATTACHMENT_MAX_COUNT = 10;
/** Limite em MB para exibição — derivado de MAX_BYTES (fonte única). */
export const PRC_ATTACHMENT_MAX_MB = PRC_ATTACHMENT_MAX_BYTES / 1024 / 1024;

const _EXT_OK = new Set(["pdf", "png", "jpg", "jpeg", "webp"]);

export type PrcAttachmentLocalCheck =
  | { ok: true }
  | { ok: false; error: string };

/** Pré-validação rápida por extensão+tamanho — o servidor valida
 * magic bytes e é a autoridade final. */
export function prcCheckAttachmentFile(file: File): PrcAttachmentLocalCheck {
  const ext = (file.name.split(".").pop() || "").toLowerCase();
  if (!_EXT_OK.has(ext)) {
    return {
      ok: false,
      error: "Tipo não permitido. Envie PDF ou imagem (PNG, JPEG, WebP).",
    };
  }
  if (file.size <= 0) {
    return { ok: false, error: "Arquivo vazio não é permitido." };
  }
  if (file.size > PRC_ATTACHMENT_MAX_BYTES) {
    return { ok: false, error: "Arquivo excede o limite de 10 MB." };
  }
  return { ok: true };
}

export function prcFormatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${bytes} B`;
}

export const PRC_ATTACHMENT_STATE_LABELS: Record<string, string> = {
  PENDING_SCAN: "Em análise",
  AVAILABLE: "Disponível",
  REJECTED: "Rejeitado",
  QUARANTINED: "Em quarentena",
  DELETED: "Removido",
};

export const PRC_ATTACHMENT_MEDIA_LABELS: Record<string, string> = {
  "application/pdf": "PDF",
  "image/png": "PNG",
  "image/jpeg": "JPEG",
  "image/webp": "WebP",
};
