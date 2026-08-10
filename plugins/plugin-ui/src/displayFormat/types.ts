/** Formatação de exibição canônica (Excel-like) — motor único do kit. */

export type DisplayFormatCategory =
  | "general"
  | "number"
  | "currency"
  | "accounting"
  | "date"
  | "time"
  | "percent"
  | "scientific"
  | "text"
  | "custom";

export type DisplayFormatLocale = "pt-BR";

export type DisplayFormatSpec = {
  category: DisplayFormatCategory;
  presetId?: string;
  decimalPlaces?: number | null;
  useThousandsSeparator?: boolean;
  currency?: "BRL";
  pattern?: string;
  locale?: DisplayFormatLocale;
};

export type DisplayFormatTarget =
  | "chartValue"
  | "chartCategory"
  | "table"
  | "kpi"
  | "canvasCell";

export type ParsedDisplayDate = {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  second: number;
  /** true = só calendário ISO (UTC parts, sem timezone). */
  dateOnly: boolean;
};

export const EMPTY_DISPLAY = "—";

export function isDisplayFormatSpec(value: unknown): value is DisplayFormatSpec {
  if (!value || typeof value !== "object") return false;
  const category = (value as DisplayFormatSpec).category;
  return (
    category === "general" ||
    category === "number" ||
    category === "currency" ||
    category === "accounting" ||
    category === "date" ||
    category === "time" ||
    category === "percent" ||
    category === "scientific" ||
    category === "text" ||
    category === "custom"
  );
}
