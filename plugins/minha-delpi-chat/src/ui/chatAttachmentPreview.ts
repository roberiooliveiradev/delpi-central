export type AttachmentPreviewKind = "image" | "pdf" | "text" | "unsupported";

export function formatAttachmentSize(size?: number): string {
  if (!size || size < 0) {
    return "";
  }

  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

export function resolveAttachmentPreviewKind(
  contentType?: string | null,
  filename?: string,
): AttachmentPreviewKind {
  const mime = String(contentType || "").trim().toLowerCase();
  const name = String(filename || "").trim().toLowerCase();

  if (mime.startsWith("image/")) {
    return "image";
  }

  if (mime === "application/pdf" || name.endsWith(".pdf")) {
    return "pdf";
  }

  if (
    mime.startsWith("text/") ||
    mime === "application/json" ||
    mime === "application/markdown" ||
    name.endsWith(".txt") ||
    name.endsWith(".md") ||
    name.endsWith(".markdown") ||
    name.endsWith(".csv") ||
    name.endsWith(".json")
  ) {
    return "text";
  }

  return "unsupported";
}

export function createLocalAttachmentPreviewUrl(file: File): string | null {
  const kind = resolveAttachmentPreviewKind(file.type, file.name);

  if (kind === "image" || kind === "pdf") {
    return URL.createObjectURL(file);
  }

  return null;
}

export function revokeAttachmentPreviewUrl(url?: string | null) {
  if (url?.startsWith("blob:")) {
    URL.revokeObjectURL(url);
  }
}
