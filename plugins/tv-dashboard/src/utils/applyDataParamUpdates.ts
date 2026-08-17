import { EXCLUDE_WEEKENDS_PARAM } from "@delpi/tv-dashboard-presentation";

import type { DataParamSchema } from "../components/DataParamFields";
import { findDateRangeKeys, isDateRangePairKey } from "./dateRangePresets";

const MIN_SANE_YEAR = 1990;
const MAX_SANE_YEAR = 2100;

function isSaneIsoDate(raw: string): boolean {
  const text = raw.trim();
  if (!/^\d{4}-\d{2}-\d{2}/.test(text)) return false;
  const year = Number(text.slice(0, 4));
  if (!Number.isFinite(year) || year < MIN_SANE_YEAR || year > MAX_SANE_YEAR) return false;
  const parsed = new Date(`${text.slice(0, 10)}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime());
}

/** Converte raw de UI (string) para valor tipado do schema. */
export function parseDataParamRaw(
  key: string,
  raw: string,
  schema: DataParamSchema | undefined,
): string | number | boolean | undefined {
  const fieldType = schema?.[key]?.type;
  if (!raw.trim()) return undefined;
  const datePair = findDateRangeKeys(Object.keys(schema ?? {}));
  const looksLikeDate =
    fieldType === "string" &&
    (isDateRangePairKey(key, datePair) ||
      String((schema?.[key] as { format?: string } | undefined)?.format || "").toLowerCase() ===
        "date");
  if (looksLikeDate || /^\d{4}-\d{2}-\d{2}/.test(raw.trim())) {
    if (!isSaneIsoDate(raw)) return undefined;
    return raw.trim().slice(0, 10);
  }
  if (fieldType === "integer" || fieldType === "number") return Number(raw);
  if (fieldType === "boolean" || key === EXCLUDE_WEEKENDS_PARAM) return raw === "true";
  return raw.trim();
}

/**
 * Aplica várias chaves de parâmetro de uma vez (evita race com binding stale
 * quando Período + competence / datas mudam juntos).
 */
export function applyDataParamRawUpdates(
  current: Record<string, string | number | boolean | null | undefined> | undefined,
  updates: Record<string, string>,
  schema: DataParamSchema | undefined,
): Record<string, string | number | boolean> {
  const next: Record<string, string | number | boolean> = { ...(current ?? {}) };
  for (const [key, raw] of Object.entries(updates)) {
    const parsed = parseDataParamRaw(key, raw, schema);
    if (parsed === undefined) delete next[key];
    else next[key] = parsed;
  }
  return next;
}
