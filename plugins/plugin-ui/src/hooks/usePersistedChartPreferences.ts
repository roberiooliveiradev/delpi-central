import { useCallback, useEffect, useMemo, useState } from "react";

/** View types supported by MultiTypeSeriesChart / ChartViewShell. */
export type PersistedChartType =
  | "column"
  | "line"
  | "area"
  | "pie"
  | "bar"
  | "horizontal_bar"
  | "stacked_bar";

export type SeriesTrendStyle = {
  color?: string;
  dash?: "solid" | "dashed";
  width?: number;
};

export type PersistedChartPreferences = {
  chartType?: PersistedChartType;
  comparePriorYear?: boolean;
  /** YoY depth for billing series (0–3). */
  compareYears?: number;
  showTrend?: boolean;
  /** Incomplete bucket handling for OLS trend. Default exclude when unset. */
  incompleteBucketMode?: "exclude" | "weightByFraction";
  /**
   * User overrides for series fills keyed by `dataKey`.
   * Empty / omitted → chart uses the host default fills.
   */
  seriesFills?: Record<string, string>;
  /** dataKey → true hides the series without dropping source rows. */
  hiddenSeries?: Record<string, boolean>;
  /**
   * Per-series OLS trend ON/OFF keyed by `dataKey`.
   * Absent key = OFF for inspector hosts (`applySeriesViewPreferences`).
   * `showTrend` remains for historical COLOR_ONLY / non-inspector charts.
   */
  seriesTrend?: Record<string, boolean>;
  /** Optional trend stroke/dash/width overrides keyed by `dataKey`. */
  seriesTrendStyles?: Record<string, SeriesTrendStyle>;
};

export type UsePersistedChartPreferencesOptions = {
  storageKey: string;
  defaults: PersistedChartPreferences;
  /** Allowed chart types — invalid stored values fall back to defaults.chartType. */
  allowedChartTypes?: readonly PersistedChartType[];
  /** When false, does not read/write localStorage (default true). */
  enabled?: boolean;
};

const CHART_TYPES: readonly PersistedChartType[] = [
  "column",
  "line",
  "area",
  "pie",
  "bar",
  "horizontal_bar",
  "stacked_bar",
] as const;

function isChartType(value: unknown): value is PersistedChartType {
  return typeof value === "string" && (CHART_TYPES as readonly string[]).includes(value);
}

/** Keep only non-empty string dataKey → CSS color / var fills. */
export function sanitizeSeriesFills(
  value: unknown,
): Record<string, string> | undefined {
  if (value == null) return undefined;
  if (typeof value !== "object" || Array.isArray(value)) return undefined;
  const out: Record<string, string> = {};
  for (const [rawKey, rawFill] of Object.entries(value as Record<string, unknown>)) {
    const key = typeof rawKey === "string" ? rawKey.trim() : "";
    if (!key) continue;
    if (typeof rawFill !== "string") continue;
    const fill = rawFill.trim();
    if (!fill) continue;
    out[key] = fill;
  }
  return Object.keys(out).length > 0 ? out : undefined;
}

export function sanitizeBooleanOverrideMap(
  value: unknown,
): Record<string, boolean> | undefined {
  if (value == null) return undefined;
  if (typeof value !== "object" || Array.isArray(value)) return undefined;
  const out: Record<string, boolean> = {};
  for (const [rawKey, rawValue] of Object.entries(value as Record<string, unknown>)) {
    const key = typeof rawKey === "string" ? rawKey.trim() : "";
    if (!key || typeof rawValue !== "boolean") continue;
    out[key] = rawValue;
  }
  return Object.keys(out).length > 0 ? out : undefined;
}

export function sanitizeHiddenSeries(
  value: unknown,
): Record<string, boolean> | undefined {
  const mapped = sanitizeBooleanOverrideMap(value);
  if (!mapped) return undefined;
  const out: Record<string, boolean> = {};
  for (const [key, hidden] of Object.entries(mapped)) {
    if (hidden) out[key] = true;
  }
  return Object.keys(out).length > 0 ? out : undefined;
}

export function sanitizeSeriesTrendStyles(
  value: unknown,
): Record<string, SeriesTrendStyle> | undefined {
  if (value == null) return undefined;
  if (typeof value !== "object" || Array.isArray(value)) return undefined;
  const out: Record<string, SeriesTrendStyle> = {};
  for (const [rawKey, rawStyle] of Object.entries(value as Record<string, unknown>)) {
    const key = typeof rawKey === "string" ? rawKey.trim() : "";
    if (!key || !rawStyle || typeof rawStyle !== "object" || Array.isArray(rawStyle)) {
      continue;
    }
    const style = rawStyle as Record<string, unknown>;
    const next: SeriesTrendStyle = {};
    if (typeof style.color === "string" && style.color.trim()) {
      next.color = style.color.trim();
    }
    if (style.dash === "solid" || style.dash === "dashed") {
      next.dash = style.dash;
    }
    if (typeof style.width === "number" && Number.isFinite(style.width)) {
      next.width = Math.min(8, Math.max(1, Math.round(style.width)));
    }
    if (next.color || next.dash || next.width != null) {
      out[key] = next;
    }
  }
  return Object.keys(out).length > 0 ? out : undefined;
}

