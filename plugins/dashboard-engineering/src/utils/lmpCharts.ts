import type {
  LmpDashboardItem,
  LmpsDashboardCharts,
  LmpsEvolutionDatum,
} from "../types/lmp";
import { lmpDateSortKey, parseDateParts } from "./dates";

function parseDateNumber(value?: string | null): number {
  const key = lmpDateSortKey(value);
  if (!key) return 0;
  const parsed = Number(key);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function getPeriodo(dateValue?: string | null): string | null {
  const parts = parseDateParts(dateValue);
  if (!parts) return null;

  const date = new Date(parts.year, parts.month - 1, parts.day);
  return date.toLocaleDateString("pt-BR", {
    month: "short",
    year: "2-digit",
  });
}

export function buildLmpFallbackCharts(
  items: LmpDashboardItem[]
): Required<LmpsDashboardCharts> {
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

  const evolutionMap = new Map<
    string,
    {
      periodo: string;
      sortKey: number;
      totalLead: number;
      leadCount: number;
      propostas: number;
    }
  >();

  for (const item of items) {
    const periodo = getPeriodo(item.start_date);
    const sortKey = parseDateNumber(item.start_date);
    if (!periodo || !sortKey) continue;

    const current = evolutionMap.get(periodo) ?? {
      periodo,
      sortKey,
      totalLead: 0,
      leadCount: 0,
      propostas: 0,
    };

    current.propostas += 1;
    if (item.lead_time_util != null) {
      current.totalLead += item.lead_time_util;
      current.leadCount += 1;
    }
    if (sortKey < current.sortKey) current.sortKey = sortKey;
    evolutionMap.set(periodo, current);
  }

  const evolutionData: LmpsEvolutionDatum[] = Array.from(evolutionMap.values())
    .sort((a, b) => a.sortKey - b.sortKey)
    .map(({ periodo, totalLead, leadCount, propostas }) => ({
      periodo,
      mediaLead: leadCount ? Number((totalLead / leadCount).toFixed(2)) : 0,
      propostas,
    }));

  return { levelData, statusData, leadByLevel, evolutionData };
}
