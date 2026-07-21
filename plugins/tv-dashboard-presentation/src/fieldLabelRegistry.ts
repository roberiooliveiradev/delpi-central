/**
 * Registro de rótulos de display por fonte — chave da API estável; só muda o texto na TV.
 *
 * Cascata:
 *   1. label na projeção do visual (só se for override real — não igual à chave)
 *   2. data_source.fieldLabels[field] (lookup case-insensitive)
 *   3. catálogo / resolved atual
 *   4. field (chave bruta)
 */

import type {
  ComunicadoDataResolved,
  ComunicadoDataTableColumn,
} from "./comunicadoTypes";

export type FieldLabelsMap = Record<string, string>;

/** Rótulo de projeção “assado” com a chave — não conta como override do usuário. */
export function isAutoBakedFieldLabel(
  label: string | null | undefined,
  field: string,
): boolean {
  const text = String(label ?? "");
  const key = String(field ?? "").trim();
  if (!key) return !text.trim();
  return text.trim().toLowerCase() === key.toLowerCase();
}

/** Lookup case-insensitive; preserva espaços no valor. */
export function lookupFieldLabel(
  labels: FieldLabelsMap | null | undefined,
  field: string,
): string | undefined {
  if (!labels) return undefined;
  const key = String(field ?? "").trim();
  if (!key) return undefined;
  if (Object.prototype.hasOwnProperty.call(labels, key)) {
    const direct = labels[key];
    return typeof direct === "string" ? direct : undefined;
  }
  const lower = key.toLowerCase();
  for (const [entryKey, value] of Object.entries(labels)) {
    if (entryKey.toLowerCase() === lower && typeof value === "string") {
      return value;
    }
  }
  return undefined;
}

/**
 * Normaliza o mapa: chave trimada; valor preserva espaços finais (só descarta se vazio).
 * Em conflito case-insensitive, a última entrada vence (chave canônica = última vista).
 */
export function normalizeFieldLabels(raw: unknown): FieldLabelsMap | undefined {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return undefined;
  const out: FieldLabelsMap = {};
  const canonicalByLower = new Map<string, string>();
  for (const [key, value] of Object.entries(raw as Record<string, unknown>)) {
    const field = String(key ?? "").trim();
    if (!field) continue;
    if (typeof value !== "string") continue;
    if (!value.trim()) continue;
    const lower = field.toLowerCase();
    const previous = canonicalByLower.get(lower);
    if (previous && previous !== field) {
      delete out[previous];
    }
    canonicalByLower.set(lower, field);
    out[field] = value;
  }
  return Object.keys(out).length > 0 ? out : undefined;
}

export type ResolveFieldDisplayLabelInput = {
  field: string;
  projectionLabel?: string | null;
  sourceFieldLabels?: FieldLabelsMap | null;
  catalogLabel?: string | null;
  resolvedLabel?: string | null;
};

export function resolveFieldDisplayLabel(input: ResolveFieldDisplayLabelInput): string {
  const field = String(input.field ?? "").trim();
  if (!field) return "";
  const projection = input.projectionLabel;
  if (
    typeof projection === "string" &&
    projection.trim() &&
    !isAutoBakedFieldLabel(projection, field)
  ) {
    return projection;
  }
  const fromSource = lookupFieldLabel(input.sourceFieldLabels, field);
  if (fromSource?.trim()) return fromSource;
  const catalog = input.catalogLabel;
  if (typeof catalog === "string" && catalog.trim()) return catalog;
  const resolved = input.resolvedLabel;
  if (typeof resolved === "string" && resolved.trim()) return resolved;
  return field;
}

/**
 * Reaplica rótulos do registro da fonte em table.columns e kpiMetrics.
 * Não altera keys das rows nem valores — só display.
 */
