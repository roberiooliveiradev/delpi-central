/**
 * Inline images in MentionComposer (paste/drop at caret) — Word-like:
 * span+img inside the paragraph so caret can sit left/right on the same line.
 * Persist as markdown `![alt](attachment:pending:{id})` via Turndown.
 */
import { resolveFilePreviewKind } from "../preview/resolveFilePreviewKind";
import type { RichTextAlign } from "../rich-text/richTextCommands";

export type MentionComposerInlineImageInsert = {
  pendingId: string;
  file: File;
  previewUrl: string;
};

export type InlineImageAlign = RichTextAlign;

/** @deprecated Align lives on the paragraph `text-align`; kept for legacy DOM. */
export const INLINE_IMAGE_ALIGN_ATTR = "data-align";

/** Composer + bubble inline image wrappers (span; figure kept for legacy HTML). */
export const INLINE_IMAGE_FIGURE_SELECTOR =
  "span.delpi-ui-mention-composer__inline-image, span.delpi-ui-message-thread__inline-image, " +
  "figure.delpi-ui-mention-composer__inline-image, figure.delpi-ui-message-thread__inline-image";

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

function clipboardImageFingerprint(file: File): string {
  return `${file.name}|${file.size}|${file.type}|${file.lastModified}`;
}

function pushUniqueImages(out: File[], seen: Set<string>, file: File): void {
  if (!isComposerInlineImageFile(file)) return;
  const key = clipboardImageFingerprint(file);
  if (seen.has(key)) return;
  seen.add(key);
  out.push(file);
}

function collectImagesFromFileList(list: FileList | null | undefined): File[] {
  if (!list?.length) return [];
  const out: File[] = [];
  const seen = new Set<string>();
  for (const file of Array.from(list)) pushUniqueImages(out, seen, file);
  return out;
}

function collectImagesFromItems(items: DataTransferItemList | null | undefined): File[] {
  if (!items?.length) return [];
  const out: File[] = [];
  const seen = new Set<string>();
  for (const item of Array.from(items)) {
    if (item.kind !== "file") continue;
    const file = item.getAsFile();
    if (file) pushUniqueImages(out, seen, file);
  }
  return out;
}

/**
 * Clipboard images once per capture.
 * Prefer `files`; only fall back to `items` when `files` has no images.
 * Dedup by fingerprint (name|size|type|lastModified) — Chromium often exposes
 * the same screenshot as two distinct `File` objects in files + items.
 */
export function uniqueClipboardImageFiles(
  data: DataTransfer | null | undefined,
): File[] {
  if (!data) return [];
  const fromFiles = collectImagesFromFileList(data.files);
  if (fromFiles.length > 0) return fromFiles;
  return collectImagesFromItems(data.items);
}

/** @deprecated Prefer `uniqueClipboardImageFiles` (same behavior). */
export function collectClipboardImageFiles(
  data: DataTransfer | null | undefined,
): File[] {
  return uniqueClipboardImageFiles(data);
}

function dataUrlToImageFile(dataUrl: string, fileName: string): File | null {
  const match = /^data:([^;,]+)?(;base64)?,(.*)$/i.exec(dataUrl.trim());
  if (!match) return null;
  const mime = (match[1] || "image/png").trim() || "image/png";
  if (!mime.startsWith("image/")) return null;
  const isBase64 = Boolean(match[2]);
  const payload = match[3] ?? "";
  try {
    let bytes: Uint8Array;
    if (isBase64) {
      const binary = atob(payload);
      bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    } else {
      bytes = new TextEncoder().encode(decodeURIComponent(payload));
    }
    const ext = mime.split("/")[1]?.split("+")[0] || "png";
    const name = fileName.includes(".") ? fileName : `${fileName || "image"}.${ext}`;
    return new File([bytes], name, { type: mime });
  } catch {
    return null;
  }
}

/**
 * HTML-only paste (no clipboard files): at most one File per unique data: image src.
 * Ignores http(s) (policy) and blob: (async; screenshots usually arrive via files).
 */
