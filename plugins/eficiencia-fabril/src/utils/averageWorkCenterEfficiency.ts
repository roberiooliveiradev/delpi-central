import type { EfficiencyByWorkCenter } from "../types/eficienciaFabril";

const PLACEHOLDER_WORK_CENTER = "—";

/** Média simples das eficiências já agregadas por CT (KPI do dashboard). */
export function averageWorkCenterEfficiencyPct(
  rows: EfficiencyByWorkCenter[]
): number | null {
  const values = rows
    .filter((row) => {
      const workCenter = row.work_center?.trim();
      return Boolean(workCenter) && workCenter !== PLACEHOLDER_WORK_CENTER;
    })
    .map((row) => row.efficiency_pct)
    .filter((value): value is number => value !== null && value !== undefined && !Number.isNaN(value));

  if (values.length === 0) return null;
  return Math.round((values.reduce((acc, value) => acc + value, 0) / values.length) * 100) / 100;
}
