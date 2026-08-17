import { getDisplayFormatPreset } from "./catalog";
import { formatCustomPattern } from "./formatCustomPattern";
import {
  isLocalizedChartPeriodLabel,
  localizeEnglishMonthTokensInLabel,
  monthAbbrevPt,
  monthFullPt,
  parseDisplayDate,
  weekdayFullPt,
} from "./parseDisplayDate";
import { EMPTY_DISPLAY, type DisplayFormatSpec } from "./types";

export function formatDisplayValue(
  value: unknown,
  spec: DisplayFormatSpec | null | undefined,
): string {
  const resolved = normalizeSpec(spec);
  if (value === null || value === undefined || value === "") return EMPTY_DISPLAY;

  if (resolved.category === "text") {
    return String(value);
  }

  if (resolved.category === "custom") {
    const pattern = resolved.pattern?.trim();
    if (!pattern) return stringifyFallback(value);
    const custom = formatCustomPattern(value, pattern);
    return custom ?? stringifyFallback(value);
  }

  if (resolved.category === "date" || resolved.category === "time") {
    if (typeof value === "string" && isLocalizedChartPeriodLabel(value)) {
      /* «Jan. de 26» da API — não reformatar como dd/mm/yyyy. */
      return localizeEnglishMonthTokensInLabel(value);
    }
    const date = parseDisplayDate(value);
    if (!date) return stringifyFallback(value);
    return formatDateSpec(date, resolved, String(value));
  }

  const num = coerceNumber(value);
  if (num == null) {
    const date = parseDisplayDate(value);
    if (date && resolved.category === "general") return stringifyFallback(value);
    return stringifyFallback(value);
  }
  return formatNumberSpec(num, resolved);
}

export function normalizeSpec(spec: DisplayFormatSpec | null | undefined): DisplayFormatSpec {
  if (!spec?.category) return { category: "general" };
  const preset = spec.presetId ? getDisplayFormatPreset(spec.presetId) : null;
  if (preset && spec.category === preset.category) {
    return {
      ...preset.spec,
      ...spec,
      presetId: spec.presetId,
      locale: spec.locale ?? "pt-BR",
    };
  }
  return { locale: "pt-BR", ...spec };
}

function coerceNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() && !Number.isNaN(Number(value))) {
    const n = Number(value.trim().replace(/\s/g, "").replace(",", "."));
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function stringifyFallback(value: unknown): string {
  if (value === null || value === undefined || value === "") return EMPTY_DISPLAY;
  return String(value);
}

function clampPlaces(raw: number | null | undefined, fallback: number): number {
  if (typeof raw === "number" && Number.isFinite(raw)) {
    return Math.min(8, Math.max(0, Math.trunc(raw)));
  }
  return fallback;
}

function formatNumberSpec(value: number, spec: DisplayFormatSpec): string {
  const presetId = spec.presetId;
  if (presetId === "number-compact" || (spec.category === "number" && presetId === "number-compact")) {
    return value.toLocaleString("pt-BR", {
      notation: "compact",
      compactDisplay: "short",
      maximumFractionDigits: clampPlaces(spec.decimalPlaces, 1),
    });
  }

  if (spec.category === "percent") {
    const digits = clampPlaces(spec.decimalPlaces, 1);
    return `${value.toLocaleString("pt-BR", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    })}%`;
  }

  if (spec.category === "scientific") {
    const digits = clampPlaces(spec.decimalPlaces, 2);
    return value.toExponential(digits).replace(".", ",").replace(/e/, "E");
  }

  if (spec.category === "currency" || spec.category === "accounting") {
    const digits = clampPlaces(spec.decimalPlaces, spec.presetId === "currency-brl-4" ? 4 : 2);
    return value.toLocaleString("pt-BR", {
      style: "currency",
      currency: spec.currency ?? "BRL",
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }

  if (spec.category === "number") {
    const hasExplicit = typeof spec.decimalPlaces === "number" && Number.isFinite(spec.decimalPlaces);
    const digits = hasExplicit
      ? clampPlaces(spec.decimalPlaces, 2)
      : spec.presetId === "number-0"
        ? 0
        : 2;
    const thousands =
      typeof spec.useThousandsSeparator === "boolean"
        ? spec.useThousandsSeparator
        : spec.presetId !== "number-2";
    /* number-2 / number-0 padam casas do preset; overrides explícitos (atalhos .0←/.0→) vencem. */
    const padExact =
      hasExplicit || spec.presetId === "number-2" || spec.presetId === "number-0";
    return value.toLocaleString("pt-BR", {
      minimumFractionDigits: padExact ? digits : 0,
      maximumFractionDigits: digits,
      useGrouping: thousands,
    });
  }

  /* general */
  const hasExplicit = typeof spec.decimalPlaces === "number" && Number.isFinite(spec.decimalPlaces);
  if (hasExplicit) {
    const digits = clampPlaces(spec.decimalPlaces, 2);
    return value.toLocaleString("pt-BR", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

function formatDateSpec(
  date: ReturnType<typeof parseDisplayDate> & object,
  spec: DisplayFormatSpec,
  raw: string,
): string {
  if (!date) return raw;
  const preset = spec.presetId;
  const pad2 = (n: number) => String(n).padStart(2, "0");

  if (spec.category === "time" || preset === "time-hhmm") {
    if (spec.pattern?.trim()) {
      return formatCustomPattern(raw, spec.pattern) ?? `${pad2(date.hour)}:${pad2(date.minute)}`;
    }
    return `${pad2(date.hour)}:${pad2(date.minute)}`;
  }

  if (spec.pattern?.trim() && preset !== "date-long" && preset !== "date-auto" && preset !== "date-day-mon") {
    return formatCustomPattern(raw, spec.pattern) ?? raw;
  }

  if (preset === "date-iso") {
    return `${date.year}-${pad2(date.month + 1)}-${pad2(date.day)}`;
  }
  if (preset === "date-year") {
    return String(date.year);
  }
  if (preset === "date-month") {
    return `${monthAbbrevPt(date.month)}. de ${date.year}`;
  }
  if (preset === "date-day-mon") {
    return `${pad2(date.day)} ${monthAbbrevPt(date.month, false)}`;
  }
  if (preset === "date-long") {
    return `${weekdayFullPt(date.year, date.month, date.day)}, ${date.day} de ${monthFullPt(date.month)} de ${date.year}`;
  }
  if (preset === "date-auto") {
    const hasDay = /^\d{4}-\d{2}-\d{2}/.test(raw.trim());
    if (hasDay) return `${pad2(date.day)} ${monthAbbrevPt(date.month)}`;
    return `${monthAbbrevPt(date.month)}/${String(date.year).slice(-2)}`;
  }

  /* date-short default */
  return `${pad2(date.day)}/${pad2(date.month + 1)}/${date.year}`;
}
