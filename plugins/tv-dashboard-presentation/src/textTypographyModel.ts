import { clampFontSize } from "./comunicadoHelpers";
import type {
  ComunicadoContentRun,
  ComunicadoContentRunStyle,
  ComunicadoTextCaseTransform,
} from "./comunicadoTypes";
import {
  COMUNICADO_FONT_SIZE_MAX,
  COMUNICADO_FONT_SIZE_MIN,
  COMUNICADO_FONT_SIZE_STEP,
} from "./comunicadoTypes";

export const COMUNICADO_INDENT_LEVEL_MIN = 0;
export const COMUNICADO_INDENT_LEVEL_MAX = 8;
/** Pixels por nível de indent (paint canônico). */
export const COMUNICADO_INDENT_PX_PER_LEVEL = 24;

export function clampIndentLevel(raw: unknown): number {
  if (typeof raw !== "number" || !Number.isFinite(raw)) return 0;
  return Math.min(
    COMUNICADO_INDENT_LEVEL_MAX,
    Math.max(COMUNICADO_INDENT_LEVEL_MIN, Math.trunc(raw)),
  );
}

export function bumpFontSizeValue(
  current: number | null | undefined,
  deltaSteps: number,
  fallback = 28,
): number {
  const base =
    typeof current === "number" && Number.isFinite(current) ? current : fallback;
  const next = base + deltaSteps * COMUNICADO_FONT_SIZE_STEP;
  return clampFontSize(
    Math.min(COMUNICADO_FONT_SIZE_MAX, Math.max(COMUNICADO_FONT_SIZE_MIN, next)),
  );
}

/**
 * Transformação canônica de maiúsculas (conteúdo). Locale pt-BR via toLocale*.
 * Não usa CSS text-transform.
 */
export function transformTextCase(
  text: string,
  mode: ComunicadoTextCaseTransform,
): string {
  if (!text) return text;
  switch (mode) {
    case "lower":
      return text.toLocaleLowerCase("pt-BR");
    case "upper":
      return text.toLocaleUpperCase("pt-BR");
    case "title":
      return text
        .toLocaleLowerCase("pt-BR")
        .replace(/(^|[^\p{L}\p{N}])(\p{L})/gu, (_, boundary: string, ch: string) => {
          return `${boundary}${ch.toLocaleUpperCase("pt-BR")}`;
        });
    case "toggle": {
      let out = "";
      for (const ch of text) {
        const lower = ch.toLocaleLowerCase("pt-BR");
        const upper = ch.toLocaleUpperCase("pt-BR");
        if (ch === lower && ch !== upper) out += upper;
        else if (ch === upper && ch !== lower) out += lower;
        else out += ch;
      }
      return out;
    }
    case "sentence": {
      const lower = text.toLocaleLowerCase("pt-BR");
      const match = lower.match(/\p{L}/u);
      if (!match || match.index == null) return lower;
      const i = match.index;
      return (
        lower.slice(0, i) +
        lower.charAt(i).toLocaleUpperCase("pt-BR") +
        lower.slice(i + 1)
      );
    }
    default:
      return text;
  }
}

/** Aplica case transform aos runs; dataRef permanece atômico (texto placeholder preservado). */
export function transformContentRunsCase(
  runs: ComunicadoContentRun[],
  mode: ComunicadoTextCaseTransform,
  range?: { start: number; end: number },
): ComunicadoContentRun[] {
  if (!runs.length) return runs;
  if (!range || range.start >= range.end) {
    return runs.map((run) => {
      if (run.dataRef?.field?.trim()) return run;
      return { ...run, text: transformTextCase(run.text, mode) };
    });
  }
  // Character-wise for range — expand handled by caller for dataRefs.
  let pos = 0;
  const out: ComunicadoContentRun[] = [];
  for (const run of runs) {
    const len = run.dataRef?.field?.trim() ? (run.text || "…").length : run.text.length;
    const runStart = pos;
    const runEnd = pos + len;
    pos = runEnd;
    if (run.dataRef?.field?.trim()) {
      out.push(run);
      continue;
    }
    if (runEnd <= range.start || runStart >= range.end) {
      out.push(run);
      continue;
    }
    const localStart = Math.max(0, range.start - runStart);
    const localEnd = Math.min(run.text.length, range.end - runStart);
    const before = run.text.slice(0, localStart);
    const mid = transformTextCase(run.text.slice(localStart, localEnd), mode);
    const after = run.text.slice(localEnd);
    out.push({ ...run, text: `${before}${mid}${after}` });
  }
  return out;
}

export function applyBaselineShiftToCss(
  style: Pick<ComunicadoContentRunStyle, "baselineShift"> | undefined,
  css: { verticalAlign?: string; fontSize?: string | number },
): void {
  if (!style?.baselineShift) return;
  if (style.baselineShift === "sub") {
    css.verticalAlign = "sub";
    if (css.fontSize == null) css.fontSize = "0.75em";
  } else if (style.baselineShift === "super") {
    css.verticalAlign = "super";
    if (typeof css.fontSize === "string" && css.fontSize.endsWith("px")) {
      // keep absolute size; browsers scale sub/super via vertical-align
    } else if (css.fontSize == null) {
      css.fontSize = "0.75em";
    }
  }
}

export function indentPaddingPx(indentLevel: number | null | undefined): number {
  return clampIndentLevel(indentLevel) * COMUNICADO_INDENT_PX_PER_LEVEL;
}
