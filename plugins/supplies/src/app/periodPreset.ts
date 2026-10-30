/**
 * Supplies period presets — shared temporal contract from @delpi/plugin-ui.
 * Field names stay `from`/`to` for existing Overview/PR/PO consumers.
 * KPI chip (MTD/YTD) stays portal-local.
 */

import {
  PERIOD_PRESET_IDS,
  PERIOD_PRESET_OPTIONS,
  detectPeriodPreset,
  parsePeriodPresetId as parseSharedPeriodPresetId,
  resolvePeriodPreset as resolveSharedPeriodPreset,
  todayIsoInTimeZone,
  type PeriodPresetId,
} from "@delpi/plugin-ui/index";

export { PERIOD_PRESET_IDS, PERIOD_PRESET_OPTIONS, todayIsoInTimeZone };
export type { PeriodPresetId };

export type PeriodPresetRange = {
  from: string;
  to: string;
};

export function resolvePeriodPreset(
  preset: PeriodPresetId,
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): PeriodPresetRange | null {
  const range = resolveSharedPeriodPreset(preset, now, timeZone);
  if (!range) return null;
  return { from: range.dateStart, to: range.dateEnd };
}

/**
 * Returns which preset id matches the inclusive [from, to] range, or `"custom"`.
 * Used by PR/PO filters on F5 (dates in URL; no dedicated period query param).
 */
export function matchPeriodPreset(
  from: string,
  to: string,
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): PeriodPresetId {
  const fromTrim = (from || "").trim();
  const toTrim = (to || "").trim();
  if (!fromTrim || !toTrim) return "custom";
  return detectPeriodPreset(fromTrim, toTrim, now, timeZone);
}

export function parsePeriodPresetId(raw: string | null | undefined): PeriodPresetId | null {
  if (!raw) return null;
  if ((PERIOD_PRESET_IDS as readonly string[]).includes(raw)) {
    return raw as PeriodPresetId;
  }
  return parseSharedPeriodPresetId(raw);
}

// ——— Presets rápidos estendidos (filtros operacionais) ———
// Granularidade extra pedida pela operação (GLPI #1353): ontem e janelas
// móveis de 7/15/30 dias. Compõe o contrato shared sem alterar
// PERIOD_PRESET_OPTIONS — outras páginas/plugins não são afetadas.

export const SUPPLIES_QUICK_PERIOD_IDS = [
  "today",
  "yesterday",
  "last_7_days",
  "last_15_days",
  "last_30_days",
  "this_month",
  "last_month",
  "custom",
] as const;

export type SuppliesQuickPeriodId = (typeof SUPPLIES_QUICK_PERIOD_IDS)[number];

export const SUPPLIES_QUICK_PERIOD_OPTIONS: {
  value: SuppliesQuickPeriodId;
  label: string;
}[] = [
  { value: "today", label: "Hoje" },
  { value: "yesterday", label: "Ontem" },
  { value: "last_7_days", label: "Últimos 7 dias" },
  { value: "last_15_days", label: "Últimos 15 dias" },
  { value: "last_30_days", label: "Últimos 30 dias" },
  { value: "this_month", label: "Este mês" },
  { value: "last_month", label: "Mês passado" },
  { value: "custom", label: "Personalizado" },
];

const PAD2 = (value: number) => String(value).padStart(2, "0");

function shiftIsoDays(iso: string, deltaDays: number): string {
  const dt = new Date(`${iso}T00:00:00Z`);
  dt.setUTCDate(dt.getUTCDate() + deltaDays);
  return `${dt.getUTCFullYear()}-${PAD2(dt.getUTCMonth() + 1)}-${PAD2(
    dt.getUTCDate(),
  )}`;
}

/**
 * Resolve `from`/`to` para o preset operacional, ou null para `custom`.
 * Presets do contrato shared (`today`, `this_month`, `last_month`) delegam;
 * os estendidos são janelas móveis terminando em hoje.
 */
export function resolveSuppliesQuickPeriod(
  preset: SuppliesQuickPeriodId,
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): PeriodPresetRange | null {
  if (preset === "custom") return null;
  if (preset === "today" || preset === "this_month" || preset === "last_month") {
    return resolvePeriodPreset(preset, now, timeZone);
  }
  const today = todayIsoInTimeZone(now, timeZone);
  if (preset === "yesterday") {
    const yesterday = shiftIsoDays(today, -1);
    return { from: yesterday, to: yesterday };
  }
  const span =
    preset === "last_7_days" ? 7 : preset === "last_15_days" ? 15 : 30;
  return { from: shiftIsoDays(today, -(span - 1)), to: today };
}

/**
 * Detecta qual preset corresponde ao intervalo [from, to] corrente,
 * ou `"custom"` quando as datas foram editadas manualmente.
 */
export function matchSuppliesQuickPeriod(
  from: string,
  to: string,
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): SuppliesQuickPeriodId {
  const fromTrim = (from || "").trim();
  const toTrim = (to || "").trim();
  if (!fromTrim || !toTrim) return "custom";
  for (const id of SUPPLIES_QUICK_PERIOD_IDS) {
    if (id === "custom") continue;
    const range = resolveSuppliesQuickPeriod(id, now, timeZone);
    if (range && range.from === fromTrim && range.to === toTrim) return id;
  }
  return "custom";
}

/** MTD/YTD chip for DashboardKpiCard — mirrors Commercial resolvePeriodKindChip. */
export type PeriodKindChip = "MTD" | "YTD";

export function resolvePeriodKindChip(
  preset: PeriodPresetId | null | undefined,
): PeriodKindChip | null {
  if (preset === "today" || preset === "this_week" || preset === "this_month" || preset === "last_month") {
    return "MTD";
  }
  if (preset === "this_year" || preset === "last_12_months") return "YTD";
  return null;
}
