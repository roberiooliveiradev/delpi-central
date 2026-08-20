/**
 * Inline image blocks in MentionComposer (paste/drop at caret).
 * Persist as markdown `![alt](attachment:pending:{id})` via Turndown rule.
 */
import { resolveFilePreviewKind } from "../preview/resolveFilePreviewKind";

export type MentionComposerInlineImageInsert = {
  pendingId: string;
  file: File;
  previewUrl: string;
};

const PENDING_ATTR = "data-attachment-pending";

export function isComposerInlineImageFile(file: File): boolean {
  return resolveFilePreviewKind({ fileName: file.name, mimeType: file.type }) === "image";
}

export function newInlineImagePendingId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID().replace(/-/g, "").slice(0, 16);
  }
  return `img${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
}

/** Image files from clipboard (FileList + items), de-duplicated by reference. */
export function collectClipboardImageFiles(data: DataTransfer | null | undefined): File[] {
  if (!data) return [];
  const out: File[] = [];
  const seen = new Set<File>();
  if (data.files?.length) {
    for (const file of Array.from(data.files)) {
      if (!isComposerInlineImageFile(file) || seen.has(file)) continue;
      seen.add(file);
      out.push(file);
    }
  }
  if (data.items?.length) {
    for (const item of Array.from(data.items)) {
      if (item.kind !== "file") continue;
      const file = item.getAsFile();
      if (!file || !isComposerInlineImageFile(file) || seen.has(file)) continue;
      seen.add(file);
      out.push(file);
    }
  }
  return out;
}

export function buildInlineImageInserts(files: readonly File[]): MentionComposerInlineImageInsert[] {
  return files.filter(isComposerInlineImageFile).map((file) => {
    const pendingId = newInlineImagePendingId();
    const previewUrl =
      typeof URL !== "undefined" && typeof URL.createObjectURL === "function"
        ? URL.createObjectURL(file)
        : `blob:pending-${pendingId}`;
    return {
      pendingId,
      file,
      previewUrl,
    };
  });
}

export function inlineImageBlockHtml(insert: MentionComposerInlineImageInsert): string {
  const alt = escapeAttr(insert.file.name || "image");
  const src = escapeAttr(insert.previewUrl);
  const pending = escapeAttr(insert.pendingId);
  return (
    `<p></p>` +
    `<figure class="delpi-ui-mention-composer__inline-image" contenteditable="false">` +
    `<img src="${src}" alt="${alt}" ${PENDING_ATTR}="${pending}" data-attachment-href="attachment:pending:${pending}" />` +
    `</figure>` +
    `<p></p>`
  );
}

export function composerInlineImagePendingAttr(): string {
  return PENDING_ATTR;
}

function escapeAttr(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
