import type { ChartGranularity } from "../types/chartGranularity";

function parseIsoDate(value: string): Date | null {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(year, month - 1, day);

  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return null;
  }

  return date;
}

/**
 * Granularidade automática do gráfico por duração do período:
 * - até ~1 mês (≤ 31 dias inclusive) → `day`
 * - maior que 1 mês → `month`
 */
export function suggestChartGranularity(
  dateStart?: string,
  dateEnd?: string,
): ChartGranularity {
  if (!dateStart || !dateEnd) return "month";

  const start = parseIsoDate(dateStart);
  const end = parseIsoDate(dateEnd);

  if (!start || !end || start > end) return "month";

  const diffDays =
    Math.floor((end.getTime() - start.getTime()) / 86_400_000) + 1;

  if (diffDays <= 31) return "day";
  return "month";
}