export function extractClipboardHtmlImageFiles(html: string | null | undefined): File[] {
  const source = (html ?? "").trim();
  if (!source || typeof DOMParser === "undefined") return [];
  if (!/<img\b/i.test(source)) return [];
  try {
    const doc = new DOMParser().parseFromString(source, "text/html");
    const out: File[] = [];
    const seen = new Set<string>();
    for (const img of Array.from(doc.querySelectorAll("img"))) {
      const src = (img.getAttribute("src") || "").trim();
      if (!src.startsWith("data:")) continue;
      if (seen.has(src)) continue;
      seen.add(src);
      const file = dataUrlToImageFile(src, img.getAttribute("alt") || "image");
      if (file) out.push(file);
    }
    return out;
  } catch {
    return [];
  }
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

export function normalizeInlineImageAlign(
  value: string | null | undefined,
): InlineImageAlign {
  const raw = String(value ?? "")
    .trim()
    .toLowerCase();
  if (raw === "center" || raw === "right" || raw === "justify") return raw;
  return "left";
}

/** Title from markdown `![alt](url "align=center")` or bare align token (legacy). */
export function parseAlignFromImageTitle(
  title: string | null | undefined,
): InlineImageAlign {
  const raw = String(title ?? "").trim();
  if (!raw) return "left";
  const match = /(?:^|[;\s,])align\s*=\s*(left|center|right|justify)\b/i.exec(
    ` ${raw}`,
  );
  if (match?.[1]) return normalizeInlineImageAlign(match[1]);
  return normalizeInlineImageAlign(raw);
}

/** @deprecated Prefer paragraph text-align. */
export function setInlineImageFigureAlign(
  figure: Element,
  align: InlineImageAlign,
): void {
  figure.setAttribute(INLINE_IMAGE_ALIGN_ATTR, normalizeInlineImageAlign(align));
}

/** @deprecated Prefer paragraph text-align. */
export function readInlineImageFigureAlign(
  figure: Element | null | undefined,
): InlineImageAlign {
  if (!figure) return "left";
  return normalizeInlineImageAlign(figure.getAttribute(INLINE_IMAGE_ALIGN_ATTR));
}

export function findInlineImageFigureFromSelection(
  root: HTMLElement | null | undefined,
): HTMLElement | null {
  if (!root || typeof window === "undefined") return null;
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  const node = selection.getRangeAt(0).commonAncestorContainer;
  const el = node instanceof Element ? node : node?.parentElement;
  const figure = el?.closest(INLINE_IMAGE_FIGURE_SELECTOR);
  if (!figure || !root.contains(figure)) return null;
  return figure as HTMLElement;
}

/**
 * No-op: Word-like inline images sit inside `<p>`; caret does not need sibling anchors.
 * Kept so call sites compile until hydrate drops the import in E3.S2.
 */
export function ensureInlineImageCaretAnchors(_root: ParentNode): void {
  /* intentionally empty */
}

/** Span+img fragment for insert at caret (same paragraph). */
export function inlineImageInlineHtml(
  insert: MentionComposerInlineImageInsert,
  options?: { removeAriaLabel?: string },
): string {
  const alt = escapeAttr(insert.file.name || "image");
  const src = escapeAttr(insert.previewUrl);
  const pending = escapeAttr(insert.pendingId);
  const removeLabel = escapeAttr(
    options?.removeAriaLabel ?? `Remove ${insert.file.name || "image"}`,
  );
  return (
    `\u200b<span class="delpi-ui-mention-composer__inline-image" contenteditable="false">` +
    `<img src="${src}" alt="${alt}" ${PENDING_ATTR}="${pending}" data-attachment-href="attachment:pending:${pending}" />` +
    `<button type="button" class="delpi-ui-mention-composer__inline-image-remove" data-inline-image-remove="1" contenteditable="false" tabindex="-1" aria-label="${removeLabel}">` +
    `×` +
    `</button>` +
    `</span>\u200b`
  );
}

/** @deprecated Use `inlineImageInlineHtml`. */
export function inlineImageBlockHtml(
  insert: MentionComposerInlineImageInsert,
  options?: { removeAriaLabel?: string },
): string {
  return inlineImageInlineHtml(insert, options);
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
