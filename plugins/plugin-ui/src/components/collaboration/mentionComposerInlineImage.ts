/**
 * Inline image blocks in MentionComposer (paste/drop at caret).
 * Persist as markdown `![alt](attachment:pending:{id})` via Turndown rule;
 * optional title `"align=center|right|justify"` when not left.
 */
import { resolveFilePreviewKind } from "../preview/resolveFilePreviewKind";
import type { RichTextAlign } from "../rich-text/richTextCommands";

export type MentionComposerInlineImageInsert = {
  pendingId: string;
  file: File;
  previewUrl: string;
};

export type InlineImageAlign = RichTextAlign;

export const INLINE_IMAGE_ALIGN_ATTR = "data-align";

/** Composer + bubble figure roots. */
export const INLINE_IMAGE_FIGURE_SELECTOR =
  "figure.delpi-ui-mention-composer__inline-image, figure.delpi-ui-message-thread__inline-image";

const PENDING_ATTR = "data-attachment-pending";

const CARET_ANCHOR_HTML = "<p><br></p>";

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

export function normalizeInlineImageAlign(
  value: string | null | undefined,
): InlineImageAlign {
  const raw = String(value ?? "")
    .trim()
    .toLowerCase();
  if (raw === "center" || raw === "right" || raw === "justify") return raw;
  return "left";
}

/** Title from markdown `![alt](url "align=center")` or bare align token. */
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

export function setInlineImageFigureAlign(
  figure: Element,
  align: InlineImageAlign,
): void {
  figure.setAttribute(INLINE_IMAGE_ALIGN_ATTR, normalizeInlineImageAlign(align));
}

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

function ownerDocumentOf(root: ParentNode): Document {
  if (root instanceof Document) return root;
  if (root instanceof Element) return root.ownerDocument ?? document;
  return document;
}

function isEditableCaretAnchor(node: Node | null | undefined): boolean {
  if (!node) return false;
  if (node.nodeType === Node.TEXT_NODE) {
    return Boolean((node.textContent ?? "").trim());
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return false;
  const el = node as Element;
  if (el.matches?.(INLINE_IMAGE_FIGURE_SELECTOR)) return false;
  const tag = el.tagName;
  return (
    tag === "P" ||
    tag === "DIV" ||
    tag === "LI" ||
    tag === "H1" ||
    tag === "H2" ||
    tag === "H3" ||
    tag === "H4" ||
    tag === "H5" ||
    tag === "H6" ||
    tag === "BLOCKQUOTE" ||
    tag === "PRE"
  );
}

function createCaretAnchor(doc: Document): HTMLParagraphElement {
  const p = doc.createElement("p");
  p.appendChild(doc.createElement("br"));
  return p;
}

/**
 * Ensures editable `<p><br></p>` siblings before/after each inline figure so
 * the caret can land around `contenteditable=false` blocks.
 */
export function ensureInlineImageCaretAnchors(root: ParentNode): void {
  const host =
    root instanceof Element
      ? root
      : root instanceof Document
        ? root.body
        : null;
  if (!host || typeof host.querySelectorAll !== "function") return;
  const doc = ownerDocumentOf(root);
  const figures = Array.from(host.querySelectorAll(INLINE_IMAGE_FIGURE_SELECTOR));
  for (const figure of figures) {
    if (!isEditableCaretAnchor(figure.previousSibling)) {
      figure.parentNode?.insertBefore(createCaretAnchor(doc), figure);
    }
    if (!isEditableCaretAnchor(figure.nextSibling)) {
      figure.parentNode?.insertBefore(createCaretAnchor(doc), figure.nextSibling);
    }
  }
}

export function inlineImageBlockHtml(
  insert: MentionComposerInlineImageInsert,
  options?: { removeAriaLabel?: string },
): string {
  const alt = escapeAttr(insert.file.name || "image");
  const src = escapeAttr(insert.previewUrl);
  const pending = escapeAttr(insert.pendingId);
  const removeLabel = escapeAttr(
    options?.removeAriaLabel ?? `Remove ${insert.file.name || "image"}`,
  );
  const figure =
    `<figure class="delpi-ui-mention-composer__inline-image" contenteditable="false" ${INLINE_IMAGE_ALIGN_ATTR}="left">` +
    `<img src="${src}" alt="${alt}" ${PENDING_ATTR}="${pending}" data-attachment-href="attachment:pending:${pending}" />` +
    `<button type="button" class="delpi-ui-mention-composer__inline-image-remove" data-inline-image-remove="1" contenteditable="false" tabindex="-1" aria-label="${removeLabel}">` +
    `×` +
    `</button>` +
    `</figure>`;
  return `${CARET_ANCHOR_HTML}${figure}${CARET_ANCHOR_HTML}`;
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
