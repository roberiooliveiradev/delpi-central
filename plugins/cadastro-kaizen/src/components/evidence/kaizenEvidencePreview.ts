import type { KaizenEvidence } from "../../types/kaizen";

export type EvidencePreviewMode = "image" | "pdf" | "none";

function fileName(value: string | null | undefined): string {
  return (value ?? "").toLowerCase();
}

function isImageMime(mime: string | null | undefined): boolean {
  return !!mime && mime.toLowerCase().startsWith("image/");
}

function isPdfSource(mime: string | null | undefined, name: string): boolean {
  return (mime ?? "").toLowerCase() === "application/pdf" || name.endsWith(".pdf");
}

/** Modo de pré-visualização de uma evidência já salva (link não pré-visualiza inline). */
export function resolveEvidencePreviewMode(evidence: KaizenEvidence): EvidencePreviewMode {
  if (evidence.type === "link") return "none";
  const name = fileName(evidence.file_name);
  if (isImageMime(evidence.mime_type) || /\.(png|jpe?g|gif|webp|bmp|svg)$/.test(name)) return "image";
  if (isPdfSource(evidence.mime_type, name)) return "pdf";
  return "none";
}

export function canPreviewEvidence(evidence: KaizenEvidence): boolean {
  return resolveEvidencePreviewMode(evidence) !== "none";
}

/** Modo de pré-visualização de um arquivo local ainda não enviado. */
export function resolveLocalFilePreviewMode(file: File): EvidencePreviewMode {
  const mime = file.type.toLowerCase();
  const name = file.name.toLowerCase();
  if (mime.startsWith("image/")) return "image";
  if (mime === "application/pdf" || name.endsWith(".pdf")) return "pdf";
  return "none";
}

export function canPreviewLocalFile(file: File): boolean {
  return resolveLocalFilePreviewMode(file) !== "none";
}

export function evidencePreviewTitle(evidence: KaizenEvidence): string {
  return evidence.description || evidence.file_name || "Evidência";
}
