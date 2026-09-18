import type {
  PersistedChartPreferences,
  SeriesTrendStyle,
} from "../../hooks/usePersistedChartPreferences";
import { isAutomaticTextColor } from "../shape/colorUtils";
import type { MultiTypeSeriesSpec } from "./MultiTypeSeriesChart";

export type { SeriesTrendStyle };
export type SeriesTrendDash = NonNullable<SeriesTrendStyle["dash"]>;

export type ChartSeriesConfigItem = {
  dataKey: string;
  name: string;
  fill: string;
  visible: boolean;
  trendCapable: boolean;
  trendEnabled: boolean;
  trendColor: string | null;
  trendDash: SeriesTrendDash;
  trendWidth: number;
  /** False for comparatives whose buckets are already complete. */
  trendApplyIncompleteBucket: boolean;
};

export type SeriesViewPreferenceSlice = Pick<
  PersistedChartPreferences,
  "seriesFills" | "hiddenSeries" | "showTrend" | "seriesTrend" | "seriesTrendStyles"
>;

const DEFAULT_TREND_WIDTH = 3;

/**
 * Apply persisted series fill overrides onto host default series specs.
 * Trend lines in MultiTypeSeriesChart inherit `source.fill` after this merge.
 */
export function applySeriesFillPreferences(
  series: ReadonlyArray<MultiTypeSeriesSpec>,
  seriesFills?: Record<string, string> | null,
): MultiTypeSeriesSpec[] {
  if (!seriesFills || Object.keys(seriesFills).length === 0) {
    return series.map((entry) => ({ ...entry }));
  }
  return series.map((entry) => {
    const override = seriesFills[entry.dataKey];
    if (typeof override !== "string") return { ...entry };
    const fill = override.trim();
    if (!fill) return { ...entry };
    return { ...entry, fill };
  });
}

export function omitRecordKey<T>(
  record: Record<string, T> | undefined,
  key: string,
): Record<string, T> | undefined {
  if (!record || !(key in record)) {
    return record && Object.keys(record).length > 0 ? record : undefined;
  }
  const next = { ...record };
  delete next[key];
  return Object.keys(next).length > 0 ? next : undefined;
}

export function isSeriesTrendCapable(
  entry: Pick<MultiTypeSeriesSpec, "trendCapable">,
): boolean {
  return entry.trendCapable !== false;
}

/** Effective ON state: only an explicit `seriesTrend[dataKey] === true`. */
export function resolveSeriesTrendEnabled(
  dataKey: string,
  eligible: boolean,
  seriesTrend?: Record<string, boolean> | null,
): boolean {
  if (!eligible) return false;
  return seriesTrend?.[dataKey] === true;
}

export function resolveEffectiveShowTrend(
  series: ReadonlyArray<Pick<MultiTypeSeriesSpec, "dataKey" | "trendCapable">>,
  seriesTrend?: Record<string, boolean> | null,
  hiddenSeries?: Record<string, boolean> | null,
): boolean {
  return series.some(
    (entry) =>
      !hiddenSeries?.[entry.dataKey] &&
      resolveSeriesTrendEnabled(
        entry.dataKey,
        isSeriesTrendCapable(entry),
        seriesTrend,
      ),
  );
}

export function applySeriesViewPreferences(
  series: ReadonlyArray<MultiTypeSeriesSpec>,
  preferences?: SeriesViewPreferenceSlice | null,
): MultiTypeSeriesSpec[] {
  const filled = applySeriesFillPreferences(series, preferences?.seriesFills);
  return filled
    .filter((entry) => !preferences?.hiddenSeries?.[entry.dataKey])
    .map((entry) => {
      const capable = isSeriesTrendCapable(entry);
      const trendOn = resolveSeriesTrendEnabled(
        entry.dataKey,
        capable,
        preferences?.seriesTrend,
      );
      const style = preferences?.seriesTrendStyles?.[entry.dataKey];
      const rawTrendColor = style?.color?.trim();
      const trendStroke =
        rawTrendColor && !isAutomaticTextColor(rawTrendColor)
          ? rawTrendColor
          : undefined;
      const trendLineStyle: SeriesTrendDash | undefined = style?.dash;
      const width = style?.width;
      const trendStrokeWidth =
        typeof width === "number" && Number.isFinite(width)
          ? Math.min(8, Math.max(1, Math.round(width)))
          : undefined;
      return {
        ...entry,
        trendSource: trendOn,
        trendStroke,
        trendLineStyle,
        trendStrokeWidth,
      };
    });
}

