import type { CSSProperties } from "react";

import {
  joinContentLinesToRuns,
  splitContentRunsIntoLines,
  type ContentLineSegment,
} from "./comunicadoContentList";
import { contentRunStyleToCss } from "./comunicadoContentRuns";
import type {
  ComunicadoContentRun,
  ComunicadoContentRunStyle,
  ComunicadoNamedTextStyle,
  ComunicadoTextBlock,
} from "./comunicadoTypes";

export type ContentRunNamedStyleSelectionState = ComunicadoNamedTextStyle | "mixed" | null;

export const COMUNICADO_NAMED_TEXT_STYLE_OPTIONS: Array<{
  key: ComunicadoNamedTextStyle;
  label: string;
}> = [
  { key: "title1", label: "Título 1" },
  { key: "subtitle", label: "Subtítulo" },
  { key: "body", label: "Corpo" },
];

const NAMED_STYLE_PRESETS: Record<ComunicadoNamedTextStyle, ComunicadoContentRunStyle> = {
  title1: {
    fontSize: 56,
    fontWeight: "bold",
    lineHeight: 1.15,
  },
  subtitle: {
    fontSize: 36,
    fontWeight: "normal",
    lineHeight: 1.2,
  },
  body: {
    fontSize: 28,
    fontWeight: "normal",
    lineHeight: 1.15,
  },
};

export function namedTextStylePreset(key: ComunicadoNamedTextStyle): ComunicadoContentRunStyle {
  return { ...NAMED_STYLE_PRESETS[key] };
}

export function defaultNamedStyleForBlockType(
  type: ComunicadoTextBlock["type"],
): ComunicadoNamedTextStyle {
  return type === "heading" ? "title1" : "body";
}

export function stripNamedStyleFromRunStyle(
  style: ComunicadoContentRunStyle | undefined,
): ComunicadoContentRunStyle | undefined {
  if (!style?.namedStyle) {
    if (!style) return undefined;
    const { namedStyle: _omit, ...rest } = style;
    return Object.keys(rest).length > 0 ? rest : undefined;
  }
  const next = { ...style };
  delete next.namedStyle;
  return Object.keys(next).length > 0 ? next : undefined;
}

export function resolveEffectiveRunStyle(
  style: ComunicadoContentRunStyle | undefined,
  options?: { fontScale?: number },
): CSSProperties {
  if (!style?.namedStyle) return contentRunStyleToCss(style, options);
  const { namedStyle, ...inline } = style;
  const preset = namedTextStylePreset(namedStyle);
  const merged: ComunicadoContentRunStyle = { ...preset, ...inline };
  return contentRunStyleToCss(merged, options);
}

function lineIndexForOffset(chars: Array<{ text: string }>, offset: number): number {
  if (chars.length === 0) return 0;
  let line = 0;
  for (let index = 0; index < Math.min(offset, chars.length); index += 1) {
    if (chars[index].text === "\n") line += 1;
  }
  return line;
}

function flattenRunChars(runs: ComunicadoContentRun[]): Array<{ text: string }> {
  const chars: Array<{ text: string }> = [];
  for (const run of runs) {
    for (const char of run.text) chars.push({ text: char });
  }
  return chars;
}

function lineRangeForOffsets(
  chars: Array<{ text: string }>,
  start: number,
  end: number,
): { startLine: number; endLine: number } {
  const safeStart = Math.max(0, Math.min(chars.length, Math.min(start, end)));
  const safeEnd = Math.max(0, Math.min(chars.length, Math.max(start, end)));
  return {
    startLine: lineIndexForOffset(chars, safeStart),
    endLine: lineIndexForOffset(chars, Math.max(safeStart, safeEnd - 1)),
  };
}

export function hasNamedStyleContentRuns(runs: ComunicadoContentRun[]): boolean {
  return splitContentRunsIntoLines(runs).some((line) => line.namedStyle != null);
}

export function selectionNamedStyleState(
  runs: ComunicadoContentRun[],
  start: number,
  end: number,
): ContentRunNamedStyleSelectionState {
  const chars = flattenRunChars(runs);
  const length = chars.length;
  const safeStart = Math.max(0, Math.min(length, Math.min(start, end)));
  const safeEnd = Math.max(0, Math.min(length, Math.max(start, end)));

  let lineStart: number;
  let lineEnd: number;
  if (safeStart >= safeEnd) {
    const line = lineIndexForOffset(chars, safeStart);
    lineStart = line;
    lineEnd = line;
  } else {
    const range = lineRangeForOffsets(chars, safeStart, safeEnd);
    lineStart = range.startLine;
    lineEnd = range.endLine;
  }

  const lines = splitContentRunsIntoLines(runs);
  const selected = lines.slice(lineStart, lineEnd + 1);
  const styles = new Set(selected.map((line) => line.namedStyle ?? null));
  if (styles.size > 1) return "mixed";
  const [only] = [...styles];
  return only;
}

function applyNamedStyleToLine(
  line: ContentLineSegment,
  namedStyle: ComunicadoNamedTextStyle | undefined,
): ContentLineSegment {
  const nextRuns = line.runs.map((run) => {
    const base = stripNamedStyleFromRunStyle(run.style) ?? {};
    if (!namedStyle) {
      const style = Object.keys(base).length > 0 ? base : undefined;
      return style ? { text: run.text, style } : { text: run.text };
    }
    return {
      text: run.text,
      style: { ...base, namedStyle },
    };
  });
  return {
    runs: nextRuns,
    listType: line.listType,
    namedStyle,
  };
}

export function applyNamedStyleInRange(
  runs: ComunicadoContentRun[],
  start: number,
  end: number,
  namedStyle: ComunicadoNamedTextStyle,
): ComunicadoContentRun[] {
  const chars = flattenRunChars(runs);
  const length = chars.length;
  const safeStart = Math.max(0, Math.min(length, Math.min(start, end)));
  const safeEnd = Math.max(0, Math.min(length, Math.max(start, end)));

  let lineStart: number;
  let lineEnd: number;
  if (safeStart >= safeEnd) {
    const line = lineIndexForOffset(chars, safeStart);
    lineStart = line;
    lineEnd = line;
  } else {
    const range = lineRangeForOffsets(chars, safeStart, safeEnd);
    lineStart = range.startLine;
    lineEnd = range.endLine;
  }

  const lines = splitContentRunsIntoLines(runs);
  const nextLines = lines.map((line, index) => {
    if (index < lineStart || index > lineEnd) return line;
    return applyNamedStyleToLine(line, namedStyle);
  });
  return joinContentLinesToRuns(nextLines);
}

export function applyNamedStyleOnAllLines(
  runs: ComunicadoContentRun[],
  namedStyle: ComunicadoNamedTextStyle,
): ComunicadoContentRun[] {
  const lines = splitContentRunsIntoLines(runs);
  return joinContentLinesToRuns(lines.map((line) => applyNamedStyleToLine(line, namedStyle)));
}

export function resolveNamedStyleSelectionForBlock(
  block: Pick<ComunicadoTextBlock, "type" | "content" | "contentRuns">,
  start: number,
  end: number,
): ContentRunNamedStyleSelectionState {
  const runs = block.contentRuns?.length
    ? block.contentRuns
    : [{ text: block.content }];
  const state = selectionNamedStyleState(runs, start, end);
  if (state === "mixed" || state != null) return state;
  return defaultNamedStyleForBlockType(block.type);
}
