import type { CSSProperties } from "react";

import {
  contentRunStyleToCss,
  plainTextFromContentRuns,
  shouldPersistContentRuns,
  syncTextBlockFields,
} from "./comunicadoContentRuns";
import type {
  ComunicadoContentRun,
  ComunicadoContentRunStyle,
  ComunicadoTextBlock,
  ComunicadoTextDecoration,
} from "./comunicadoTypes";
import { buildTextDecoration, parseTextDecorationFlags } from "./comunicadoHelpers";

type CharToken = {
  text: string;
  style?: ComunicadoContentRunStyle;
};

export type ContentRunStyleToggleKey = "fontWeight" | "fontStyle" | "underline" | "strikethrough";

export type ContentRunSelectionStyleState = {
  fontWeight: "bold" | "normal" | "mixed";
  fontStyle: "italic" | "normal" | "mixed";
  underline: boolean | "mixed";
  strikethrough: boolean | "mixed";
};

const TOGGLE_SPECS: Record<
  ContentRunStyleToggleKey,
  {
    activate: (style: ComunicadoContentRunStyle) => ComunicadoContentRunStyle | undefined;
    deactivate: (style: ComunicadoContentRunStyle) => ComunicadoContentRunStyle | undefined;
    isActive: (style?: ComunicadoContentRunStyle) => boolean;
  }
> = {
  fontWeight: {
    isActive: (style) => style?.fontWeight === "bold",
    activate: (style) => pruneRunStyle({ ...style, fontWeight: "bold" }),
    deactivate: (style) => {
      const next = { ...style };
      delete next.fontWeight;
      return pruneRunStyle(next);
    },
  },
  fontStyle: {
    isActive: (style) => style?.fontStyle === "italic",
    activate: (style) => pruneRunStyle({ ...style, fontStyle: "italic" }),
    deactivate: (style) => {
      const next = { ...style };
      delete next.fontStyle;
      return pruneRunStyle(next);
    },
  },
  underline: {
    isActive: (style) => parseTextDecorationFlags(style?.textDecoration).underline,
    activate: (style) => {
      const flags = parseTextDecorationFlags(style?.textDecoration);
      return pruneRunStyle({
        ...style,
        textDecoration: buildTextDecoration(true, flags.strikethrough),
      });
    },
    deactivate: (style) => {
      const flags = parseTextDecorationFlags(style?.textDecoration);
      return pruneRunStyle({
        ...style,
        textDecoration: buildTextDecoration(false, flags.strikethrough),
      });
    },
  },
  strikethrough: {
    isActive: (style) => parseTextDecorationFlags(style?.textDecoration).strikethrough,
    activate: (style) => {
      const flags = parseTextDecorationFlags(style?.textDecoration);
      return pruneRunStyle({
        ...style,
        textDecoration: buildTextDecoration(flags.underline, true),
      });
    },
    deactivate: (style) => {
      const flags = parseTextDecorationFlags(style?.textDecoration);
      return pruneRunStyle({
        ...style,
        textDecoration: buildTextDecoration(flags.underline, false),
      });
    },
  },
};

function pruneRunStyle(style: ComunicadoContentRunStyle): ComunicadoContentRunStyle | undefined {
  const cleaned: ComunicadoContentRunStyle = {};
  if (style.fontSize != null) cleaned.fontSize = style.fontSize;
  if (style.color) cleaned.color = style.color;
  if (style.fontFamily) cleaned.fontFamily = style.fontFamily;
  if (style.textHighlight) cleaned.textHighlight = style.textHighlight;
  if (style.fontWeight === "bold") cleaned.fontWeight = "bold";
  if (style.fontStyle === "italic") cleaned.fontStyle = "italic";
  if (style.textDecoration && style.textDecoration !== "none") {
    cleaned.textDecoration = style.textDecoration;
  }
  return Object.keys(cleaned).length > 0 ? cleaned : undefined;
}

function runStylesEqual(
  left?: ComunicadoContentRunStyle,
  right?: ComunicadoContentRunStyle,
): boolean {
  return JSON.stringify(left ?? {}) === JSON.stringify(right ?? {});
}

export function compactContentRuns(runs: ComunicadoContentRun[]): ComunicadoContentRun[] {
  const compacted: ComunicadoContentRun[] = [];
  for (const run of runs) {
    if (!run.text) continue;
    const style = pruneRunStyle(run.style ?? {});
    const previous = compacted[compacted.length - 1];
    if (previous && runStylesEqual(previous.style, style)) {
      previous.text += run.text;
      continue;
    }
    compacted.push(style ? { text: run.text, style } : { text: run.text });
  }
  return compacted.length > 0 ? compacted : [{ text: "" }];
}

