import type {
  EnrichedLmpItem,
  LmpItem,
  LmpNivel,
  LmpStatus
} from "../types/lmp";

type ChartDatum = {
  name: string;
  value: number;
};

type LeadByLevelDatum = {
  nivel: string;
  valor: number;
};

type EvolutionDatum = {
  periodo: string;
  mediaLead: number;
  propostas: number;
};

export type LmpsDashboardMetrics = {
  enrichedItems: EnrichedLmpItem[];
  totalLmps: number;
  percentDentroPrazo: number;
  avgLeadTime: number;
  levelData: ChartDatum[];
  statusData: ChartDatum[];
  leadByLevel: LeadByLevelDatum[];
  evolutionData: EvolutionDatum[];
};

const SLA_BY_LEVEL: Record<LmpNivel, number> = {
  "Nível 1": 4,
  "Nível 2": 8,
  "Nível 3": 20
};

function parseTotvsDate(value?: string | null): Date | null {
  if (!value || value.length !== 8) return null;

  const year = Number(value.slice(0, 4));
  const month = Number(value.slice(4, 6));
  const day = Number(value.slice(6, 8));

  if (!year || !month || !day) return null;

  return new Date(year, month - 1, day);
}

function isWeekend(date: Date): boolean {
  const day = date.getDay();
  return day === 0 || day === 6;
}

function addBusinessDays(start: Date, businessDays: number): Date {
  const result = new Date(start);
  let added = 0;

  while (added < businessDays) {
    result.setDate(result.getDate() + 1);
    if (!isWeekend(result)) {
      added += 1;
    }
  }

  return result;
}

function businessDaysBetween(start: Date, end: Date): number {
  if (end < start) return 0;

  const cursor = new Date(start);
  let count = 0;

  while (cursor <= end) {
    if (!isWeekend(cursor)) {
      count += 1;
    }
    cursor.setDate(cursor.getDate() + 1);
  }

  return count;
}

function formatDateToYmd(date: Date | null): string | null {
  if (!date) return null;

  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");

  return `${yyyy}${mm}${dd}`;
}

function getNivel(qtdPi?: number | null): LmpNivel {
  const value = qtdPi ?? 0;

  if (value <= 10) return "Nível 1";
  if (value <= 20) return "Nível 2";
  return "Nível 3";
}

function getPeriodo(dateValue?: string | null): string | null {
  const date = parseTotvsDate(dateValue);
  if (!date) return null;

  return date.toLocaleDateString("pt-BR", {
    month: "short",
    year: "2-digit"
  });
}

function enrichItem(item: LmpItem, today: Date): EnrichedLmpItem {
  const nivel = getNivel(item.qtd_pi);
  const dias_uteis_sla = SLA_BY_LEVEL[nivel];

  const startDate = parseTotvsDate(item.start_date);
  const endDate = parseTotvsDate(item.end_date);

  const dataLimiteDate = startDate ? addBusinessDays(startDate, dias_uteis_sla) : null;
  const lead_time_util =
    startDate && endDate ? businessDaysBetween(startDate, endDate) : null;

  let status: LmpStatus;

  if (!endDate) {
    status = dataLimiteDate && today > dataLimiteDate ? "Atrasado" : "Andamento";
  } else {
    status = dataLimiteDate && endDate <= dataLimiteDate ? "Pontual" : "Atrasado";
  }

  return {
    ...item,
    nivel,
    dias_uteis_sla,
    data_limite: formatDateToYmd(dataLimiteDate),
    lead_time_util,
    status
  };
}

export function adaptLmpsToDashboard(
  items: LmpItem[],
  statusFilter: string = "Todos"
): LmpsDashboardMetrics {
  const today = new Date();

  const enrichedItems = items.map((item) => enrichItem(item, today));

  const filteredItems =
    statusFilter === "Todos"
      ? enrichedItems
      : enrichedItems.filter((item) => item.status === statusFilter);

  const totalLmps = filteredItems.length;
  const pontuais = filteredItems.filter((item) => item.status === "Pontual").length;

  const percentDentroPrazo = totalLmps ? (pontuais / totalLmps) * 100 : 0;

  const leadItems = filteredItems.filter((item) => item.lead_time_util !== null);
  const avgLeadTime = leadItems.length
    ? leadItems.reduce((acc, item) => acc + (item.lead_time_util ?? 0), 0) /
      leadItems.length
    : 0;

  const levelOrder: LmpNivel[] = ["Nível 1", "Nível 2", "Nível 3"];
  const statusOrder: LmpStatus[] = ["Pontual", "Atrasado", "Andamento"];

  const levelData = levelOrder.map((name) => ({
    name,
    value: filteredItems.filter((item) => item.nivel === name).length
  }));

  const statusData = statusOrder.map((name) => ({
    name,
    value: filteredItems.filter((item) => item.status === name).length
  }));

  const leadByLevel = levelOrder.map((nivel) => {
    const itemsByLevel = filteredItems.filter(
      (item) => item.nivel === nivel && item.lead_time_util !== null
    );

    const avg =
      itemsByLevel.length > 0
        ? itemsByLevel.reduce((acc, item) => acc + (item.lead_time_util ?? 0), 0) /
          itemsByLevel.length
        : 0;

    return {
      nivel,
      valor: Number(avg.toFixed(2))
    };
  });

  const evolutionMap = new Map<
    string,
    { totalLead: number; leadCount: number; propostas: number }
  >();

  for (const item of filteredItems) {
    const periodo = getPeriodo(item.start_date);
    if (!periodo) continue;

    const current = evolutionMap.get(periodo) ?? {
      totalLead: 0,
      leadCount: 0,
      propostas: 0
    };

    current.propostas += 1;

    if (item.lead_time_util !== null) {
      current.totalLead += item.lead_time_util;
      current.leadCount += 1;
    }

    evolutionMap.set(periodo, current);
  }

  const evolutionData = Array.from(evolutionMap.entries()).map(
    ([periodo, value]) => ({
      periodo,
      mediaLead: value.leadCount
        ? Number((value.totalLead / value.leadCount).toFixed(2))
        : 0,
      propostas: value.propostas
    })
  );

  return {
    enrichedItems: filteredItems,
    totalLmps,
    percentDentroPrazo: Number(percentDentroPrazo.toFixed(2)),
    avgLeadTime: Number(avgLeadTime.toFixed(2)),
    levelData,
    statusData,
    leadByLevel,
    evolutionData
  };
}