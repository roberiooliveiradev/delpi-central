import type { CSSProperties } from "react";

import type {
  ComunicadoContentRun,
  ComunicadoContentRunStyle,
  ComunicadoTextBlock,
} from "./comunicadoTypes";

const RUN_STYLE_KEYS: Array<keyof ComunicadoContentRunStyle> = [
  "fontSize",
  "color",
  "fontFamily",
  "textHighlight",
  "fontWeight",
  "fontStyle",
  "textDecoration",
];

function hasRunStyle(run: ComunicadoContentRun): boolean {
  if (!run.style) return false;
  return RUN_STYLE_KEYS.some((key) => run.style?.[key] != null);
}

export function plainTextFromContentRuns(runs: ComunicadoContentRun[]): string {
  return runs.map((run) => run.text).join("");
}

export function contentRunsFromPlainText(text: string): ComunicadoContentRun[] | undefined {
  if (!text) return undefined;
  return [{ text }];
}

function normalizeRunStyle(value: unknown): ComunicadoContentRunStyle | undefined {
  if (!value || typeof value !== "object") return undefined;
  const raw = value as Record<string, unknown>;
  const style: ComunicadoContentRunStyle = {};
  if (typeof raw.fontSize === "number" && Number.isFinite(raw.fontSize)) {
    style.fontSize = raw.fontSize;
  }
  if (typeof raw.color === "string" && raw.color.trim()) style.color = raw.color.trim();
  if (typeof raw.fontFamily === "string" && raw.fontFamily.trim()) {
    style.fontFamily = raw.fontFamily.trim();
  }
  if (typeof raw.textHighlight === "string" && raw.textHighlight.trim()) {
    style.textHighlight = raw.textHighlight.trim();
  }
  if (raw.fontWeight === "bold" || raw.fontWeight === "normal") style.fontWeight = raw.fontWeight;
  if (raw.fontStyle === "italic" || raw.fontStyle === "normal") style.fontStyle = raw.fontStyle;
  if (
    raw.textDecoration === "none" ||
    raw.textDecoration === "underline" ||
    raw.textDecoration === "line-through" ||
    raw.textDecoration === "underline line-through"
  ) {
    style.textDecoration = raw.textDecoration;
  }
  return Object.keys(style).length > 0 ? style : undefined;
}

function normalizeContentRun(value: unknown): ComunicadoContentRun | null {
  if (!value || typeof value !== "object") return null;
  const raw = value as Record<string, unknown>;
  const text = typeof raw.text === "string" ? raw.text : "";
  const style = normalizeRunStyle(raw.style);
  if (!text && !style) return null;
  return style ? { text, style } : { text };
}

export function normalizeContentRuns(value: unknown): ComunicadoContentRun[] | undefined {
  if (!Array.isArray(value) || value.length === 0) return undefined;
  const runs = value
    .map(normalizeContentRun)
    .filter((run): run is ComunicadoContentRun => run != null);
  return runs.length > 0 ? runs : undefined;
}

export function shouldPersistContentRuns(runs: ComunicadoContentRun[] | undefined): boolean {
  if (!runs || runs.length === 0) return false;
  if (runs.length > 1) return true;
  return hasRunStyle(runs[0]);
}

export function serializeContentRuns(
  runs: ComunicadoContentRun[] | undefined,
): Array<Record<string, unknown>> | undefined {
  if (!shouldPersistContentRuns(runs)) return undefined;
  return (runs ?? []).map((run) => {
    const payload: Record<string, unknown> = { text: run.text };
    if (run.style && Object.keys(run.style).length > 0) payload.style = run.style;
    return payload;
  });
}

export function syncTextBlockFields(
  content: string,
  contentRunsRaw: unknown,
): Pick<ComunicadoTextBlock, "content" | "contentRuns"> {
  const contentRuns = normalizeContentRuns(contentRunsRaw);
  if (contentRuns) {
    return {
      content: plainTextFromContentRuns(contentRuns),
      contentRuns: shouldPersistContentRuns(contentRuns) ? contentRuns : undefined,
    };
  }
  return { content, contentRuns: undefined };
}

export function resolveTextBlockDisplayRuns(
  block: Pick<ComunicadoTextBlock, "content" | "contentRuns">,
): ComunicadoContentRun[] {
  if (block.contentRuns && block.contentRuns.length > 0) return block.contentRuns;
  return [{ text: block.content }];
}

export function contentRunStyleToCss(
  style: ComunicadoContentRunStyle | undefined,
  options?: { fontScale?: number },
): CSSProperties {
  if (!style) return {};
  const fontScale = options?.fontScale ?? 1;
  const css: CSSProperties = {};
  if (style.fontSize != null) css.fontSize = `${Math.max(8, style.fontSize * fontScale)}px`;
  if (style.color) css.color = style.color;
  if (style.fontFamily) css.fontFamily = style.fontFamily;
  if (style.textHighlight) css.backgroundColor = style.textHighlight;
  if (style.fontWeight) css.fontWeight = style.fontWeight;
  if (style.fontStyle) css.fontStyle = style.fontStyle;
  if (style.textDecoration) css.textDecoration = style.textDecoration;
  return css;
}

export function hasRichTextRuns(block: Pick<ComunicadoTextBlock, "contentRuns">): boolean {
  return shouldPersistContentRuns(block.contentRuns);
}
