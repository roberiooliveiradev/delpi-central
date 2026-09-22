/**
 * Inline image insert at caret — shared by RichTextEditor (helpdesk) and MentionComposer.
 * Image is an inline object in the paragraph flow (not append-at-end HTML).
 */
export type RichTextInlineImageInsert = {
  src: string;
  alt?: string;
  pendingId?: string;
  documentId?: number | string;
  /** Optional stable href token for markdown round-trip. */
  attachmentHref?: string;
};

const CARET_ZWSP = "\u200b";
const PENDING_ATTR = "data-attachment-pending";
const DOCUMENT_ATTR = "data-attachment-id";

function ensureParagraphAtCaret(editor: HTMLElement, range: Range): void {
  const block = (
    range.commonAncestorContainer instanceof Element
      ? range.commonAncestorContainer
      : range.commonAncestorContainer.parentElement
  )?.closest("p,li,h1,h2,h3,h4,h5,h6,td,th");
  if (block && editor.contains(block) && block !== editor) return;

  const p = editor.ownerDocument.createElement("p");
  if (!editor.childNodes.length) {
    editor.appendChild(p);
  } else {
    editor.appendChild(p);
  }
  range.selectNodeContents(p);
  range.collapse(true);
}

export function createRichTextInlineImageSpan(
  insert: RichTextInlineImageInsert,
  options?: { removeAriaLabel?: string },
): HTMLSpanElement {
  const doc = editorDocument();
  const span = doc.createElement("span");
  span.className =
    "delpi-ui-mention-composer__inline-image delpi-ui-rich-text__inline-image";
  span.setAttribute("contenteditable", "false");

  const img = doc.createElement("img");
  img.src = insert.src;
  img.alt = insert.alt || "image";
  if (insert.pendingId) {
    img.setAttribute(PENDING_ATTR, insert.pendingId);
    img.setAttribute(
      "data-attachment-href",
      insert.attachmentHref || `attachment:pending:${insert.pendingId}`,
    );
  }
  if (insert.documentId != null && String(insert.documentId).trim()) {
    img.setAttribute(DOCUMENT_ATTR, String(insert.documentId));
  }

  const btn = doc.createElement("button");
  btn.type = "button";
  btn.className =
    "delpi-ui-mention-composer__inline-image-remove delpi-ui-rich-text__inline-image-remove";
  btn.setAttribute("data-inline-image-remove", "1");
  btn.setAttribute("contenteditable", "false");
  btn.tabIndex = -1;
  btn.setAttribute(
    "aria-label",
    options?.removeAriaLabel ?? `Remove ${insert.alt || "image"}`,
  );
  btn.textContent = "×";

  span.appendChild(img);
  span.appendChild(btn);
  return span;
}

function editorDocument(): Document {
  if (typeof document === "undefined") throw new Error("document required");
  return document;
}

/**
 * Insert image as an inline character at the caret (or replacing the selection).
 */
export function insertRichTextInlineImageAtCaret(
  editor: HTMLElement | null,
  insert: RichTextInlineImageInsert,
  options?: { removeAriaLabel?: string },
): HTMLSpanElement | null {
  if (!editor || !insert.src) return null;
  editor.focus();
  const selection = window.getSelection();
  let range: Range | null = null;
  if (
    selection &&
    selection.rangeCount > 0 &&
    editor.contains(selection.getRangeAt(0).commonAncestorContainer)
  ) {
    range = selection.getRangeAt(0);
  }
  if (!range) {
    range = editor.ownerDocument.createRange();
    const lastP = editor.querySelector("p:last-of-type");
    if (lastP) {
      range.selectNodeContents(lastP);
      range.collapse(false);
    } else {
      const p = editor.ownerDocument.createElement("p");
      editor.appendChild(p);
      range.selectNodeContents(p);
      range.collapse(true);
    }
  }

  ensureParagraphAtCaret(editor, range);
  range.deleteContents();

  const zwspBefore = editor.ownerDocument.createTextNode(CARET_ZWSP);
  const span = createRichTextInlineImageSpan(insert, options);
  const zwspAfter = editor.ownerDocument.createTextNode(CARET_ZWSP);

  const frag = editor.ownerDocument.createDocumentFragment();
  frag.appendChild(zwspBefore);
  frag.appendChild(span);
  frag.appendChild(zwspAfter);
  range.insertNode(frag);

  const after = editor.ownerDocument.createRange();
  after.setStart(zwspAfter, zwspAfter.length);
  after.collapse(true);
  selection?.removeAllRanges();
  selection?.addRange(after);
  return span;
}

export function removeRichTextInlineImage(
  node: Element | null,
): void {
  if (!node) return;
  const host =
    node.closest(
      "span.delpi-ui-mention-composer__inline-image, span.delpi-ui-rich-text__inline-image, " +
        "figure.delpi-ui-mention-composer__inline-image, figure.delpi-ui-rich-text__inline-image",
    ) ??
    (node.classList.contains("delpi-ui-mention-composer__inline-image") ||
    node.classList.contains("delpi-ui-rich-text__inline-image")
      ? node
      : null);
  if (!host?.parentNode) return;
  host.parentNode.removeChild(host);
}
