/** Normalização fiscal de apresentação (API continua como fonte final). */

export type NormalizedDocumentPreview = {
  digits: string;
  display: string;
  matchKey: string;
  valid: boolean;
  error: string | null;
};

export function normalizeDocumentInput(raw: string): NormalizedDocumentPreview {
  const digits = String(raw ?? "").replace(/\D/g, "");
  if (!digits) {
    return {
      digits: "",
      display: "",
      matchKey: "",
      valid: false,
      error: "Informe o número da nota (somente dígitos).",
    };
  }
  if (digits.length > 9) {
    return {
      digits: digits.slice(0, 9),
      display: digits.slice(0, 9),
      matchKey: digits.slice(0, 9).padStart(9, "0"),
      valid: false,
      error: "Número da nota deve ter no máximo 9 dígitos.",
    };
  }
  const display = digits.padStart(9, "0");
  const matchKey = digits.padStart(9, "0");
  return {
    digits,
    display,
    matchKey,
    valid: true,
    error: null,
  };
}

export function sanitizeDocumentTyping(raw: string): string {
  return String(raw ?? "").replace(/\D/g, "").slice(0, 9);
}

/** Digitação de valor monetário BR: dígitos + uma vírgula/ponto decimal. */
export function sanitizeAmountTyping(raw: string): string {
  const cleaned = String(raw ?? "").replace(/[^\d.,]/g, "");
  if (!cleaned) return "";

  const lastComma = cleaned.lastIndexOf(",");
  const lastDot = cleaned.lastIndexOf(".");
  const sepIndex = Math.max(lastComma, lastDot);

  if (sepIndex < 0) {
    return cleaned.replace(/[.,]/g, "");
  }

  const intPart = cleaned.slice(0, sepIndex).replace(/[.,]/g, "");
  const fracPart = cleaned
    .slice(sepIndex + 1)
    .replace(/[.,]/g, "")
    .slice(0, 2);
  const sep = cleaned[sepIndex] === "," ? "," : ".";
  return fracPart.length > 0 || cleaned.endsWith(",") || cleaned.endsWith(".")
    ? `${intPart}${sep}${fracPart}`
    : intPart;
}

/** Converte valor digitado (vírgula ou ponto) para número; null se inválido. */
export function parseAmountInput(raw: string): number | null {
  const text = String(raw ?? "").trim();
  if (!text) return null;
  const normalized = text.includes(",")
    ? text.replace(/\./g, "").replace(",", ".")
    : text;
  const value = Number(normalized);
  if (!Number.isFinite(value) || value < 0) return null;
  return Math.round(value * 100) / 100;
}

export function normalizeSeriesInput(raw: string): string {
  return String(raw ?? "").trim().toUpperCase().slice(0, 3);
}

export const BRANCH_OPTIONS = [
  { value: "01", label: "01 — Santa Catarina" },
  { value: "02", label: "02 — Espírito Santo" },
] as const;
