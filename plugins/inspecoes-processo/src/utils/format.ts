export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return value.toLocaleString("pt-BR");
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`;
}

export function formatIsoDatePt(value: string | null | undefined): string {
  const normalized = value?.trim();
  if (!normalized) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(normalized);
  if (!match) return normalized;
  return `${match[3]}/${match[2]}/${match[1]}`;
}
