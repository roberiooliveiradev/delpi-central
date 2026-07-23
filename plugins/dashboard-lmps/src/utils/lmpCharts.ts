import type { LmpDashboardItem } from "../types/lmp";
import type { LmpsDashboardCharts } from "../api/lmpApi";
import { lmpDateSortKey } from "./dates";

export function buildLmpFallbackCharts(
  items: LmpDashboardItem[]
): Required<Pick<LmpsDashboardCharts, "levelData" | "statusData" | "leadByLevel">> {
  const levelOrder = ["Nível 1", "Nível 2", "Nível 3"];
  const statusOrder = ["Pontual", "Atrasado", "Andamento", "Retornada"];

  const levelData = levelOrder.map((name) => ({
    name,
    value: items.filter((item) => item.nivel === name).length,
  }));

  const statusData = statusOrder.map((name) => ({
    name,
    value: items.filter((item) => item.status === name).length,
  }));

  const leadByLevel = levelOrder.map((nivel) => {
    const itemsByLevel = items.filter(
      (item) => item.nivel === nivel && item.lead_time_util != null
    );
    const avg =
      itemsByLevel.length > 0
        ? itemsByLevel.reduce(
            (acc, item) => acc + (item.lead_time_util ?? 0),
            0
          ) / itemsByLevel.length
        : 0;

    return { nivel, valor: Number(avg.toFixed(2)) };
  });

  return { levelData, statusData, leadByLevel };
}

/** Número YYYYMMDD para sort (aceita dd/mm/yyyy e YYYYMMDD). */
export function parseLmpDateNumber(value?: string | null): number {
  const key = lmpDateSortKey(value);
  if (!key) return 0;
  const parsed = Number(key);
  return Number.isNaN(parsed) ? 0 : parsed;
}