function readStored(storageKey: string): PersistedChartPreferences | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return null;
    return parsed as PersistedChartPreferences;
  } catch {
    return null;
  }
}

function mergePreferences(
  defaults: PersistedChartPreferences,
  stored: PersistedChartPreferences | null,
  allowedChartTypes?: readonly PersistedChartType[],
): PersistedChartPreferences {
  const merged: PersistedChartPreferences = { ...defaults, ...(stored ?? {}) };
  if (merged.chartType != null && !isChartType(merged.chartType)) {
    merged.chartType = defaults.chartType;
  }
  if (
    allowedChartTypes &&
    merged.chartType != null &&
    !allowedChartTypes.includes(merged.chartType)
  ) {
    merged.chartType = defaults.chartType;
  }
  if (merged.compareYears != null) {
    const n = Number(merged.compareYears);
    merged.compareYears = Number.isFinite(n) ? Math.max(0, Math.min(3, Math.trunc(n))) : defaults.compareYears;
  }
  if (
    merged.incompleteBucketMode != null &&
    merged.incompleteBucketMode !== "exclude" &&
    merged.incompleteBucketMode !== "weightByFraction"
  ) {
    merged.incompleteBucketMode = defaults.incompleteBucketMode ?? "exclude";
  }
  if (stored != null && "seriesFills" in stored) {
    merged.seriesFills = sanitizeSeriesFills(stored.seriesFills);
  } else {
    merged.seriesFills = sanitizeSeriesFills(defaults.seriesFills);
  }
  if (stored != null && "hiddenSeries" in stored) {
    merged.hiddenSeries = sanitizeHiddenSeries(stored.hiddenSeries);
  } else {
    merged.hiddenSeries = sanitizeHiddenSeries(defaults.hiddenSeries);
  }
  if (stored != null && "seriesTrend" in stored) {
    merged.seriesTrend = sanitizeBooleanOverrideMap(stored.seriesTrend);
  } else {
    merged.seriesTrend = sanitizeBooleanOverrideMap(defaults.seriesTrend);
  }
  if (stored != null && "seriesTrendStyles" in stored) {
    merged.seriesTrendStyles = sanitizeSeriesTrendStyles(stored.seriesTrendStyles);
  } else {
    merged.seriesTrendStyles = sanitizeSeriesTrendStyles(defaults.seriesTrendStyles);
  }
  return merged;
}

/**
 * Persist chart view preferences (type, YoY, trend) in localStorage —
 * same browser persistence pattern as `usePersistedViewLayout` for tables.
 */
export function usePersistedChartPreferences(
  options: UsePersistedChartPreferencesOptions,
) {
  const {
    storageKey,
    defaults,
    allowedChartTypes,
    enabled = true,
  } = options;

  const defaultsKey = useMemo(() => JSON.stringify(defaults), [defaults]);
  const allowedKey = useMemo(
    () => (allowedChartTypes ? allowedChartTypes.join("|") : ""),
    [allowedChartTypes],
  );

  const [preferences, setPreferencesState] = useState<PersistedChartPreferences>(() => {
    if (!enabled) return { ...defaults };
    return mergePreferences(defaults, readStored(storageKey), allowedChartTypes);
  });

  useEffect(() => {
    if (!enabled) {
      setPreferencesState({ ...defaults });
      return;
    }
    setPreferencesState(
      mergePreferences(defaults, readStored(storageKey), allowedChartTypes),
    );
    // Re-sync when key or defaults identity changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- defaultsKey/allowedKey stand in for defaults/allowed
  }, [enabled, storageKey, defaultsKey, allowedKey]);

  useEffect(() => {
    if (!enabled) return;
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(preferences));
    } catch {
      /* ignore */
    }
  }, [enabled, preferences, storageKey]);

  const setPreferences = useCallback(
    (
      patch:
        | PersistedChartPreferences
        | ((prev: PersistedChartPreferences) => PersistedChartPreferences),
    ) => {
      setPreferencesState((prev) => {
        const next = typeof patch === "function" ? patch(prev) : { ...prev, ...patch };
        return mergePreferences(defaults, next, allowedChartTypes);
      });
    },
    [allowedChartTypes, defaults],
  );

  const setChartType = useCallback(
    (chartType: PersistedChartType) => {
      setPreferences({ chartType });
    },
    [setPreferences],
  );

  return {
    preferences,
    setPreferences,
    setChartType,
  };
}

export type UsePersistedChartPreferencesResult = ReturnType<
  typeof usePersistedChartPreferences
>;
