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
import {
  isComposerShellContentEmpty,
  normalizeComposerFormatShells,
} from "./mentionComposerNormalize";

export const COMPOSER_FORMAT_KINDS = [
  "bold",
  "italic",
  "strike",
  "underline",
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
  underline: "u",
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
  underline: "u",
  code: "code",
};

/** Inline via execCommand quando a seleção está expandida. */
const EXEC_TOGGLE: Partial<Record<ComposerFormatKind, string>> = {
  bold: "bold",
  italic: "italic",
  strike: "strikeThrough",
  underline: "underline",
};

const INLINE_TOGGLE_KINDS = new Set<ComposerFormatKind>([
  "bold",
  "italic",
  "strike",
  "underline",
  "code",
]);

export function emptyComposerFormatFlags(): ComposerFormatFlags {
  return {
    bold: false,
    italic: false,
    strike: false,
    underline: false,
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
    underline: isInside(editor, SELECTOR.underline!) || queryRichTextCommandState("underline"),
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

function makeTaggedFragment(tag: string, frag: DocumentFragment): HTMLElement | null {
  if (!frag.hasChildNodes() || isComposerShellContentEmpty(frag)) return null;
  const el = document.createElement(tag);
  el.appendChild(frag);
  return el;
}

/**
 * Caret colapsado dentro do formato: sai do estilo para digitação seguinte
 * sem remover o formato do texto já escrito (Word/Teams).
 * Divide o elemento no caret e posiciona o caret no meio (texto plano).
 */
export function exitInlineFormatAtCaret(
  editor: HTMLElement,
  hit: Element,
  selection: Selection,
  range: Range,
): void {
  const parent = hit.parentNode;
  if (!parent || !editor.contains(hit)) return;

  const tag = hit.tagName;
  const beforeRange = document.createRange();
  beforeRange.selectNodeContents(hit);
  beforeRange.setEnd(range.startContainer, range.startOffset);

  const afterRange = document.createRange();
  afterRange.selectNodeContents(hit);
  afterRange.setStart(range.endContainer, range.endOffset);

  const beforeEl = makeTaggedFragment(tag, beforeRange.cloneContents());
  const afterEl = makeTaggedFragment(tag, afterRange.cloneContents());
  const marker = document.createTextNode("\u200b");

  if (beforeEl) parent.insertBefore(beforeEl, hit);
  parent.insertBefore(marker, hit);
  if (afterEl) parent.insertBefore(afterEl, hit);
  parent.removeChild(hit);

  normalizeComposerFormatShells(editor);

  const next = document.createRange();
  if (marker.isConnected) {
    next.setStart(marker, marker.data.length);
  } else {
    next.selectNodeContents(editor);
    next.collapse(false);
  }
  next.collapse(true);
  selection.removeAllRanges();
  selection.addRange(next);
}

/**
 * Remove o formato só no trecho selecionado (split Word-like).
 * Caret colapsado → sai do estilo da digitação (não unwrap do trecho anterior).
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

  if (range.collapsed) {
    // Blockquote (bloco): unwrap integral.
    if (hit.tagName.toLowerCase() === "blockquote") {
      unwrapRichTextElement(hit);
      return;
    }
    exitInlineFormatAtCaret(editor, hit, selection, range);
    return;
  }

  const fullText = hit.textContent ?? "";
  if (range.toString() === fullText) {
    const preParent =
      hit.tagName.toLowerCase() === "code" && hit.parentElement?.tagName === "PRE"
        ? hit.parentElement
        : null;
    unwrapRichTextElement(hit);
    if (preParent?.isConnected) unwrapRichTextElement(preParent);
    return;
  }

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
  const beforeEl = makeTaggedFragment(tag, beforeFrag);
  const afterEl = makeTaggedFragment(tag, afterFrag);
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

  normalizeComposerFormatShells(editor);

  const midStart = beforeEl ? 1 : 0;
  const midNode = inserted[midStart];
  if (midNode && midNode.isConnected) {
    const sel = document.createRange();
    sel.selectNodeContents(midNode);
    selection.removeAllRanges();
    selection.addRange(sel);
  }
}

function placeCaretInsideLastEmptyShell(editor: HTMLElement, tag: string): void {
  const shells = editor.querySelectorAll(tag);
  const last = shells[shells.length - 1];
  if (!(last instanceof HTMLElement) || !editor.contains(last)) return;
  if (!isComposerShellContentEmpty(last)) return;
  const selection = window.getSelection();
  if (!selection) return;
  let text = last.firstChild;
  if (!text || text.nodeType !== Node.TEXT_NODE) {
    text = document.createTextNode("\u200b");
    last.appendChild(text);
  }
  const range = document.createRange();
  const len = text.textContent?.length ?? 0;
  range.setStart(text, len);
  range.collapse(true);
  selection.removeAllRanges();
  selection.addRange(range);
}

function wrapSelectionWithTag(editor: HTMLElement, tag: string) {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    insertRichTextHtmlFragment(editor, `<${tag}>\u200b</${tag}>`);
    placeCaretInsideLastEmptyShell(editor, tag);
    return;
  }
  const range = selection.getRangeAt(0);
  if (!editor.contains(range.commonAncestorContainer)) {
    insertRichTextHtmlFragment(editor, `<${tag}>\u200b</${tag}>`);
    placeCaretInsideLastEmptyShell(editor, tag);
    return;
  }
  if (range.collapsed) {
    insertRichTextHtmlFragment(editor, `<${tag}>\u200b</${tag}>`);
    placeCaretInsideLastEmptyShell(editor, tag);
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

/** Código: inline `<code>` ou bloco `<pre><code>` se a seleção tiver quebra de linha. */
function wrapSelectionAsCode(editor: HTMLElement) {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    insertRichTextHtmlFragment(editor, `<code>\u200b</code>`);
    placeCaretInsideLastEmptyShell(editor, "code");
    return;
  }
  const range = selection.getRangeAt(0);
  if (!editor.contains(range.commonAncestorContainer)) {
    insertRichTextHtmlFragment(editor, `<code>\u200b</code>`);
    placeCaretInsideLastEmptyShell(editor, "code");
    return;
  }
  if (range.collapsed) {
    insertRichTextHtmlFragment(editor, `<code>\u200b</code>`);
    placeCaretInsideLastEmptyShell(editor, "code");
    return;
  }
  if (!range.toString().includes("\n")) {
    wrapSelectionWithTag(editor, "code");
    return;
  }
  const pre = document.createElement("pre");
  const code = document.createElement("code");
  try {
    code.appendChild(range.extractContents());
  } catch {
    code.textContent = range.toString();
    range.deleteContents();
  }
  pre.appendChild(code);
  range.insertNode(pre);
  selection.removeAllRanges();
  const after = document.createRange();
  after.selectNodeContents(code);
  after.collapse(false);
  selection.addRange(after);
}

function selectionIsCollapsed(editor: HTMLElement): boolean {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return true;
  const range = selection.getRangeAt(0);
  if (!editor.contains(range.commonAncestorContainer)) return true;
  return range.collapsed;
}

/**
 * B/I/S/U/code com caret: liga estilo de digitação ou sai sem apagar o trecho.
 * Com seleção expandida: execCommand ou wrap/unwrap.
 */
function toggleInlineFormat(
  editor: HTMLElement,
  kind: "bold" | "italic" | "strike" | "underline" | "code",
): void {
  const selector = SELECTOR[kind]!;
  const tag = WRAP_TAG[kind]!;
  const collapsed = selectionIsCollapsed(editor);
  const active = isInside(editor, selector);

  if (collapsed) {
    if (active) unwrapFormatInSelection(editor, selector);
    else if (kind === "code") wrapSelectionAsCode(editor);
    else wrapSelectionWithTag(editor, tag);
    return;
  }

  const execCmd = EXEC_TOGGLE[kind];
  if (execCmd) {
    const before = editor.innerHTML;
    runRichTextCommand(editor, execCmd);
    if (editor.innerHTML !== before) return;
  }

  if (active || (execCmd && queryRichTextCommandState(execCmd))) {
    unwrapFormatInSelection(editor, selector);
  } else if (kind === "code") {
    wrapSelectionAsCode(editor);
  } else {
    wrapSelectionWithTag(editor, tag);
  }
}

/**
 * Liga/desliga o formato no trecho (ou estilo de digitação no caret).
 * Inline: caret colapsado nunca unwrap do texto já escrito.
 */
export function toggleComposerFormat(editor: HTMLElement, kind: ComposerFormatKind): void {
  if (INLINE_TOGGLE_KINDS.has(kind)) {
    const collapsed = selectionIsCollapsed(editor);
    const selector = SELECTOR[kind]!;
    const wasActive = isInside(editor, selector!);
    toggleInlineFormat(
      editor,
      kind as "bold" | "italic" | "strike" | "underline" | "code",
    );
    // Só preserva `<code>\u200b</code>` (etc.) recém-criado para digitação.
    // Após desligar formato / unwrap, remove cascas vazias (bolhas fantasmas).
    normalizeComposerFormatShells(editor, {
      preserveActiveTypingShell: collapsed && !wasActive,
    });
    return;
  }

  const active = queryComposerFormatFlags(editor)[kind];

  if (kind === "ul") {
    runRichTextCommand(editor, "insertUnorderedList");
    normalizeComposerFormatShells(editor);
    return;
  }
  if (kind === "ol") {
    runRichTextCommand(editor, "insertOrderedList");
    normalizeComposerFormatShells(editor);
    return;
  }
  if (kind === "quote") {
    if (active) unwrapFormatInSelection(editor, "blockquote");
    else execRichTextCommand("formatBlock", "blockquote");
    normalizeComposerFormatShells(editor);
    return;
  }
  if (kind === "link") {
    const anchor = findRichTextLinkAtSelection(editor);
    if (anchor) {
      const selection = window.getSelection();
      const range = selection?.rangeCount ? selection.getRangeAt(0) : null;
      if (range?.collapsed) {
        exitInlineFormatAtCaret(editor, anchor, selection!, range);
      } else if (range && range.toString() !== (anchor.textContent ?? "")) {
        const before = editor.innerHTML;
        runRichTextCommand(editor, "unlink");
        if (editor.innerHTML !== before) {
          normalizeComposerFormatShells(editor);
          return;
        }
        unwrapFormatInSelection(editor, "a");
      } else {
        unwrapRichTextLink(anchor);
      }
    } else {
      insertRichTextLink(editor, "https://");
    }
    normalizeComposerFormatShells(editor);
  }
}
