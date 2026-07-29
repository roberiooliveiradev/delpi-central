import type { KaizenEvidenceType } from "../../types/kaizen";

export function formatEvidenceFileSize(bytes?: number | null): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function isImageFile(file: File): boolean {
  return file.type.toLowerCase().startsWith("image/");
}

export function inferEvidenceTypeFromFile(file: File): KaizenEvidenceType {
  const mime = file.type.toLowerCase();
  const name = file.name.toLowerCase();
  if (mime.startsWith("image/")) return "photo";
  if (
    mime === "application/pdf" ||
    mime.includes("word") ||
    mime.includes("spreadsheet") ||
    mime.includes("excel") ||
    name.endsWith(".pdf") ||
    name.endsWith(".doc") ||
    name.endsWith(".docx") ||
    name.endsWith(".xls") ||
    name.endsWith(".xlsx")
  ) {
    return "document";
  }
  return "attachment";
}

export function createPendingUploadId(): string {
  return `pending-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}
