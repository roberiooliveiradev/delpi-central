import type {
  ComunicadoContentRun,
  ComunicadoContentRunStyle,
  ComunicadoListType,
} from "./comunicadoTypes";

export type ContentLineSegment = {
  runs: ComunicadoContentRun[];
  listType?: ComunicadoListType;
};

export type TextDisplaySegment =
  | { kind: "text"; runs: ComunicadoContentRun[] }
  | { kind: "list"; listType: ComunicadoListType; items: ComunicadoContentRun[][] };

export type ContentRunListSelectionState = {
  bullet: boolean | "mixed";
  ordered: boolean | "mixed";
};

type CharToken = {
  text: string;
  style?: ComunicadoContentRunStyle;
};

function pruneRunStyle(style: ComunicadoContentRunStyle): ComunicadoContentRunStyle | undefined {
  const cleaned: ComunicadoContentRunStyle = {};
  if (style.fontSize != null) cleaned.fontSize = style.fontSize;
  if (style.color) cleaned.color = style.color;
  if (style.fontFamily) cleaned.fontFamily = style.fontFamily;
  if (style.textHighlight) cleaned.textHighlight = style.textHighlight;
  if (style.fontWeight === "bold") cleaned.fontWeight = "bold";
  if (style.fontStyle === "italic") cleaned.fontStyle = style.fontStyle;
  if (style.textDecoration && style.textDecoration !== "none") {
    cleaned.textDecoration = style.textDecoration;
  }
  if (style.listType === "bullet" || style.listType === "ordered") {
    cleaned.listType = style.listType;
  }
  return Object.keys(cleaned).length > 0 ? cleaned : undefined;
}

function runStylesEqual(
  left?: ComunicadoContentRunStyle,
  right?: ComunicadoContentRunStyle,
): boolean {
  return JSON.stringify(left ?? {}) === JSON.stringify(right ?? {});
}

