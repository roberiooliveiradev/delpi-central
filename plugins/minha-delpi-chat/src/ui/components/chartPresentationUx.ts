const PERIOD_FIELD_KEYS = ["period", "periodo", "ano", "year", "referencia", "reference"];
const MONTH_PATTERN =
  /^(20\d{2}[-/]?(0[1-9]|1[0-2])|[0-9]{1,2}[/\-](20)?\d{2}|jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)/i;

export type ChartTopFilter = "all" | "5" | "10" | "20";

export type ChartZoomWindow = "all" | "6" | "12" | "24";

export type PeriodCompareSpec = {
  periodKey: string;
  categoryKey: string;
  valueKey: string;
  periods: string[];
};

export function isTemporalChartAxis(xAxis: string, data: Record<string, unknown>[]): boolean {
  if (!xAxis || data.length < 3) {
    return false;
  }

  const matches = data.filter((row) => MONTH_PATTERN.test(String(row[xAxis] ?? ""))).length;

  return matches >= Math.ceil(data.length * 0.6);
}

export function applyChartTopFilter(
  data: Record<string, unknown>[],
  xAxis: string,
  valueKey: string,
  limit: ChartTopFilter,
): Record<string, unknown>[] {
  if (limit === "all" || data.length <= Number(limit)) {
    return data;
  }

  const max = Number(limit);

  return [...data]
    .sort((left, right) => {
      const a = Number(left[valueKey]);
      const b = Number(right[valueKey]);

      if (Number.isFinite(a) && Number.isFinite(b)) {
        return b - a;
      }

      return 0;
    })
    .slice(0, max);
}

export function applyChartZoomWindow(
  data: Record<string, unknown>[],
  window: ChartZoomWindow,
): Record<string, unknown>[] {
  if (window === "all" || data.length <= Number(window)) {
    return data;
  }

  return data.slice(-Number(window));
}

export function detectPeriodCompare(
  data: Record<string, unknown>[],
  xAxis: string,
  valueKey: string,
): PeriodCompareSpec | null {
  if (!data.length) {
    return null;
  }

  const sample = data[0];
  const periodKey = PERIOD_FIELD_KEYS.find((key) => key in sample && key !== xAxis);

  if (!periodKey) {
    return null;
  }

  const periods = [
    ...new Set(
      data
        .map((row) => String(row[periodKey] ?? "").trim())
        .filter(Boolean),
    ),
  ].sort();

  if (periods.length < 2) {
    return null;
  }

  const categoryKey = xAxis && xAxis !== periodKey ? xAxis : guessCategoryKey(sample, periodKey, valueKey);

  if (!categoryKey) {
    return null;
  }

  return {
    periodKey,
    categoryKey,
    valueKey,
    periods: periods.slice(0, 4),
  };
}

export function buildPeriodComparisonRows(
  data: Record<string, unknown>[],
  spec: PeriodCompareSpec,
): { rows: Record<string, unknown>[]; yAxes: string[] } {
  const categories = [
    ...new Set(
      data
        .map((row) => String(row[spec.categoryKey] ?? "").trim())
        .filter(Boolean),
    ),
  ];

  const rows = categories.map((category) => {
    const row: Record<string, unknown> = {
      [spec.categoryKey]: category,
    };

    for (const period of spec.periods) {
      const match = data.find(
        (item) =>
          String(item[spec.categoryKey] ?? "") === category &&
          String(item[spec.periodKey] ?? "") === period,
      );

      const raw = match?.[spec.valueKey];
      row[period] = typeof raw === "number" ? raw : Number(raw) || 0;
    }

    return row;
  });

  return { rows, yAxes: spec.periods };
}

function guessCategoryKey(
  sample: Record<string, unknown>,
  periodKey: string,
  valueKey: string,
): string | null {
  for (const key of Object.keys(sample)) {
    if (key === periodKey || key === valueKey) {
      continue;
    }

    if (typeof sample[key] === "string") {
      return key;
    }
  }

  return null;
}

export function firstNumericValueKey(
  data: Record<string, unknown>[],
  xAxis: string,
  yAxes: string[],
): string {
  if (yAxes[0]) {
    return yAxes[0];
  }

  const sample = data[0] ?? {};

  for (const key of Object.keys(sample)) {
    if (key === xAxis) {
      continue;
    }

    const value = sample[key];

    if (typeof value === "number" && Number.isFinite(value)) {
      return key;
    }
  }

  return "value";
}
