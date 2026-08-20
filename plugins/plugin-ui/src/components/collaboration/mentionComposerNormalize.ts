/**
 * Remove cascas de formato vazias (só ZWSP/whitespace) no composer.
 * Evita «bolhas» indeleveles após undo/unwrap de code, quote e ênfases.
 */

const INLINE_SHELL_SELECTOR = "code, strong, b, em, i, s, strike, del, u, a";

const INLINE_IMAGE_SELECTOR =
  "span.delpi-ui-mention-composer__inline-image, span.delpi-ui-message-thread__inline-image, " +
  "figure.delpi-ui-mention-composer__inline-image, figure.delpi-ui-message-thread__inline-image";

const BLOCK_TAGS = new Set([
  "P",
  "DIV",
  "UL",
  "OL",
  "LI",
  "H1",
  "H2",
  "H3",
  "H4",
  "H5",
  "H6",
  "BLOCKQUOTE",
  "PRE",
  "TABLE",
]);

const CARET_ZWSP = "\u200b";

export type NormalizeComposerFormatShellsOptions = {
  /**
   * Mantém a casca vazia sob o caret (modo digitação: `<code>\u200b</code>`).
   * Undo/redo/paste não devem preservar.
   */
  preserveActiveTypingShell?: boolean;
};

/** Conteúdo sem significado tipográfico (ZWSP, NBSP, espaços). */
export function isComposerShellContentEmpty(node: Node): boolean {
  const text = (node.textContent ?? "")
    .replace(/\u200b/g, "")
    .replace(/\u00a0/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return text.length === 0;
}

function boundaryElement(container: Node, offset: number): Element | null {
  if (container.nodeType === Node.TEXT_NODE) return container.parentElement;
  if (!(container instanceof Element)) return null;
  const child =
    container.childNodes[offset] ?? container.childNodes[offset - 1] ?? container;
  if (child instanceof Element) return child;
  return child.parentElement;
}

/** Cascas vazias sob caret colapsado (estilo de digitação). */
export function findActiveTypingFormatShell(editor: HTMLElement): Element | null {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  const range = selection.getRangeAt(0);
  if (!range.collapsed || !editor.contains(range.commonAncestorContainer)) return null;
  const start = boundaryElement(range.startContainer, range.startOffset);
  const hit = start?.closest(INLINE_SHELL_SELECTOR) ?? null;
  if (!hit || hit === editor || !editor.contains(hit)) return null;
  if (!isComposerShellContentEmpty(hit)) return null;
  return hit;
}

function removeEmptyInlineShells(
  editor: HTMLElement,
  preserve: Element | null,
): boolean {
  let changed = false;
  const shells = Array.from(editor.querySelectorAll(INLINE_SHELL_SELECTOR));
  shells.sort((a, b) => {
    if (a.contains(b)) return 1;
    if (b.contains(a)) return -1;
    return 0;
  });
  for (const el of shells) {
    if (!editor.contains(el)) continue;
    if (preserve && (el === preserve || preserve.contains(el) || el.contains(preserve))) {
      continue;
    }
    if (!isComposerShellContentEmpty(el)) continue;
    el.remove();
    changed = true;
  }
  return changed;
}

function removeEmptyBlockShells(editor: HTMLElement): boolean {
  let changed = false;
  for (const pre of Array.from(editor.querySelectorAll("pre"))) {
    if (!editor.contains(pre)) continue;
    if (isComposerShellContentEmpty(pre)) {
      pre.remove();
      changed = true;
      continue;
    }
    const onlyCode =
      pre.children.length === 1 && pre.firstElementChild?.tagName === "CODE";
    if (onlyCode && isComposerShellContentEmpty(pre.firstElementChild!)) {
      pre.remove();
      changed = true;
    }
  }
  for (const bq of Array.from(editor.querySelectorAll("blockquote"))) {
    if (!editor.contains(bq)) continue;
    if (!isComposerShellContentEmpty(bq)) continue;
    bq.remove();
    changed = true;
  }
  return changed;
}

function isBlockElement(node: Node | null): boolean {
  return node instanceof Element && BLOCK_TAGS.has(node.tagName);
}

function elementContainsBlock(node: Node): boolean {
  if (!(node instanceof Element)) return false;
  if (isBlockElement(node)) return true;
  return Boolean(
    node.querySelector("p, div, ul, ol, li, h1, h2, h3, h4, h5, h6, blockquote, pre, table"),
  );
}

type ComposerSelectionSnapshot = {
  startContainer: Node;
  startOffset: number;
  endContainer: Node;
  endOffset: number;
};

function snapshotComposerSelection(editor: HTMLElement): ComposerSelectionSnapshot | null {
  const selection = editor.ownerDocument.defaultView?.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  const range = selection.getRangeAt(0);
  if (!editor.contains(range.commonAncestorContainer)) return null;
  return {
    startContainer: range.startContainer,
    startOffset: range.startOffset,
    endContainer: range.endContainer,
    endOffset: range.endOffset,
  };
}

function restoreComposerSelection(
  editor: HTMLElement,
  snapshot: ComposerSelectionSnapshot | null,
): void {
  if (!snapshot) return;
  if (!editor.contains(snapshot.startContainer) || !editor.contains(snapshot.endContainer)) {
    return;
  }
  try {
    const range = editor.ownerDocument.createRange();
    range.setStart(snapshot.startContainer, snapshot.startOffset);
    range.setEnd(snapshot.endContainer, snapshot.endOffset);
    const selection = editor.ownerDocument.defaultView?.getSelection();
    selection?.removeAllRanges();
    selection?.addRange(range);
  } catch {
    /* range may be stale after an aggressive rewrite */
  }
}

function isProtectedHost(el: Element): boolean {
  return Boolean(el.closest("pre, code, table"));
}

function insertZwsp(doc: Document, ref: Node, before: boolean): void {
  const text = doc.createTextNode(CARET_ZWSP);
  if (before) {
    ref.parentNode?.insertBefore(text, ref);
  } else {
    ref.parentNode?.insertBefore(text, ref.nextSibling);
  }
}

function hasCaretAnchor(node: Node | null, before: boolean): boolean {
  if (!node) return false;
  if (node.nodeType === Node.TEXT_NODE) {
    return (node.textContent ?? "").length > 0;
  }
  if (!(node instanceof Element)) return false;
  if (node.matches?.(INLINE_IMAGE_SELECTOR)) return false;
  if (node.tagName === "BR") return true;
  return (node.textContent ?? "").length > 0 || node.childNodes.length > 0;
}

/** ZWSP before/after each image so the caret can sit on both sides in the same `<p>`. */
export function ensureInlineImageCaretZwsp(editor: HTMLElement): void {
  const doc = editor.ownerDocument;
  for (const wrap of Array.from(editor.querySelectorAll(INLINE_IMAGE_SELECTOR))) {
    if (!editor.contains(wrap) || isProtectedHost(wrap)) continue;
    if (!hasCaretAnchor(wrap.previousSibling, true)) insertZwsp(doc, wrap, true);
    if (!hasCaretAnchor(wrap.nextSibling, false)) insertZwsp(doc, wrap, false);
  }
}

/** Wrap editor-level orphans (text / image / br) into `<p>` — insertHTML often lifts the span. */
export function wrapComposerOrphanInlines(editor: HTMLElement): void {
  const doc = editor.ownerDocument;
  const children = Array.from(editor.childNodes);
  let run: Node[] = [];
  const flush = () => {
    if (run.length === 0) return;
    const p = doc.createElement("p");
    editor.insertBefore(p, run[0] ?? null);
    for (const node of run) p.appendChild(node);
    run = [];
  };
  for (const node of children) {
    if (isBlockElement(node) || elementContainsBlock(node)) {
      flush();
      continue;
    }
    run.push(node);
  }
  flush();
}

/** Browser `defaultParagraphSeparator=div` → promote editor-level `<div>` to `<p>`. */
export function promoteComposerDivsToParagraphs(editor: HTMLElement): void {
  const doc = editor.ownerDocument;
  for (const child of Array.from(editor.children)) {
    if (child.tagName !== "DIV" || isProtectedHost(child)) continue;
    const p = doc.createElement("p");
    while (child.firstChild) p.appendChild(child.firstChild);
    child.replaceWith(p);
  }
}

function firstDirectBreak(block: HTMLElement): HTMLBRElement | null {
  for (const node of Array.from(block.childNodes)) {
    if (node instanceof HTMLBRElement) return node;
  }
  return null;
}

function splitParagraphAtFirstBreak(block: HTMLElement): void {
  if (isProtectedHost(block)) return;
  const br = firstDirectBreak(block);
  // Trailing `<br>` is an empty-paragraph placeholder — do not recurse forever.
  if (!br || !br.nextSibling) return;
  const next = block.ownerDocument.createElement("p");
  let sibling = br.nextSibling;
  while (sibling) {
    const move = sibling;
    sibling = sibling.nextSibling;
    next.appendChild(move);
  }
  br.remove();
  if (!next.childNodes.length) next.appendChild(block.ownerDocument.createElement("br"));
  block.parentNode?.insertBefore(next, block.nextSibling);
  splitParagraphAtFirstBreak(next);
}

/** Shift+Enter `<br>` inside a paragraph becomes a new `<p>` (Word Enter). Skip pre/code. */
export function splitComposerBreaksIntoParagraphs(editor: HTMLElement): void {
  for (const block of Array.from(editor.querySelectorAll("p"))) {
    if (!editor.contains(block) || isProtectedHost(block)) continue;
    splitParagraphAtFirstBreak(block);
  }
}

/**
 * After paste/insert/align: image stays in a `<p>`, line breaks are paragraphs,
 * caret can land before the image.
 */
export function ensureComposerParagraphFlow(editor: HTMLElement | null): void {
  if (!editor) return;
  const selection = snapshotComposerSelection(editor);
  wrapComposerOrphanInlines(editor);
  promoteComposerDivsToParagraphs(editor);
  splitComposerBreaksIntoParagraphs(editor);
  ensureInlineImageCaretZwsp(editor);
  restoreComposerSelection(editor, selection);
}

/** Shift+Enter: new `<p>` (Word). Falls back when execCommand is missing (jsdom). */
export function insertComposerParagraph(editor: HTMLElement | null): void {
  if (!editor) return;
  let usedExec = false;
  try {
    if (typeof editor.ownerDocument.execCommand === "function") {
      usedExec = Boolean(editor.ownerDocument.execCommand("insertParagraph"));
    }
  } catch {
    usedExec = false;
  }
  if (!usedExec) {
    const doc = editor.ownerDocument;
    const next = doc.createElement("p");
    next.appendChild(doc.createElement("br"));
    const selection = doc.defaultView?.getSelection();
    const anchor = selection?.anchorNode ?? null;
    const host = anchor instanceof Element ? anchor : anchor?.parentElement ?? null;
    const block = host?.closest("p");
    if (block && editor.contains(block) && block !== editor) {
      block.after(next);
    } else {
      editor.appendChild(next);
    }
    try {
      const range = doc.createRange();
      range.setStart(next, 0);
      range.collapse(true);
      selection?.removeAllRanges();
      selection?.addRange(range);
    } catch {
      /* ignore */
    }
  }
  ensureComposerParagraphFlow(editor);
}

/**
 * Normaliza o contenteditable após mutação de formato / undo / redo / paste.
 * Idempotente.
 */
export function normalizeComposerFormatShells(
  editor: HTMLElement | null,
  options?: NormalizeComposerFormatShellsOptions,
): void {
  if (!editor) return;
  const preserve = options?.preserveActiveTypingShell
    ? findActiveTypingFormatShell(editor)
    : null;
  let guard = 0;
  while (guard < 8) {
    guard += 1;
    const a = removeEmptyInlineShells(editor, preserve);
    const b = removeEmptyBlockShells(editor);
    if (!a && !b) break;
  }
}

/**
 * After paste / image insert / undo restore — shells first, then paragraph flow.
 * Format toggles must call only `normalizeComposerFormatShells` (no wrap/`<p>`).
 */
export function normalizeComposerContent(
  editor: HTMLElement | null,
  options?: NormalizeComposerFormatShellsOptions,
): void {
  normalizeComposerFormatShells(editor, options);
  ensureComposerParagraphFlow(editor);
}