function compactContentRuns(runs: ComunicadoContentRun[]): ComunicadoContentRun[] {
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

function lineListType(chars: CharToken[]): ComunicadoListType | undefined {
  for (const char of chars) {
    if (char.text === "\n") continue;
    if (char.style?.listType) return char.style.listType;
  }
  return undefined;
}

function stripListTypeFromStyle(
  style: ComunicadoContentRunStyle | undefined,
): ComunicadoContentRunStyle | undefined {
  if (!style?.listType) return pruneRunStyle(style ?? {});
  const next = { ...style };
  delete next.listType;
  return pruneRunStyle(next);
}

function applyListTypeToLineChars(
  chars: CharToken[],
  listType: ComunicadoListType | undefined,
): CharToken[] {
  return chars.map((char) => {
    if (char.text === "\n") return char;
    const base = stripListTypeFromStyle(char.style) ?? {};
    if (!listType) {
      const next = pruneRunStyle(base);
      return next ? { text: char.text, style: next } : { text: char.text };
    }
    return { text: char.text, style: pruneRunStyle({ ...base, listType }) };
  });
}

export function splitContentRunsIntoLines(runs: ComunicadoContentRun[]): ContentLineSegment[] {
  const chars = flattenRunsToChars(runs);
  if (chars.length === 0) return [{ runs: [{ text: "" }] }];

  const lines: ContentLineSegment[] = [];
  let current: CharToken[] = [];

  for (const char of chars) {
    if (char.text === "\n") {
      lines.push({
        runs: charsToRuns(current),
        listType: lineListType(current),
      });
      current = [];
      continue;
    }
    current.push(char);
  }

  lines.push({
    runs: charsToRuns(current),
    listType: lineListType(current),
  });
  return lines;
}

export function joinContentLinesToRuns(lines: ContentLineSegment[]): ComunicadoContentRun[] {
  if (lines.length === 0) return [{ text: "" }];

  const merged: ComunicadoContentRun[] = [];
  lines.forEach((line, index) => {
    const lineRuns = line.listType
      ? line.runs.map((run) => {
          const base = stripListTypeFromStyle(run.style) ?? {};
          return {
            text: run.text,
            style: pruneRunStyle({ ...base, listType: line.listType }),
          };
        })
      : line.runs.map((run) => {
          const style = stripListTypeFromStyle(run.style);
          return style ? { text: run.text, style } : { text: run.text };
        });

    for (const run of lineRuns) {
      if (!run.text) continue;
      const previous = merged[merged.length - 1];
      if (previous && runStylesEqual(previous.style, run.style)) {
        previous.text += run.text;
        continue;
      }
      merged.push(run.style ? { text: run.text, style: run.style } : { text: run.text });
    }

    if (index < lines.length - 1) {
      const previous = merged[merged.length - 1];
      if (previous && !previous.style) {
        previous.text += "\n";
      } else {
        merged.push({ text: "\n" });
      }
    }
  });

  return compactContentRuns(merged.length > 0 ? merged : [{ text: "" }]);
}

function lineIndexForOffset(chars: CharToken[], offset: number): number {
  if (chars.length === 0) return 0;
  let line = 0;
  for (let index = 0; index < Math.min(offset, chars.length); index += 1) {
    if (chars[index].text === "\n") line += 1;
  }
  return line;
}

function lineRangeForOffsets(
  chars: CharToken[],
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

export function hasListContentRuns(runs: ComunicadoContentRun[]): boolean {
  return splitContentRunsIntoLines(runs).some((line) => line.listType != null);
}

export function selectionListTypeState(
  runs: ComunicadoContentRun[],
  start: number,
  end: number,
): ContentRunListSelectionState {
  const chars = flattenRunsToChars(runs);
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
  const bulletStates = new Set(selected.map((line) => line.listType === "bullet"));
  const orderedStates = new Set(selected.map((line) => line.listType === "ordered"));

  return {
    bullet: bulletStates.size > 1 ? "mixed" : bulletStates.has(true),
    ordered: orderedStates.size > 1 ? "mixed" : orderedStates.has(true),
  };
}

export function toggleListTypeInRange(
  runs: ComunicadoContentRun[],
  start: number,
  end: number,
  listType: ComunicadoListType,
): ComunicadoContentRun[] {
  const chars = flattenRunsToChars(runs);
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
  const targetLines = lines.slice(lineStart, lineEnd + 1);
  const allActive = targetLines.length > 0 && targetLines.every((line) => line.listType === listType);
  const nextListType = allActive ? undefined : listType;

  const nextLines = lines.map((line, index) => {
    if (index < lineStart || index > lineEnd) return line;
    const lineChars = flattenRunsToChars(line.runs);
    return {
      runs: charsToRuns(applyListTypeToLineChars(lineChars, nextListType)),
      listType: nextListType,
    };
  });

  return joinContentLinesToRuns(nextLines);
}

export function toggleListTypeOnAllLines(
  runs: ComunicadoContentRun[],
  listType: ComunicadoListType,
): ComunicadoContentRun[] {
  const lines = splitContentRunsIntoLines(runs);
  const allActive = lines.length > 0 && lines.every((line) => line.listType === listType);
  const nextListType = allActive ? undefined : listType;
  const nextLines = lines.map((line) => {
    const lineChars = flattenRunsToChars(line.runs);
    return {
      runs: charsToRuns(applyListTypeToLineChars(lineChars, nextListType)),
      listType: nextListType,
    };
  });
  return joinContentLinesToRuns(nextLines);
}

export function insertLineBreakAtOffset(
  runs: ComunicadoContentRun[],
  offset: number,
): ComunicadoContentRun[] {
  const chars = flattenRunsToChars(runs);
  const length = chars.length;
  const safeOffset = Math.max(0, Math.min(length, offset));
  const lines = splitContentRunsIntoLines(runs);
  const lineIndex = lineIndexForOffset(chars, safeOffset);
  const currentLine = lines[lineIndex];
  const inheritedListType = currentLine?.listType;

  let lineCharStart = 0;
  for (let index = 0; index < lineIndex; index += 1) {
    lineCharStart += flattenRunsToChars(lines[index].runs).length + 1;
  }
  const withinLine = safeOffset - lineCharStart;

  const beforeChars = flattenRunsToChars(currentLine?.runs ?? [{ text: "" }]).slice(0, withinLine);
  const afterChars = flattenRunsToChars(currentLine?.runs ?? [{ text: "" }]).slice(withinLine);

  const nextLines = [...lines];
  nextLines.splice(lineIndex, 1, {
    runs: charsToRuns(beforeChars),
    listType: currentLine?.listType,
  }, {
    runs: charsToRuns(
      inheritedListType
        ? applyListTypeToLineChars(afterChars.length > 0 ? afterChars : [{ text: "" }], inheritedListType)
        : afterChars.length > 0
          ? afterChars
          : [{ text: "" }],
    ),
    listType: inheritedListType,
  });

  return joinContentLinesToRuns(nextLines);
}

export function groupContentRunsForDisplay(runs: ComunicadoContentRun[]): TextDisplaySegment[] {
  const lines = splitContentRunsIntoLines(runs);
  const segments: TextDisplaySegment[] = [];

  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.listType) {
      segments.push({ kind: "text", runs: line.runs });
      index += 1;
      continue;
    }

    const listType = line.listType;
    const items: ComunicadoContentRun[][] = [];
    while (index < lines.length && lines[index].listType === listType) {
      items.push(lines[index].runs);
      index += 1;
    }
    segments.push({ kind: "list", listType, items });
  }

  return segments;
}

export function contentRunsHaveListOrRichStyle(runs: ComunicadoContentRun[]): boolean {
  if (runs.length > 1) return true;
  const style = runs[0]?.style;
  if (!style) return false;
  return Object.keys(style).length > 0;
}
