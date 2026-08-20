import {
  execRichTextCommand,
  findRichTextLinkAtSelection,
  insertRichTextHtmlFragment,
  insertRichTextLink,
  queryRichTextCommandState,
  runRichTextCommand,
  unwrapRichTextElement,
  unwrapRichTextLink,
} from "../rich-text/richTextCommands";

export const COMPOSER_FORMAT_KINDS = [
  "bold",
  "italic",
  "strike",
  "ul",
  "ol",
  "code",
  "quote",
  "link",
] as const;

export type ComposerFormatKind = (typeof COMPOSER_FORMAT_KINDS)[number];

export type ComposerFormatFlags = Record<ComposerFormatKind, boolean>;

const SELECTOR: Record<ComposerFormatKind, string | null> = {
  bold: "strong, b",
  italic: "em, i",
  strike: "s, strike, del",
  ul: "ul",
  ol: "ol",
  code: "code",
  quote: "blockquote",
  link: "a",
};

const WRAP_TAG: Partial<Record<ComposerFormatKind, string>> = {
  bold: "strong",
  italic: "em",
  strike: "s",
  code: "code",
};

/** B/I/S → execCommand nativo (toggle Word/Teams no trecho). */
const EXEC_TOGGLE: Partial<Record<ComposerFormatKind, string>> = {
  bold: "bold",
  italic: "italic",
  strike: "strikeThrough",
};

export function emptyComposerFormatFlags(): ComposerFormatFlags {
  return {
    bold: false,
    italic: false,
    strike: false,
    ul: false,
    ol: false,
    code: false,
    quote: false,
    link: false,
  };
}

function boundaryElement(container: Node, offset: number): Element | null {
  if (container.nodeType === Node.TEXT_NODE) return container.parentElement;
  if (!(container instanceof Element)) return null;
  const child =
    container.childNodes[offset] ?? container.childNodes[offset - 1] ?? container;
  if (child instanceof Element) return child;
  return child.parentElement;
}

function matchingFormatElement(editor: HTMLElement, selector: string): Element | null {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  const range = selection.getRangeAt(0);
  if (!editor.contains(range.commonAncestorContainer)) return null;
  const startEl = boundaryElement(range.startContainer, range.startOffset);
  const endEl = boundaryElement(range.endContainer, range.endOffset);
  const startHit = startEl?.closest(selector) ?? null;
  const endHit = endEl?.closest(selector) ?? null;
  if (startHit && startHit === endHit && editor.contains(startHit) && startHit !== editor) {
    return startHit;
  }
  if (range.collapsed && startHit && editor.contains(startHit) && startHit !== editor) {
    return startHit;
  }
  // Seleção parcial nas bordas: qualquer ponta dentro do formato conta (Word).
  if (startHit && editor.contains(startHit) && startHit !== editor) return startHit;
  if (endHit && editor.contains(endHit) && endHit !== editor) return endHit;
  return null;
}

function isInside(editor: HTMLElement, selector: string): boolean {
  return Boolean(matchingFormatElement(editor, selector));
}

export function queryComposerFormatFlags(editor: HTMLElement | null): ComposerFormatFlags {
  const empty = emptyComposerFormatFlags();
  if (!editor) return empty;
  return {
    bold: isInside(editor, SELECTOR.bold!) || queryRichTextCommandState("bold"),
    italic: isInside(editor, SELECTOR.italic!) || queryRichTextCommandState("italic"),
    strike: isInside(editor, SELECTOR.strike!) || queryRichTextCommandState("strikeThrough"),
    ul: isInside(editor, SELECTOR.ul!) || queryRichTextCommandState("insertUnorderedList"),
    ol: isInside(editor, SELECTOR.ol!) || queryRichTextCommandState("insertOrderedList"),
    code: isInside(editor, SELECTOR.code!),
    quote: isInside(editor, SELECTOR.quote!),
    link: Boolean(findRichTextLinkAtSelection(editor) || matchingFormatElement(editor, "a")),
  };
}

function stripMatchingTags(root: Node, selector: string): void {
  if (root instanceof Element && root.matches?.(selector)) {
    const parent = root.parentNode;
    if (!parent) return;
    while (root.firstChild) parent.insertBefore(root.firstChild, root);
    parent.removeChild(root);
    return;
  }
  if (!(root instanceof Element) && !(root instanceof DocumentFragment)) return;
  for (const hit of Array.from(root.querySelectorAll(selector))) {
    unwrapRichTextElement(hit);
  }
}

/**
 * Remove o formato só no trecho selecionado (split Word-like).
 * Caret colapsado ou seleção cobrindo o elemento inteiro → unwrap do elemento.
 */
