import type { DisplayFormatCategory, DisplayFormatSpec } from "./types";

export type DisplayFormatPreset = {
  id: string;
  category: DisplayFormatCategory;
  label: string;
  description?: string;
  spec: DisplayFormatSpec;
};

export type DisplayFormatCategoryMeta = {
  category: DisplayFormatCategory;
  label: string;
  description: string;
  /** Preset aplicado ao escolher a categoria no menu. */
  defaultPresetId: string;
};

export const DISPLAY_FORMAT_CATEGORIES: readonly DisplayFormatCategoryMeta[] = [
  { category: "general", label: "Geral", description: "Sem formato específico", defaultPresetId: "general" },
  { category: "number", label: "Número", description: "Separador decimal pt-BR", defaultPresetId: "number-2" },
  { category: "currency", label: "Moeda", description: "Real brasileiro (R$)", defaultPresetId: "currency-brl" },
  { category: "accounting", label: "Contábil", description: "Igual à moeda nesta versão", defaultPresetId: "accounting" },
  { category: "date", label: "Data abreviada", description: "Dia, mês e ano", defaultPresetId: "date-short" },
  { category: "time", label: "Hora", description: "Hora e minuto", defaultPresetId: "time-hhmm" },
  { category: "percent", label: "Porcentagem", description: "Valor já em pontos percentuais", defaultPresetId: "percent" },
  { category: "scientific", label: "Científico", description: "Notação exponencial", defaultPresetId: "scientific" },
  { category: "text", label: "Texto", description: "Exibe o valor como está", defaultPresetId: "text" },
  { category: "custom", label: "Personalizado", description: "Máscara livre", defaultPresetId: "custom" },
] as const;

export const DISPLAY_FORMAT_PRESETS: readonly DisplayFormatPreset[] = [
  { id: "general", category: "general", label: "Geral", spec: { category: "general" } },
  {
    id: "number-0",
    category: "number",
    label: "0",
    spec: { category: "number", decimalPlaces: 0, useThousandsSeparator: true },
  },
  {
    id: "number-2",
    category: "number",
    label: "0,00",
    spec: { category: "number", decimalPlaces: 2, useThousandsSeparator: false },
  },
  {
    id: "number-thousands",
    category: "number",
    label: "#.##0,00",
    spec: { category: "number", decimalPlaces: 2, useThousandsSeparator: true },
  },
  {
    id: "number-compact",
    category: "number",
    label: "Compacto",
    spec: { category: "number", presetId: "number-compact", decimalPlaces: 1 },
  },
  {
    id: "currency-brl",
    category: "currency",
    label: "R$ #.##0,00",
    spec: { category: "currency", currency: "BRL", decimalPlaces: 2 },
  },
  {
    id: "currency-brl-4",
    category: "currency",
    label: "Moeda (R$ · 4 casas)",
    spec: { category: "currency", currency: "BRL", decimalPlaces: 4 },
  },
  {
    id: "accounting",
    category: "accounting",
    label: "Contábil (R$)",
    spec: { category: "accounting", currency: "BRL", decimalPlaces: 2 },
  },
  {
    id: "date-short",
    category: "date",
    label: "03/08/2026",
    spec: { category: "date", presetId: "date-short", pattern: "dd/mm/yyyy" },
  },
  {
    id: "date-long",
    category: "date",
    label: "Data completa",
    spec: { category: "date", presetId: "date-long" },
  },
  {
    id: "date-iso",
    category: "date",
    label: "2026-08-03",
    spec: { category: "date", presetId: "date-iso", pattern: "yyyy-mm-dd" },
  },
  {
    id: "date-day-mon",
    category: "date",
    label: "03 ago",
    spec: { category: "date", presetId: "date-day-mon" },
  },
  {
    id: "date-month",
    category: "date",
    label: "ago. de 2026",
    spec: { category: "date", presetId: "date-month" },
  },
  {
    id: "date-year",
    category: "date",
    label: "2026",
    spec: { category: "date", presetId: "date-year" },
  },
  {
    id: "date-auto",
    category: "date",
    label: "Data (auto)",
    spec: { category: "date", presetId: "date-auto" },
  },
  {
    id: "time-hhmm",
    category: "time",
    label: "HH:mm",
    spec: { category: "time", pattern: "HH:mm" },
  },
  {
    id: "percent",
    category: "percent",
    label: "0,0%",
    spec: { category: "percent", decimalPlaces: 1 },
  },
  {
    id: "scientific",
    category: "scientific",
    label: "0,00E+00",
    spec: { category: "scientific", decimalPlaces: 2 },
  },
  { id: "text", category: "text", label: "Texto", spec: { category: "text" } },
  { id: "custom", category: "custom", label: "Personalizado", spec: { category: "custom", pattern: "" } },
];

const PRESET_BY_ID = new Map(DISPLAY_FORMAT_PRESETS.map((item) => [item.id, item]));

export function getDisplayFormatPreset(id: string | null | undefined): DisplayFormatPreset | null {
  if (!id) return null;
  return PRESET_BY_ID.get(id) ?? null;
}

export function presetsForCategory(category: DisplayFormatCategory): DisplayFormatPreset[] {
  return DISPLAY_FORMAT_PRESETS.filter((item) => item.category === category && item.id !== "custom");
}

export function specFromPresetId(id: string): DisplayFormatSpec {
  const preset = getDisplayFormatPreset(id);
  if (!preset) return { category: "general" };
  return { ...preset.spec, presetId: preset.id };
}

export function menuCategoryItems(): Array<DisplayFormatCategoryMeta & { menuOnly?: boolean }> {
  return DISPLAY_FORMAT_CATEGORIES.filter((item) => item.category !== "custom");
}

export type DisplayFormatMenuItem = {
  id: string;
  category: DisplayFormatCategory;
  presetId: string;
  label: string;
  description?: string;
};

/** Itens do dropdown (Data abreviada + Data completa; compacto/4 casas só no diálogo). */
export function displayFormatMenuItems(): DisplayFormatMenuItem[] {
  return [
    { id: "general", category: "general", presetId: "general", label: "Geral", description: "Sem formato específico" },
    { id: "number", category: "number", presetId: "number-2", label: "Número" },
    { id: "currency", category: "currency", presetId: "currency-brl", label: "Moeda" },
    { id: "accounting", category: "accounting", presetId: "accounting", label: "Contábil" },
    { id: "date-short", category: "date", presetId: "date-short", label: "Data abreviada" },
    { id: "date-long", category: "date", presetId: "date-long", label: "Data completa" },
    { id: "time", category: "time", presetId: "time-hhmm", label: "Hora" },
    { id: "percent", category: "percent", presetId: "percent", label: "Porcentagem" },
    { id: "scientific", category: "scientific", presetId: "scientific", label: "Científico" },
    { id: "text", category: "text", presetId: "text", label: "Texto" },
  ];
}

export function isNumericDisplayCategory(category: DisplayFormatCategory): boolean {
  return (
    category === "general" ||
    category === "number" ||
    category === "currency" ||
    category === "accounting" ||
    category === "percent" ||
    category === "scientific"
  );
}

export function displayFormatTriggerLabel(spec: DisplayFormatSpec | null | undefined): string {
  if (!spec?.category) return "Geral";
  if (spec.category === "date" && spec.presetId === "date-long") return "Data completa";
  if (spec.category === "date" && spec.presetId === "date-iso") return "ISO";
  if (spec.category === "custom") return "Personalizado";
  return DISPLAY_FORMAT_CATEGORIES.find((item) => item.category === spec.category)?.label ?? "Geral";
}
