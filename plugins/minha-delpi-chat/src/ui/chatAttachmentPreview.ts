import {
  canPreviewFile,
  resolveFilePreviewKind,
  type FilePreviewKind,
} from "@delpi/plugin-ui/index";

export type AttachmentPreviewKind = Exclude<FilePreviewKind, "none"> | "unsupported";

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
  const kind = resolveFilePreviewKind({
    mimeType: contentType,
    fileName: filename,
  });

  return kind === "none" ? "unsupported" : kind;
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

export function canPreviewAttachment(contentType?: string | null, filename?: string): boolean {
  return canPreviewFile({
    mimeType: contentType,
    fileName: filename,
  });
}
