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

export type PersistedChartPreferences = {
  chartType?: PersistedChartType;
  comparePriorYear?: boolean;
  /** YoY depth for billing series (0–3). */
  compareYears?: number;
  showTrend?: boolean;
  /** Incomplete bucket handling for OLS trend. Default exclude when unset. */
  incompleteBucketMode?: "exclude" | "weightByFraction";
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