export function applyFieldLabelsToResolved(
  resolved: ComunicadoDataResolved | undefined,
  fieldLabels: FieldLabelsMap | null | undefined,
): ComunicadoDataResolved | undefined {
  if (!resolved) return resolved;
  const labels = normalizeFieldLabels(fieldLabels);
  if (!labels) return resolved;

  let next: ComunicadoDataResolved = resolved;
  let changed = false;

  if (resolved.table?.columns?.length) {
    const columns: ComunicadoDataTableColumn[] = resolved.table.columns.map((col) => {
      const override = lookupFieldLabel(labels, col.key);
      if (!override?.trim() || override === col.label) return col;
      changed = true;
      return { ...col, label: override };
    });
    if (changed) {
      next = {
        ...next,
        table: { ...resolved.table, columns },
      };
    }
  }

  if (resolved.kpiMetrics?.length) {
    let metricsChanged = false;
    const kpiMetrics = resolved.kpiMetrics.map((metric) => {
      const override = lookupFieldLabel(labels, metric.field);
      if (!override?.trim() || override === metric.label) return metric;
      metricsChanged = true;
      return { ...metric, label: override };
    });
    if (metricsChanged) {
      changed = true;
      const primary = kpiMetrics[0];
      const primaryOverride =
        primary && lookupFieldLabel(labels, primary.field);
      next = {
        ...next,
        kpiMetrics,
        kpi: next.kpi
          ? {
              ...next.kpi,
              label: primaryOverride?.trim() ? primaryOverride : next.kpi.label,
            }
          : next.kpi,
      };
    }
  }

  if (resolved.chart?.series?.length) {
    let seriesChanged = false;
    const series = resolved.chart.series.map((entry) => {
      const field = entry.field?.trim();
      if (!field) return entry;
      const override = lookupFieldLabel(labels, field);
      if (!override?.trim() || override === entry.name) return entry;
      seriesChanged = true;
      return { ...entry, name: override };
    });
    if (seriesChanged) {
      changed = true;
      next = {
        ...next,
        chart: { ...resolved.chart, series },
      };
    }
  }

  return changed ? next : resolved;
}

export type EditableFieldOption = {
  field: string;
  /** Rótulo efetivo atual (já resolvido). */
  label: string;
  /** Default sem o registro da fonte (catálogo/resolved). */
  defaultLabel: string;
};

/**
 * Campos editáveis: colunas da tabela + métricas KPI + keys do catálogo.
 * Dedupa case-insensitive preferindo a chave do resolved (API) sobre o catálogo.
 */
export function suggestEditableFields(
  resolved: ComunicadoDataResolved | undefined,
  catalogFields?: Array<{ field: string; label: string }>,
  sourceFieldLabels?: FieldLabelsMap | null,
): EditableFieldOption[] {
  const defaults = new Map<string, string>();
  const canonicalByLower = new Map<string, string>();

  const upsert = (fieldRaw: string, defaultLabel: string) => {
    const field = fieldRaw.trim();
    if (!field) return;
    const lower = field.toLowerCase();
    const existingKey = canonicalByLower.get(lower);
    if (existingKey && existingKey !== field) {
      // Preferir chave já canônica (resolved) — não sobrescrever com catálogo divergente.
      if (!defaults.has(existingKey)) {
        defaults.set(existingKey, defaultLabel.trim() || existingKey);
      }
      return;
    }
    canonicalByLower.set(lower, field);
    if (!defaults.has(field)) {
      defaults.set(field, defaultLabel.trim() || field);
    }
  };

  for (const col of resolved?.table?.columns ?? []) {
    if (col.key) upsert(col.key, col.label || col.key);
  }
  for (const metric of resolved?.kpiMetrics ?? []) {
    if (metric.field) upsert(metric.field, metric.label || metric.field);
  }
  const firstRow = resolved?.table?.rows?.[0];
  if (firstRow && typeof firstRow === "object") {
    for (const key of Object.keys(firstRow)) {
      upsert(key, key);
    }
  }
  for (const item of catalogFields ?? []) {
    upsert(item.field, item.label.trim() || item.field);
  }

  return [...defaults.entries()].map(([field, defaultLabel]) => ({
    field,
    defaultLabel,
    label: resolveFieldDisplayLabel({
      field,
      sourceFieldLabels,
      catalogLabel: defaultLabel,
      resolvedLabel: defaultLabel,
    }),
  }));
}

/** Patch do mapa: só whitespace remove a entrada; espaços finais são preservados. */
export function patchFieldLabels(
  current: FieldLabelsMap | null | undefined,
  field: string,
  label: string | null | undefined,
): FieldLabelsMap | undefined {
  const key = field.trim();
  if (!key) return normalizeFieldLabels(current);
  const next: FieldLabelsMap = { ...(normalizeFieldLabels(current) ?? {}) };
  // Remover entradas case-insensitive duplicadas antes de gravar.
  const lower = key.toLowerCase();
  for (const existing of Object.keys(next)) {
    if (existing.toLowerCase() === lower && existing !== key) {
      delete next[existing];
    }
  }
  if (label == null || !label.trim()) {
    delete next[key];
  } else {
    next[key] = label;
  }
  return Object.keys(next).length > 0 ? next : undefined;
}
