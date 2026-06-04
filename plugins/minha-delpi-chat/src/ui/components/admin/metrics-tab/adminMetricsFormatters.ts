export function formatMetricNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

export function formatMetricPercent(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return `${Math.round(value * 100)}%`;
}

export function formatMetricLoggedAt(value?: string | null): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("pt-BR");
}

export function rankedFromRecord(
  record: Record<string, number> | undefined,
  limit = 12,
): Array<{ label: string; value: string; key: string }> {
  if (!record) {
    return [];
  }

  return Object.entries(record)
    .sort((left, right) => right[1] - left[1])
    .slice(0, limit)
    .map(([label, count]) => ({
      label,
      value: formatMetricNumber(count),
      key: label,
    }));
}

export function rankedFromRows(
  rows: Array<{ key: string; count: number }> | undefined,
  limit = 12,
): Array<{ label: string; value: string; key: string }> {
  if (!rows?.length) {
    return [];
  }

  return rows.slice(0, limit).map((row) => ({
    label: row.key,
    value: formatMetricNumber(row.count),
    key: row.key,
  }));
}

export function rankedFromLabelCounts(
  rows: Array<{ label: string; count: number }> | undefined,
  limit = 12,
): Array<{ label: string; value: string; key: string }> {
  if (!rows?.length) {
    return [];
  }

  return rows.slice(0, limit).map((row) => ({
    label: row.label,
    value: formatMetricNumber(row.count),
    key: row.label,
  }));
}
