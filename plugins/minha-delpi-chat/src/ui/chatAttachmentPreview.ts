export type AttachmentPreviewKind =
  | "image"
  | "pdf"
  | "text"
  | "spreadsheet"
  | "docx"
  | "unsupported";

const IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"];

const SPREADSHEET_MIMES = new Set([
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.ms-excel",
]);

const DOCX_MIMES = new Set([
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);

function extensionFromFilename(filename: string): string {
  const name = String(filename || "").trim().toLowerCase();
  const dot = name.lastIndexOf(".");

  if (dot < 0) {
    return "";
  }

  return name.slice(dot);
}

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
  const extension = extensionFromFilename(name);

  if (mime.startsWith("image/") || IMAGE_EXTENSIONS.includes(extension)) {
    return "image";
  }

  if (mime === "application/pdf" || extension === ".pdf") {
    return "pdf";
  }

  if (SPREADSHEET_MIMES.has(mime) || extension === ".xlsx" || extension === ".xls") {
    return "spreadsheet";
  }

  if (DOCX_MIMES.has(mime) || extension === ".docx") {
    return "docx";
  }

  if (
    mime.startsWith("text/") ||
    mime === "application/json" ||
    mime === "application/markdown" ||
    extension === ".txt" ||
    extension === ".md" ||
    extension === ".markdown" ||
    extension === ".csv" ||
    extension === ".tsv" ||
    extension === ".json"
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
