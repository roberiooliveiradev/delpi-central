export type ComposerAttachmentStatus =
  | "queued"
  | "uploading"
  | "indexed"
  | "failed"
  | "unsupported";

export function attachmentReadingStatusLabel(
  status?: string | null,
  parsed?: boolean,
): string {
  const normalized = String(status || "").trim().toLowerCase();

  if (parsed || normalized === "indexed") {
    return "Indexado";
  }

  if (normalized === "indexing") {
    return "Indexando para consulta";
  }

  if (normalized === "uploading" || normalized === "uploaded") {
    return "Processando leitura";
  }

  if (normalized === "unsupported") {
    return "Leitura limitada";
  }

  if (normalized === "index_failed" || normalized === "failed") {
    return "Falha na leitura";
  }

  if (normalized === "queued") {
    return "Aguardando envio";
  }

  return "Aguardando envio";
}

export function composerAttachmentStatusLabel(
  status?: ComposerAttachmentStatus,
  readingStatus?: string | null,
): string {
  if (readingStatus?.trim()) {
    return readingStatus.trim();
  }

  return attachmentReadingStatusLabel(status);
}

export function mapApiAttachmentToComposerStatus(
  apiStatus?: string | null,
): ComposerAttachmentStatus {
  const normalized = String(apiStatus || "").trim().toLowerCase();

  if (normalized === "indexed") {
    return "indexed";
  }

  if (normalized === "unsupported") {
    return "unsupported";
  }

  if (normalized === "index_failed") {
    return "failed";
  }

  if (normalized === "indexing" || normalized === "uploaded") {
    return "uploading";
  }

  return "uploading";
}
