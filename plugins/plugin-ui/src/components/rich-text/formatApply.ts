/**
 * Canonical format apply for RichTextEditor + MentionComposer.
 * UI emits FormatIntent; this module resolves the target and mutates the DOM.
 *
 * @see plugins/plugin-ui/docs/rich-text-selection-format-study.md
 */
import {
  applyRichTextAlign,
  applyRichTextFontFamily,
  applyRichTextFontSize,
  applyRichTextForeColor,
  applyRichTextHiliteColor,
  insertRichTextHorizontalRule,
  restoreRichTextSelection,
  runRichTextCommand,
  type RichTextAlign,
} from "./richTextCommands";
import {
  insertRichTextInlineImageAtCaret,
  type RichTextInlineImageInsert,
} from "./richTextInlineImage";

export type FormatIntentClass = "inline" | "block" | "object" | "insert";

export type FormatIntent =
  | { class: "inline"; op: "bold" }
  | { class: "inline"; op: "italic" }
  | { class: "inline"; op: "underline" }
  | { class: "inline"; op: "strikeThrough" }
  | { class: "inline"; op: "foreColor"; value: string }
  | { class: "inline"; op: "hiliteColor"; value: string }
  | { class: "inline"; op: "fontName"; value: string }
  | { class: "inline"; op: "fontSize"; value: number }
  | { class: "inline"; op: "removeFormat" }
  | { class: "block"; op: "align"; value: RichTextAlign }
  | { class: "block"; op: "formatBlock"; value: string }
  | { class: "block"; op: "insertUnorderedList" }
  | { class: "block"; op: "insertOrderedList" }
  | { class: "block"; op: "indent" }
  | { class: "block"; op: "outdent" }
  | { class: "insert"; op: "horizontalRule" }
  | { class: "insert"; op: "image"; value: RichTextInlineImageInsert };

export type FormatTarget =
  | { type: "range"; range: Range }
  | { type: "caret"; range: Range }
  | { type: "block"; element: HTMLElement; range: Range }
  | { type: "none" };

export type ApplyFormatOptions = {
  /** Saved toolbar selection — restored before mutate (S-F2). */
  savedRange?: Range | null;
};

const ALIGN_BLOCK_SELECTOR = "p,li,h1,h2,h3,h4,h5,h6,blockquote";

function liveRangeInEditor(editor: HTMLElement): Range | null {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  const range = selection.getRangeAt(0);
  if (!editor.contains(range.commonAncestorContainer)) return null;
  return range;
}

/** Resolve where an intent should apply given current (or restored) selection. */
export function resolveFormatTarget(
  editor: HTMLElement,
  intent: FormatIntent,
): FormatTarget {
  const range = liveRangeInEditor(editor);
  if (!range) return { type: "none" };

  if (intent.class === "block") {
    const node =
      range.commonAncestorContainer instanceof Element
        ? range.commonAncestorContainer
        : range.commonAncestorContainer.parentElement;
    const block = node?.closest(ALIGN_BLOCK_SELECTOR);
    if (block instanceof HTMLElement && editor.contains(block) && block !== editor) {
      return { type: "block", element: block, range };
    }
    return { type: range.collapsed ? "caret" : "range", range };
  }

  if (intent.class === "insert") {
    return { type: range.collapsed ? "caret" : "range", range };
  }

  // inline / object
  return { type: range.collapsed ? "caret" : "range", range };
}

function applyInline(editor: HTMLElement, intent: Extract<FormatIntent, { class: "inline" }>) {
  switch (intent.op) {
    case "bold":
    case "italic":
    case "underline":
    case "strikeThrough":
    case "removeFormat":
      runRichTextCommand(editor, intent.op);
      return;
    case "foreColor":
      applyRichTextForeColor(editor, intent.value);
      return;
    case "hiliteColor":
      applyRichTextHiliteColor(editor, intent.value);
      return;
    case "fontName":
      applyRichTextFontFamily(editor, intent.value);
      return;
    case "fontSize":
      applyRichTextFontSize(editor, intent.value);
      return;
    default:
      return;
  }
}

function applyBlock(editor: HTMLElement, intent: Extract<FormatIntent, { class: "block" }>) {
  switch (intent.op) {
    case "align":
      applyRichTextAlign(editor, intent.value);
      return;
    case "formatBlock":
      runRichTextCommand(editor, "formatBlock", intent.value);
      return;
    case "insertUnorderedList":
    case "insertOrderedList":
    case "indent":
    case "outdent":
      runRichTextCommand(editor, intent.op);
      return;
    default:
      return;
  }
}

function applyInsert(editor: HTMLElement, intent: Extract<FormatIntent, { class: "insert" }>) {
  switch (intent.op) {
    case "horizontalRule":
      insertRichTextHorizontalRule(editor);
      return;
    case "image":
      insertRichTextInlineImageAtCaret(editor, intent.value);
      return;
    default:
      return;
  }
}

/**
 * Single entrypoint: restore selection → resolve target → apply.
 * Consumers must not call execCommand / stamp helpers directly.
 */
export function applyFormat(
  editor: HTMLElement | null,
  intent: FormatIntent,
  options?: ApplyFormatOptions,
): FormatTarget {
  if (!editor) return { type: "none" };

  restoreRichTextSelection(editor, options?.savedRange ?? null);
  const target = resolveFormatTarget(editor, intent);
  if (target.type === "none" && intent.class !== "insert") {
    // Still try insert/ops that create content at end.
    if (intent.class === "inline" || intent.class === "block") {
      restoreRichTextSelection(editor, null);
    }
  }

  if (intent.class === "inline") applyInline(editor, intent);
  else if (intent.class === "block") applyBlock(editor, intent);
  else if (intent.class === "insert") applyInsert(editor, intent);

  return resolveFormatTarget(editor, intent);
}

/** Convenience builders for toolbar / shortcuts. */
export const formatIntent = {
  bold: (): FormatIntent => ({ class: "inline", op: "bold" }),
  italic: (): FormatIntent => ({ class: "inline", op: "italic" }),
  underline: (): FormatIntent => ({ class: "inline", op: "underline" }),
  strikeThrough: (): FormatIntent => ({ class: "inline", op: "strikeThrough" }),
  removeFormat: (): FormatIntent => ({ class: "inline", op: "removeFormat" }),
  foreColor: (value: string): FormatIntent => ({ class: "inline", op: "foreColor", value }),
  hiliteColor: (value: string): FormatIntent => ({ class: "inline", op: "hiliteColor", value }),
  fontName: (value: string): FormatIntent => ({ class: "inline", op: "fontName", value }),
  fontSize: (value: number): FormatIntent => ({ class: "inline", op: "fontSize", value }),
  align: (value: RichTextAlign): FormatIntent => ({ class: "block", op: "align", value }),
  formatBlock: (value: string): FormatIntent => ({ class: "block", op: "formatBlock", value }),
  unorderedList: (): FormatIntent => ({ class: "block", op: "insertUnorderedList" }),
  orderedList: (): FormatIntent => ({ class: "block", op: "insertOrderedList" }),
  indent: (): FormatIntent => ({ class: "block", op: "indent" }),
  outdent: (): FormatIntent => ({ class: "block", op: "outdent" }),
  horizontalRule: (): FormatIntent => ({ class: "insert", op: "horizontalRule" }),
  image: (value: RichTextInlineImageInsert): FormatIntent => ({
    class: "insert",
    op: "image",
    value,
  }),
};
