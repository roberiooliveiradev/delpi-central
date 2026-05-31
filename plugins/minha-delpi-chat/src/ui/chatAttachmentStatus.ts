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
): string {
  return attachmentReadingStatusLabel(status);
}
