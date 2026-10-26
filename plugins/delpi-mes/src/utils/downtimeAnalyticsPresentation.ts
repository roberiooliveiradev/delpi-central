import type {
  DowntimeAnalyticsHourCell,
  DowntimeAnalyticsQuery,
  DowntimeAnalyticsResponse,
} from "../types/mes";
import type { BranchCode } from "../constants/routes";
import type { DowntimesRouteParams } from "../hooks/useDelpiMesRoute";
import { resolveDowntimePeriod } from "./downtimesPresentation";

/** Consulta analítica derivada dos MESMOS filtros da listagem — paginação,
 * ordenação e downtimeId nunca são determinantes de métrica (RQ-E2-06).
 * Retorna null quando o período não tem início definido (custom sem "de"):
 * nesse caso a visão analítica não consulta a API e a lista segue normal. */
export function buildDowntimeAnalyticsQuery(
  branch: BranchCode,
  params: DowntimesRouteParams,
  now: Date = new Date(),
): DowntimeAnalyticsQuery | null {
  const period = resolveDowntimePeriod(params, now);
  if (!period.from) return null;
  return {
    branch,
    from: period.from,
    to: period.to,
    workCenter: params.workCenter?.trim() || undefined,
    reasonCode: params.reasonCode || undefined,
    source: params.source || undefined,
    classification: params.classification || undefined,
  };
}

export const PENDING_REASON_GROUP_KEY = "pending";

/** Rótulo do dia no formato dd/mm — date já é a chave civil de
 * America/Sao_Paulo produzida pelo backend (YYYY-MM-DD). */
export function dayKeyLabel(date: string): string {
  const parts = date.split("-");
  return parts.length === 3 ? parts[2] + "/" + parts[1] : date;
}

export type HeatmapRow = {
  weekday: number;
  weekdayLabel: string;
  hours: Array<{ hour: number; seconds: number; occurrencesCount: number }>;
};

const WEEKDAY_ROW_LABELS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

/** Matriz 7x24 para o mapa de calor — células ausentes valem zero.
 * Ordena seg→dom (weekday 0..6 do backend). */
export function buildHeatmapRows(cells: DowntimeAnalyticsHourCell[]): {
  rows: HeatmapRow[];
  maxSeconds: number;
} {
  const byCell = new Map<string, DowntimeAnalyticsHourCell>();
  let maxSeconds = 0;
  for (const cell of cells) {
    byCell.set(cell.weekday + "-" + cell.hour, cell);
    if (cell.seconds > maxSeconds) maxSeconds = cell.seconds;
  }
  const rows: HeatmapRow[] = [];
  for (let weekday = 0; weekday < 7; weekday += 1) {
    const hours = [];
    for (let hour = 0; hour < 24; hour += 1) {
      const cell = byCell.get(weekday + "-" + hour);
      hours.push({
        hour,
        seconds: cell?.seconds ?? 0,
        occurrencesCount: cell?.occurrencesCount ?? 0,
      });
    }
    rows.push({ weekday, weekdayLabel: WEEKDAY_ROW_LABELS[weekday], hours });
  }
  return { rows, maxSeconds };
}

export type AnalyticsMetric = "seconds" | "occurrences";

export function daySeriesPoints(
  days: DowntimeAnalyticsResponse["byDay"],
  metric: AnalyticsMetric,
): Array<{ label: string; value: number }> {
  return days.map((day) => ({
    label: dayKeyLabel(day.date),
    value: metric === "seconds" ? Math.round(day.seconds / 60) : day.occurrencesCount,
  }));
}
