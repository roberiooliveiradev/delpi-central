import { workspaceFileReadingStatusLabel } from "../content/workspaceFileIngestContent";

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
  return workspaceFileReadingStatusLabel(status, parsed);
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
