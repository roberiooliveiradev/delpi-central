import { formatLmpApiDateDisplay } from "./dates";

/** Converte input YYYY-MM-DD para YYYYMMDD (API ainda aceita vários formatos). */
export function inputDateToLmpApi(value?: string): string | undefined {
  if (!value) return undefined;
  const normalized = value.trim();
  if (/^\d{8}$/.test(normalized)) return normalized;
  if (/^\d{4}-\d{2}-\d{2}$/.test(normalized)) {
    return normalized.replaceAll("-", "");
  }
  return normalized;
}

export function formatLmpDisplayDate(value?: string | null): string {
  return formatLmpApiDateDisplay(value);
}

export function formatListingKind(kind?: string | null): string {
  if (kind === "AMOSTRA") return "Amostra";
  if (kind === "OUTRO") return "Outro";
  if (kind === "LMP") return "LMP";
  return kind ?? "—";
}
