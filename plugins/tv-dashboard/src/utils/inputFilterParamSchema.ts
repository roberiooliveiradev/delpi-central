import {
  intersectParamSchemaKeys,
  resolveInputParamSchemaField,
  type ComunicadoDataFilters,
  type ComunicadoInputBlock,
} from "@delpi/tv-dashboard-presentation";

import type { DataParamSchema } from "../components/DataParamFields";
import {
  DATE_RANGE_PRESET_OPTIONS,
  DATE_RANGE_PRESET_PARAM,
  PERIOD_DAYS_PARAM,
  findDateRangeKeys,
} from "./dateRangePresets";

export const INPUT_DATE_PRESET_PARAM = DATE_RANGE_PRESET_PARAM;

function mergedSchemaKeys(schemas: DataParamSchema[]): Set<string> {
  const keys = new Set<string>();
  for (const schema of schemas) {
    for (const key of Object.keys(schema)) keys.add(key);
  }
  return keys;
}

/** Interseção de chaves + presets de período quando a rota tem par de datas. */
export function intersectInputParamKeysWithPresets(schemas: DataParamSchema[]): string[] {
  const keys = new Set(intersectParamSchemaKeys(schemas));
  const datePair = findDateRangeKeys(mergedSchemaKeys(schemas));
  if (datePair) {
    keys.add(DATE_RANGE_PRESET_PARAM);
  }
  return [...keys].sort((a, b) => a.localeCompare(b));
}

function datePresetField(): DataParamSchema[string] {
  return {
    type: "string",
    label: "Período",
    enum: DATE_RANGE_PRESET_OPTIONS.map((option) => option.value),
  };
}

/** Schema expandido para o editor de valor do input (inclui presets como na fonte). */
export function buildInputValueEditorSchema(
  schemas: DataParamSchema[],
  paramKey: string,
): DataParamSchema {
  const merged: DataParamSchema = {};
  for (const schema of schemas) {
    Object.assign(merged, schema);
  }
  const datePair = findDateRangeKeys(Object.keys(merged));
  const trimmed = paramKey.trim();

  if (!trimmed) return {};

  if (datePair && (trimmed === DATE_RANGE_PRESET_PARAM || trimmed === PERIOD_DAYS_PARAM)) {
    return {
      [DATE_RANGE_PRESET_PARAM]: datePresetField(),
      [PERIOD_DAYS_PARAM]: { type: "integer", label: "Últimos N dias", optional: true },
      [datePair.startKey]: merged[datePair.startKey] ?? { type: "string", format: "date", label: "Início" },
      [datePair.endKey]: merged[datePair.endKey] ?? { type: "string", format: "date", label: "Fim" },
    };
  }

  if (datePair && (trimmed === datePair.startKey || trimmed === datePair.endKey)) {
    return {
      [DATE_RANGE_PRESET_PARAM]: datePresetField(),
      [PERIOD_DAYS_PARAM]: { type: "integer", label: "Últimos N dias", optional: true },
      [datePair.startKey]: merged[datePair.startKey]!,
      [datePair.endKey]: merged[datePair.endKey]!,
    };
  }

  const field = resolveInputParamSchemaField(trimmed, schemas);
  return field ? { [trimmed]: field } : {};
}

export function buildInputEditorValues(
  block: ComunicadoInputBlock,
  slideFilters: ComunicadoDataFilters,
  schema: DataParamSchema,
): Record<string, string | number | boolean | null | undefined> {
  const values: Record<string, string | number | boolean | null | undefined> = {};
  const scope = block.input.targetScope === "sources" ? "sources" : "slide";
  const paramKey = String(block.input.paramKey || "").trim();

  for (const key of Object.keys(schema)) {
    if (scope === "slide" && key in slideFilters) {
      values[key] = slideFilters[key];
      continue;
    }
    if (key === paramKey) {
      values[key] = block.input.defaultValue;
    }
  }

  if (scope === "slide" && paramKey === DATE_RANGE_PRESET_PARAM && values[DATE_RANGE_PRESET_PARAM] == null) {
    values[DATE_RANGE_PRESET_PARAM] =
      slideFilters[DATE_RANGE_PRESET_PARAM] ?? block.input.defaultValue ?? "this_month";
  }

  return values;
}

export function parseInputFilterValue(
  key: string,
  raw: string,
  fieldType?: string,
): string | number | boolean | null {
  if (raw === "" || raw === null || raw === undefined) return null;
  if (fieldType === "integer" || fieldType === "number") return Number(raw);
  if (fieldType === "boolean") return raw === "true";
  return String(raw).trim();
}
