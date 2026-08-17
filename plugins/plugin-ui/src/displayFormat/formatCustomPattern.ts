import {
  monthAbbrevPt,
  monthFullPt,
  parseDisplayDate,
  weekdayFullPt,
} from "./parseDisplayDate";
import type { ParsedDisplayDate } from "./types";

const DATE_HINT = /dd|yyyy|aaaa|mmm|HH|hh|ss|yy/i;

export function patternLooksLikeDate(pattern: string): boolean {
  const stripped = stripQuoted(pattern);
  return DATE_HINT.test(stripped);
}

export function formatCustomPattern(value: unknown, pattern: string): string | null {
  const trimmed = pattern.trim();
  if (!trimmed) return null;
  if (patternLooksLikeDate(trimmed)) {
    const date = parseDisplayDate(value);
    if (!date) return null;
    return formatDatePattern(date, trimmed);
  }
  const num = coerceNumber(value);
  if (num == null) return null;
  return formatNumberPattern(num, trimmed);
}

function stripQuoted(pattern: string): string {
  return pattern.replace(/"[^"]*"/g, "");
}

function coerceNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const n = Number(value.trim().replace(/\s/g, "").replace(",", "."));
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function formatDatePattern(date: ParsedDisplayDate, pattern: string): string {
  let out = "";
  let i = 0;
  let seenHour = false;
  const pad2 = (n: number) => String(n).padStart(2, "0");

  while (i < pattern.length) {
    if (pattern[i] === '"') {
      const end = pattern.indexOf('"', i + 1);
      if (end < 0) {
        out += pattern.slice(i);
        break;
      }
      out += pattern.slice(i + 1, end);
      i = end + 1;
      continue;
    }

    const rest = pattern.slice(i);
    if (rest.startsWith("mmmm")) {
      out += monthFullPt(date.month);
      i += 4;
      continue;
    }
    if (rest.startsWith("mmm")) {
      out += monthAbbrevPt(date.month, false);
      i += 3;
      continue;
    }
    if (rest.startsWith("aaaa") || rest.startsWith("yyyy")) {
      out += String(date.year);
      i += 4;
      continue;
    }
    if (rest.startsWith("dddd")) {
      out += weekdayFullPt(date.year, date.month, date.day);
      i += 4;
      continue;
    }
    if (rest.startsWith("HH") || rest.startsWith("hh")) {
      out += pad2(date.hour);
      seenHour = true;
      i += 2;
      continue;
    }
    if (rest.startsWith("ss")) {
      out += pad2(date.second);
      i += 2;
      continue;
    }
    if (rest.startsWith("mm")) {
      out += pad2(seenHour ? date.minute : date.month + 1);
      i += 2;
      continue;
    }
    if (rest.startsWith("dd")) {
      out += pad2(date.day);
      i += 2;
      continue;
    }
    if (rest.startsWith("yy")) {
      out += String(date.year).slice(-2).padStart(2, "0");
      i += 2;
      continue;
    }
    out += pattern[i];
    i += 1;
  }
  return out;
}

/**
 * Máscara numérica pt-BR simplificada: 0 / # / . milhar / , decimal / % / E+00 / literais "…".
 * Percentual NÃO multiplica por 100.
 */
function formatNumberPattern(value: number, pattern: string): string {
  type Part = { kind: "lit" | "mask"; value: string };
  const parts: Part[] = [];
  let i = 0;
  while (i < pattern.length) {
    if (pattern[i] === '"') {
      const end = pattern.indexOf('"', i + 1);
      if (end < 0) {
        parts.push({ kind: "lit", value: pattern.slice(i) });
        break;
      }
      parts.push({ kind: "lit", value: pattern.slice(i + 1, end) });
      i = end + 1;
      continue;
    }
    let j = i;
    while (j < pattern.length && pattern[j] !== '"') j += 1;
    const chunk = pattern.slice(i, j);
    if (/[0#E%,.]/.test(chunk)) parts.push({ kind: "mask", value: chunk });
    else parts.push({ kind: "lit", value: chunk });
    i = j;
  }

  const mask = parts
    .filter((part) => part.kind === "mask")
    .map((part) => part.value)
    .join("");
  const core = formatNumericMaskCore(value, mask);
  let used = false;
  return parts
    .map((part) => {
      if (part.kind === "lit") return part.value;
      if (used) return "";
      used = true;
      return core;
    })
    .join("");
}

function formatNumericMaskCore(value: number, mask: string): string {
  const isPercent = mask.includes("%");
  const sci = /E\+0+/i.test(mask);
  const cleaned = mask.replace(/%/g, "").replace(/E\+0+/gi, "").trim();
  let decimalPlaces = 0;
  const comma = cleaned.lastIndexOf(",");
  if (comma >= 0) {
    decimalPlaces = cleaned.slice(comma + 1).replace(/[^0#]/g, "").length;
  }
  const useThousands = /\d.*\.\d{3}|#\.#|#\.##0/.test(cleaned) || cleaned.includes(".#") || cleaned.includes("#.");

  const abs = Math.abs(value);
  if (sci) {
    const exp = abs === 0 ? 0 : Math.floor(Math.log10(abs));
    const mantissa = abs === 0 ? 0 : abs / 10 ** exp;
    const manStr = mantissa.toLocaleString("pt-BR", {
      minimumFractionDigits: decimalPlaces || 2,
      maximumFractionDigits: decimalPlaces || 2,
    });
    const expStr = `${exp >= 0 ? "+" : "-"}${String(Math.abs(exp)).padStart(2, "0")}`;
    return `${value < 0 ? "-" : ""}${manStr}E${expStr}`;
  }

  const formatted = abs.toLocaleString("pt-BR", {
    minimumFractionDigits: decimalPlaces,
    maximumFractionDigits: decimalPlaces,
    useGrouping: useThousands,
  });
  return `${value < 0 ? "-" : ""}${formatted}${isPercent ? "%" : ""}`;
}