export function buildChartSeriesConfigItems(
  series: ReadonlyArray<MultiTypeSeriesSpec>,
  preferences?: SeriesViewPreferenceSlice | null,
): ChartSeriesConfigItem[] {
  const filled = applySeriesFillPreferences(series, preferences?.seriesFills);
  return filled.map((entry) => {
    const style = preferences?.seriesTrendStyles?.[entry.dataKey];
    const capable = isSeriesTrendCapable(entry);
    const width = style?.width;
    return {
      dataKey: entry.dataKey,
      name: entry.name,
      fill: entry.fill,
      visible: !preferences?.hiddenSeries?.[entry.dataKey],
      trendCapable: capable,
      trendEnabled: resolveSeriesTrendEnabled(
        entry.dataKey,
        capable,
        preferences?.seriesTrend,
      ),
      trendColor:
        style?.color?.trim() && !isAutomaticTextColor(style.color)
          ? style.color.trim()
          : null,
      trendDash: style?.dash === "solid" ? "solid" : "dashed",
      trendWidth:
        typeof width === "number" && Number.isFinite(width)
          ? Math.min(8, Math.max(1, Math.round(width)))
          : DEFAULT_TREND_WIDTH,
      trendApplyIncompleteBucket: entry.trendApplyIncompleteBucket !== false,
    };
  });
}

export function seriesViewHasOverrides(
  preferences?: SeriesViewPreferenceSlice | null,
): boolean {
  if (!preferences) return false;
  if (preferences.seriesFills && Object.keys(preferences.seriesFills).length > 0) {
    return true;
  }
  if (preferences.hiddenSeries && Object.keys(preferences.hiddenSeries).length > 0) {
    return true;
  }
  if (preferences.seriesTrend && Object.keys(preferences.seriesTrend).length > 0) {
    return true;
  }
  if (
    preferences.seriesTrendStyles &&
    Object.keys(preferences.seriesTrendStyles).length > 0
  ) {
    return true;
  }
  return false;
}

export function resetSeriesViewPreferences(
  prev: PersistedChartPreferences,
  dataKey?: string,
): PersistedChartPreferences {
  if (!dataKey) {
    return {
      ...prev,
      seriesFills: undefined,
      hiddenSeries: undefined,
      seriesTrend: undefined,
      seriesTrendStyles: undefined,
    };
  }
  return {
    ...prev,
    seriesFills: omitRecordKey(prev.seriesFills, dataKey),
    hiddenSeries: omitRecordKey(prev.hiddenSeries, dataKey),
    seriesTrend: omitRecordKey(prev.seriesTrend, dataKey),
    seriesTrendStyles: omitRecordKey(prev.seriesTrendStyles, dataKey),
  };
}

export function patchSeriesTrendStyle(
  prev: Record<string, SeriesTrendStyle> | undefined,
  dataKey: string,
  patch: SeriesTrendStyle,
): Record<string, SeriesTrendStyle> | undefined {
  const current = prev?.[dataKey] ?? {};
  const next: SeriesTrendStyle = { ...current };
  if ("color" in patch) {
    const color = patch.color?.trim() ?? "";
    if (color) next.color = color;
    else delete next.color;
  }
  if ("dash" in patch) {
    if (patch.dash === "solid" || patch.dash === "dashed") next.dash = patch.dash;
    else delete next.dash;
  }
  if ("width" in patch) {
    if (typeof patch.width === "number" && Number.isFinite(patch.width)) {
      next.width = Math.min(8, Math.max(1, Math.round(patch.width)));
    } else {
      delete next.width;
    }
  }
  if (!next.color && !next.dash && next.width == null) {
    return omitRecordKey(prev, dataKey);
  }
  return { ...prev, [dataKey]: next };
}