function flattenRunsToChars(runs: ComunicadoContentRun[]): CharToken[] {
  const chars: CharToken[] = [];
  for (const run of runs) {
    const style = pruneRunStyle(run.style ?? {});
    for (const char of run.text) {
      chars.push(style ? { text: char, style } : { text: char });
    }
  }
  return chars;
}

function charsToRuns(chars: CharToken[]): ComunicadoContentRun[] {
  const runs: ComunicadoContentRun[] = [];
  for (const token of chars) {
    const previous = runs[runs.length - 1];
    if (previous && runStylesEqual(previous.style, token.style)) {
      previous.text += token.text;
      continue;
    }
    runs.push(token.style ? { text: token.text, style: token.style } : { text: token.text });
  }
  return compactContentRuns(runs);
}

function clampSelectionRange(
  runs: ComunicadoContentRun[],
  start: number,
  end: number,
): { start: number; end: number } {
  const length = plainTextFromContentRuns(runs).length;
  const safeStart = Math.max(0, Math.min(length, Math.min(start, end)));
  const safeEnd = Math.max(0, Math.min(length, Math.max(start, end)));
  return { start: safeStart, end: safeEnd };
}

export function selectionRunStyleState(
  runs: ComunicadoContentRun[],
  start: number,
  end: number,
): ContentRunSelectionStyleState {
  const range = clampSelectionRange(runs, start, end);
  if (range.start >= range.end) {
    return {
      fontWeight: "normal",
      fontStyle: "normal",
      underline: false,
      strikethrough: false,
    };
  }

  const chars = flattenRunsToChars(runs).slice(range.start, range.end);
  const weightStates = new Set(chars.map((char) => (char.style?.fontWeight === "bold" ? "bold" : "normal")));
  const styleStates = new Set(chars.map((char) => (char.style?.fontStyle === "italic" ? "italic" : "normal")));
  const underlineStates = new Set(
    chars.map((char) => parseTextDecorationFlags(char.style?.textDecoration).underline),
  );
  const strikeStates = new Set(
    chars.map((char) => parseTextDecorationFlags(char.style?.textDecoration).strikethrough),
  );

  return {
    fontWeight: weightStates.size > 1 ? "mixed" : weightStates.has("bold") ? "bold" : "normal",
    fontStyle: styleStates.size > 1 ? "mixed" : styleStates.has("italic") ? "italic" : "normal",
    underline: underlineStates.size > 1 ? "mixed" : underlineStates.has(true),
    strikethrough: strikeStates.size > 1 ? "mixed" : strikeStates.has(true),
  };
}

export function toggleContentRunStyleInRange(
  runs: ComunicadoContentRun[],
  start: number,
  end: number,
  toggleKey: ContentRunStyleToggleKey,
): ComunicadoContentRun[] {
  const range = clampSelectionRange(runs, start, end);
  if (range.start >= range.end) return compactContentRuns(runs);

  const spec = TOGGLE_SPECS[toggleKey];
  const chars = flattenRunsToChars(runs);
  const slice = chars.slice(range.start, range.end);
  const shouldActivate = !slice.every((char) => spec.isActive(char.style));

  for (let index = range.start; index < range.end; index += 1) {
    const currentStyle = chars[index].style ?? {};
    const nextStyle = shouldActivate ? spec.activate(currentStyle) : spec.deactivate(currentStyle);
    chars[index] = nextStyle
      ? { text: chars[index].text, style: nextStyle }
      : { text: chars[index].text };
  }

  return charsToRuns(chars);
}

export function syncTextBlockFromRuns(
  runs: ComunicadoContentRun[],
): Pick<ComunicadoTextBlock, "content" | "contentRuns"> {
  const compacted = compactContentRuns(runs);
  return syncTextBlockFields(plainTextFromContentRuns(compacted), compacted);
}

function mergeInheritedRunStyle(
  base: ComunicadoContentRunStyle | undefined,
  patch: ComunicadoContentRunStyle,
): ComunicadoContentRunStyle | undefined {
  return pruneRunStyle({ ...(base ?? {}), ...patch });
}

function styleFromElement(element: Element): ComunicadoContentRunStyle {
  const patch: ComunicadoContentRunStyle = {};
  const tag = element.tagName.toUpperCase();
  if (tag === "B" || tag === "STRONG") patch.fontWeight = "bold";
  if (tag === "I" || tag === "EM") patch.fontStyle = "italic";
  if (tag === "U") {
    patch.textDecoration = buildTextDecoration(true, false);
  }
  if (tag === "S" || tag === "STRIKE" || tag === "DEL") {
    patch.textDecoration = buildTextDecoration(false, true);
  }

  if (element instanceof HTMLElement) {
    const computed = element.style;
    if (computed.fontWeight === "bold" || Number(computed.fontWeight) >= 600) {
      patch.fontWeight = "bold";
    }
    if (computed.fontStyle === "italic") patch.fontStyle = "italic";
    if (computed.textDecoration) {
      const flags = parseTextDecorationFlags(computed.textDecoration as ComunicadoTextDecoration);
      patch.textDecoration = buildTextDecoration(flags.underline, flags.strikethrough);
    }
    if (computed.color) patch.color = computed.color;
    if (computed.backgroundColor) patch.textHighlight = computed.backgroundColor;
    if (computed.fontFamily) patch.fontFamily = computed.fontFamily;
    if (computed.fontSize) {
      const parsed = Number.parseFloat(computed.fontSize);
      if (Number.isFinite(parsed)) patch.fontSize = parsed;
    }
  }

  return patch;
}

