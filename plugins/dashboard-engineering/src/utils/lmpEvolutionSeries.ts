import type { ChartGranularity } from "../types/chart";
import type { LmpDashboardItem, LmpsEvolutionDatum } from "../types/lmp";
import { lmpDateToIso } from "./dates";
import { aggregateAverageByPeriod, aggregateCountByPeriod } from "./timeSeriesAggregation";

export function aggregateLmpEvolutionSeries(
  items: LmpDashboardItem[],
  dateStart?: string,
  dateEnd?: string,
  granularity: ChartGranularity = "month"
): LmpsEvolutionDatum[] {
  const counts = aggregateCountByPeriod({
    items,
    getDate: (item) => lmpDateToIso(item.start_date),
    dateStart,
    dateEnd,
    granularity,
  });

  const leads = aggregateAverageByPeriod({
    items,
    getDate: (item) => lmpDateToIso(item.start_date),
    getValue: (item) => item.lead_time_util,
    dateStart,
    dateEnd,
    granularity,
  });

  const leadByKey = new Map(leads.map((point) => [point.sortKey, point.value]));

  return counts.map((point) => ({
    periodo: point.periodo,
    mediaLead: leadByKey.get(point.sortKey) ?? 0,
    propostas: point.value,
  }));
}
