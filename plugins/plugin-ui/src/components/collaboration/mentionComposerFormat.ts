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
import { expandCollapsedSelectionForFormat } from "./mentionComposerCaret";

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

function unwrapClosest(editor: HTMLElement, selector: string): void {
  const hit = matchingFormatElement(editor, selector);
  if (hit) unwrapRichTextElement(hit);
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

/** Liga/desliga o formato no trecho selecionado (ou na mensagem, se o caret estiver colapsado). */
export function toggleComposerFormat(editor: HTMLElement, kind: ComposerFormatKind): void {
  expandCollapsedSelectionForFormat(editor);
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
    if (active) unwrapClosest(editor, "blockquote");
    else execRichTextCommand("formatBlock", "blockquote");
    return;
  }
  if (kind === "link") {
    const anchor = findRichTextLinkAtSelection(editor);
    if (anchor) unwrapRichTextLink(anchor);
    else insertRichTextLink(editor, "https://");
    return;
  }

  const selector = SELECTOR[kind];
  const tag = WRAP_TAG[kind];
  if (!selector || !tag) return;
  if (active) unwrapClosest(editor, selector);
  else wrapSelectionWithTag(editor, tag);
}