export function unwrapFormatInSelection(editor: HTMLElement, selector: string): void {
  const hit = matchingFormatElement(editor, selector);
  if (!hit) return;
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    unwrapRichTextElement(hit);
    return;
  }
  const range = selection.getRangeAt(0);
  const fullText = hit.textContent ?? "";
  if (range.collapsed || range.toString() === fullText) {
    unwrapRichTextElement(hit);
    return;
  }

  // Blockquote (bloco): unwrap integral — split parcial não faz sentido tipográfico.
  if (hit.tagName.toLowerCase() === "blockquote") {
    unwrapRichTextElement(hit);
    return;
  }

  const beforeRange = document.createRange();
  beforeRange.selectNodeContents(hit);
  beforeRange.setEnd(range.startContainer, range.startOffset);

  const afterRange = document.createRange();
  afterRange.selectNodeContents(hit);
  afterRange.setStart(range.endContainer, range.endOffset);

  const beforeFrag = beforeRange.cloneContents();
  const midFrag = range.cloneContents();
  stripMatchingTags(midFrag, selector);
  const afterFrag = afterRange.cloneContents();

  const parent = hit.parentNode;
  if (!parent) return;

  const tag = hit.tagName;
  const makeTagged = (frag: DocumentFragment): HTMLElement | null => {
    if (!frag.hasChildNodes()) return null;
    const el = document.createElement(tag);
    el.appendChild(frag);
    return el;
  };

  const beforeEl = makeTagged(beforeFrag);
  const afterEl = makeTagged(afterFrag);
  const midNodes = Array.from(midFrag.childNodes);

  const inserted: Node[] = [];
  if (beforeEl) {
    parent.insertBefore(beforeEl, hit);
    inserted.push(beforeEl);
  }
  for (const node of midNodes) {
    parent.insertBefore(node, hit);
    inserted.push(node);
  }
  if (afterEl) {
    parent.insertBefore(afterEl, hit);
    inserted.push(afterEl);
  }
  parent.removeChild(hit);

  const midStart = beforeEl ? 1 : 0;
  const midNode = inserted[midStart];
  if (midNode) {
    const sel = document.createRange();
    sel.selectNodeContents(midNode);
    selection.removeAllRanges();
    selection.addRange(sel);
  }
}

function wrapSelectionWithTag(editor: HTMLElement, tag: string) {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    insertRichTextHtmlFragment(editor, `<${tag}>\u200b</${tag}>`);
    return;
  }
  const range = selection.getRangeAt(0);
  if (!editor.contains(range.commonAncestorContainer)) {
    insertRichTextHtmlFragment(editor, `<${tag}>\u200b</${tag}>`);
    return;
  }
  if (range.collapsed) {
    insertRichTextHtmlFragment(editor, `<${tag}>\u200b</${tag}>`);
    return;
  }
  const node = document.createElement(tag);
  try {
    range.surroundContents(node);
  } catch {
    node.appendChild(range.extractContents());
    range.insertNode(node);
  }
}

function toggleInlineViaExecOrFallback(
  editor: HTMLElement,
  kind: "bold" | "italic" | "strike",
): void {
  const cmd = EXEC_TOGGLE[kind]!;
  const selector = SELECTOR[kind]!;
  const tag = WRAP_TAG[kind]!;
  const before = editor.innerHTML;
  runRichTextCommand(editor, cmd);
  if (editor.innerHTML !== before) return;

  // jsdom / ambiente sem efeito de execCommand: fallback Word-like.
  const active = isInside(editor, selector) || queryRichTextCommandState(cmd);
  if (active) unwrapFormatInSelection(editor, selector);
  else wrapSelectionWithTag(editor, tag);
}

/**
 * Liga/desliga o formato no trecho (ou estilo de digitação no caret).
 * B/I/S preferem execCommand nativo; fallback split/unwrap sem expand-all.
 */
export function toggleComposerFormat(editor: HTMLElement, kind: ComposerFormatKind): void {
  if (kind === "bold" || kind === "italic" || kind === "strike") {
    toggleInlineViaExecOrFallback(editor, kind);
    return;
  }

  const active = queryComposerFormatFlags(editor)[kind];

  if (kind === "ul") {
    runRichTextCommand(editor, "insertUnorderedList");
    return;
  }
  if (kind === "ol") {
    runRichTextCommand(editor, "insertOrderedList");
    return;
  }
  if (kind === "quote") {
    if (active) unwrapFormatInSelection(editor, "blockquote");
    else execRichTextCommand("formatBlock", "blockquote");
    return;
  }
  if (kind === "link") {
    const anchor = findRichTextLinkAtSelection(editor);
    if (anchor) {
      const selection = window.getSelection();
      const range = selection?.rangeCount ? selection.getRangeAt(0) : null;
      if (range && !range.collapsed && range.toString() !== (anchor.textContent ?? "")) {
        const before = editor.innerHTML;
        runRichTextCommand(editor, "unlink");
        if (editor.innerHTML !== before) return;
        unwrapFormatInSelection(editor, "a");
      } else {
        unwrapRichTextLink(anchor);
      }
    } else {
      insertRichTextLink(editor, "https://");
    }
    return;
  }

  if (kind === "code") {
    if (active) unwrapFormatInSelection(editor, "code");
    else wrapSelectionWithTag(editor, "code");
  }
}
