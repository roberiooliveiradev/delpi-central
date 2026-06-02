import type { DashboardEvolucaoItem } from "../data/api/transformometroApi";
import type { ChartGranularity } from "../types/chart";
import { buildPeriodBuckets } from "./periodBuckets";

export type SavingsChartPoint = {
  name: string;
  bruta: number;
  liquida: number;
  investimento: number;
  sortKey: string;
};

export type EvolucaoChartSeriesResult = {
  points: SavingsChartPoint[];
  truncated: boolean;
  /** Total mensal distribuído igualmente por dia do mês (materialização é por competência). */
  dayProrated: boolean;
};

function daysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}

function addDailyFromCompetencia(
  competencia: string,
  bruta: number,
  liquida: number,
  investimento: number,
  dateStart: string,
  dateEnd: string,
  totals: Map<string, { bruta: number; liquida: number; investimento: number }>
) {
  const match = competencia.match(/^(\d{4})-(\d{2})$/);
  if (!match) return;

  const year = Number(match[1]);
  const month = Number(match[2]);
  const dim = daysInMonth(year, month);
  const perDayBruta = bruta / dim;
  const perDayLiquida = liquida / dim;
  const perDayInvestimento = investimento / dim;

  for (let day = 1; day <= dim; day += 1) {
    const iso = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    if (iso < dateStart || iso > dateEnd) continue;

    const current = totals.get(iso) ?? { bruta: 0, liquida: 0, investimento: 0 };
    current.bruta += perDayBruta;
    current.liquida += perDayLiquida;
    current.investimento += perDayInvestimento;
    totals.set(iso, current);
  }
}

export function buildEvolucaoSavingsSeries(
  items: DashboardEvolucaoItem[],
  dateStart: string | undefined,
  dateEnd: string | undefined,
  granularity: ChartGranularity
): EvolucaoChartSeriesResult {
  if (!dateStart || !dateEnd) {
    return { points: [], truncated: false, dayProrated: false };
  }

  const byMonth = new Map<string, { bruta: number; liquida: number; investimento: number }>();
  for (const item of items) {
    const key = item.competencia?.trim() ?? "";
    if (!key) continue;
    const current = byMonth.get(key) ?? { bruta: 0, liquida: 0, investimento: 0 };
    current.bruta += Number(item.economia_bruta ?? 0);
    current.liquida += Number(item.economia_liquida_mes ?? 0);
    current.investimento += Number(item.investimento_unico_mes ?? 0);
    byMonth.set(key, current);
  }

  const { buckets, truncated } = buildPeriodBuckets(dateStart, dateEnd, granularity);

  if (granularity === "day") {
    const dailyTotals = new Map<string, { bruta: number; liquida: number; investimento: number }>();

    for (const [competencia, values] of byMonth) {
      addDailyFromCompetencia(
        competencia,
        values.bruta,
        values.liquida,
        values.investimento,
        dateStart,
        dateEnd,
        dailyTotals
      );
    }

    const points = buckets.map((bucket) => {
      const row = dailyTotals.get(bucket.key);
      return {
        name: bucket.label,
        sortKey: bucket.key,
        bruta: Number((row?.bruta ?? 0).toFixed(2)),
        liquida: Number((row?.liquida ?? 0).toFixed(2)),
        investimento: Number((row?.investimento ?? 0).toFixed(2)),
      };
    });

    return { points, truncated, dayProrated: true };
  }

  if (granularity === "month") {
    const points = buckets.map((bucket) => {
      const row = byMonth.get(bucket.key);
      return {
        name: bucket.label,
        sortKey: bucket.key,
        bruta: Number((row?.bruta ?? 0).toFixed(2)),
        liquida: Number((row?.liquida ?? 0).toFixed(2)),
        investimento: Number((row?.investimento ?? 0).toFixed(2)),
      };
    });

    return { points, truncated, dayProrated: false };
  }

  const byYear = new Map<string, { bruta: number; liquida: number; investimento: number }>();
  for (const [monthKey, values] of byMonth) {
    const year = monthKey.slice(0, 4);
    const current = byYear.get(year) ?? { bruta: 0, liquida: 0, investimento: 0 };
    current.bruta += values.bruta;
    current.liquida += values.liquida;
    current.investimento += values.investimento;
    byYear.set(year, current);
  }

  const points = buckets.map((bucket) => {
    const row = byYear.get(bucket.key);
    return {
      name: bucket.label,
      sortKey: bucket.key,
      bruta: Number((row?.bruta ?? 0).toFixed(2)),
      liquida: Number((row?.liquida ?? 0).toFixed(2)),
      investimento: Number((row?.investimento ?? 0).toFixed(2)),
    };
  });

  return { points, truncated, dayProrated: false };
}