export function contentRunsFromEditableRoot(root: HTMLElement): ComunicadoContentRun[] {
  const runs: ComunicadoContentRun[] = [];

  function appendText(text: string, style?: ComunicadoContentRunStyle) {
    if (!text) return;
    const normalizedStyle = pruneRunStyle(style ?? {});
    const previous = runs[runs.length - 1];
    if (previous && runStylesEqual(previous.style, normalizedStyle)) {
      previous.text += text;
      return;
    }
    runs.push(normalizedStyle ? { text, style: normalizedStyle } : { text });
  }

  function walk(node: Node, inherited?: ComunicadoContentRunStyle) {
    if (node.nodeType === Node.TEXT_NODE) {
      appendText(node.textContent ?? "", inherited);
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    const element = node as Element;
    if (element.tagName === "BR") {
      appendText("\n", inherited);
      return;
    }
    const merged = mergeInheritedRunStyle(inherited, styleFromElement(element));
    for (const child of element.childNodes) {
      walk(child, merged);
    }
  }

  for (const child of root.childNodes) {
    walk(child);
  }

  return compactContentRuns(runs);
}

export function runStyleToInlineCss(
  style: ComunicadoContentRunStyle | undefined,
  options?: { fontScale?: number },
): string {
  const css = contentRunStyleToCss(style, options);
  return Object.entries(css)
    .map(([key, value]) => {
      const property = key.replace(/[A-Z]/g, (match) => `-${match.toLowerCase()}`);
      return `${property}:${value}`;
    })
    .join(";");
}

export function renderContentRunsHtml(
  runs: ComunicadoContentRun[],
  options?: { fontScale?: number },
): string {
  const resolved = compactContentRuns(runs);
  if (resolved.length === 1 && !resolved[0].style) {
    return escapeHtml(resolved[0].text);
  }
  return resolved
    .map((run) => {
      const inline = runStyleToInlineCss(run.style, options);
      if (!inline) return escapeHtml(run.text);
      return `<span style="${inline}">${escapeHtml(run.text)}</span>`;
    })
    .join("");
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function getEditableTextSelectionOffsets(
  root: HTMLElement,
): { start: number; end: number } | null {
  const selection = root.ownerDocument.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  const range = selection.getRangeAt(0);
  if (!root.contains(range.startContainer) || !root.contains(range.endContainer)) return null;

  const start = measureTextOffset(root, range.startContainer, range.startOffset);
  const end = measureTextOffset(root, range.endContainer, range.endOffset);
  return { start: Math.min(start, end), end: Math.max(start, end) };
}

function measureTextOffset(root: HTMLElement, container: Node, offset: number): number {
  const walker = root.ownerDocument.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let total = 0;
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (node === container) return total + offset;
    total += node.textContent?.length ?? 0;
  }
  return total;
}

export function restoreEditableTextSelection(
  root: HTMLElement,
  start: number,
  end: number,
): void {
  const selection = root.ownerDocument.getSelection();
  if (!selection) return;
  const startPos = locateTextPosition(root, start);
  const endPos = locateTextPosition(root, end);
  if (!startPos || !endPos) return;
  const range = root.ownerDocument.createRange();
  range.setStart(startPos.node, startPos.offset);
  range.setEnd(endPos.node, endPos.offset);
  selection.removeAllRanges();
  selection.addRange(range);
}

function locateTextPosition(
  root: HTMLElement,
  absoluteOffset: number,
): { node: Text; offset: number } | null {
  const walker = root.ownerDocument.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let remaining = Math.max(0, absoluteOffset);
  while (walker.nextNode()) {
    const node = walker.currentNode as Text;
    const length = node.textContent?.length ?? 0;
    if (remaining <= length) return { node, offset: remaining };
    remaining -= length;
  }
  return null;
}

export function hasPersistableContentRuns(runs: ComunicadoContentRun[] | undefined): boolean {
  return shouldPersistContentRuns(runs);
}

export function contentRunInlineStyleProperties(
  style: ComunicadoContentRunStyle | undefined,
  options?: { fontScale?: number },
): CSSProperties {
  return contentRunStyleToCss(style, options);
}
