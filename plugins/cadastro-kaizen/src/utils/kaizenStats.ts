import type { KaizenRecord, KaizenStatus } from "../types/kaizen";
import { unitLabel } from "./labels";

export type CountBucket = { key: string; label: string; value: number };

export type ValidityBucket = {
  record: KaizenRecord;
  validUntil: string;
  daysLeft: number;
};

export type KaizenStats = {
  total: number;
  implantados: number;
  emAndamento: number;
  descontinuados: number;
  cancelados: number;
  activeAnnualSavings: number;
  realizedAnnualSavings: number;
  totalInvestment: number;
  activeCount: number;
  /** Indicador: ganhos financeiros no período (economia_diária × dias ativos, validade 1 ano). */
  periodSavings: number;
  /** Indicador: total de kaizens implantados no período. */
  periodImplantedCount: number;
  /** Indicador: implantados por mês (série cronológica pela date_implemented). */
  implantedByMonth: CountBucket[];
  /** Há filtro de período aplicado? Muda o rótulo dos indicadores (período vs acumulado). */
  hasPeriod: boolean;
  byStatus: CountBucket[];
  byBranch: CountBucket[];
  bySavingsType: CountBucket[];
  byCategory: CountBucket[];
  topAccountables: CountBucket[];
  expiringSoon: ValidityBucket[];
  expiredButImplanted: number;
  recent: KaizenRecord[];
};

export type ComputeStatsOptions = {
  dateStart?: string;
  dateEnd?: string;
};

const STATUS_LABEL: Record<KaizenStatus, string> = {
  em_andamento: "Em andamento",
  implantado: "Implantado",
  descontinuado: "Descontinuado",
  cancelado: "Cancelado",
};

const SAVINGS_LABEL: Record<string, string> = {
  tempo: "Tempo",
  material: "Material",
  financeiro: "Financeiro",
  qualitativo: "Qualitativo",
  misto: "Misto",
};

const EXPIRING_WINDOW_DAYS = 90;
const DAY_MS = 86_400_000;
const MONTH_FMT = new Intl.DateTimeFormat("pt-BR", { month: "short", year: "numeric" });

function toDate(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const date = new Date(`${iso.slice(0, 10)}T00:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

/** Último dia em que o kaizen ainda contabiliza (implantação + 1 ano − 1 dia). */
function savingsValidUntil(implemented: Date): Date {
  const value = new Date(implemented);
  value.setFullYear(value.getFullYear() + 1);
  value.setDate(value.getDate() - 1);
  return value;
}

/**
 * Dias em que o kaizen contabiliza ganhos dentro do intervalo, aplicando o teto de
 * 1 ano de validade. Espelha `kaizen_savings_validity.active_days_in_range` da API.
 */
export function activeDaysInRange(
  implementedIso: string | null | undefined,
  startIso: string | undefined,
  endIso: string | undefined,
  today: Date,
): number {
  const implemented = toDate(implementedIso);
  if (!implemented) return 0;
  const start = toDate(startIso) ?? implemented;
  const end = toDate(endIso) ?? today;
  const effectiveStart = implemented > start ? implemented : start;
  const validUntil = savingsValidUntil(implemented);
  const effectiveEnd = end < validUntil ? end : validUntil;
  if (effectiveStart > effectiveEnd) return 0;
  return Math.floor((effectiveEnd.getTime() - effectiveStart.getTime()) / DAY_MS) + 1;
}

function monthLabel(key: string): string {
  const [year, month] = key.split("-").map(Number);
  if (!year || !month) return key;
  return MONTH_FMT.format(new Date(year, month - 1, 1));
}

function tally(
  records: KaizenRecord[],
  keyOf: (record: KaizenRecord) => string,
  labelOf: (key: string) => string,
): CountBucket[] {
  const map = new Map<string, number>();
  for (const record of records) {
    const key = keyOf(record);
    map.set(key, (map.get(key) ?? 0) + 1);
  }
  return [...map.entries()]
    .map(([key, value]) => ({ key, label: labelOf(key), value }))
    .sort((a, b) => b.value - a.value);
}

function daysBetween(fromIso: string): number {
  const target = new Date(`${fromIso}T00:00:00`).getTime();
  if (Number.isNaN(target)) return Number.POSITIVE_INFINITY;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target - today.getTime()) / (1000 * 60 * 60 * 24));
}

export function computeKaizenStats(
  allRecords: KaizenRecord[],
  options: ComputeStatsOptions = {},
): KaizenStats {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const { dateStart, dateEnd } = options;
  const hasPeriod = Boolean(dateStart || dateEnd);

  // Registros no período (pela data de implantação) — base das contagens/distribuições.
  const records = allRecords.filter((record) => {
    if (!hasPeriod) return true;
    const implemented = record.date_implemented;
    if (!implemented) return false;
    if (dateStart && implemented < dateStart) return false;
    if (dateEnd && implemented > dateEnd) return false;
    return true;
  });

  // Indicador 1 — ganhos financeiros no período: sobre TODOS os registros (inclui os
  // implantados antes do período que ainda contabilizam), ponderado por dias ativos.
  const periodSavings = allRecords.reduce((sum, record) => {
    if (record.status !== "implantado") return sum;
    const daily = record.daily_savings ?? 0;
    if (!daily) return sum;
    return sum + daily * activeDaysInRange(record.date_implemented, dateStart, dateEnd, today);
  }, 0);

  // Indicador 2 — novos implantados por mês (pela date_implemented, dentro do período).
  const implantedInPeriod = records.filter(
    (r) => r.status === "implantado" && r.date_implemented,
  );
  const monthCounts = new Map<string, number>();
  for (const record of implantedInPeriod) {
    const key = (record.date_implemented as string).slice(0, 7);
    monthCounts.set(key, (monthCounts.get(key) ?? 0) + 1);
  }
  const implantedByMonth: CountBucket[] = [...monthCounts.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([key, value]) => ({ key, label: monthLabel(key), value }));

  const byStatusCount = (status: KaizenStatus) =>
    records.filter((r) => r.status === status).length;

  const activeRecords = records.filter((r) => r.savings_active && r.status === "implantado");

  const expiringSoon: ValidityBucket[] = activeRecords
    .filter((r) => r.savings_valid_until)
    .map((r) => ({
      record: r,
      validUntil: r.savings_valid_until as string,
      daysLeft: daysBetween(r.savings_valid_until as string),
    }))
    .filter((b) => b.daysLeft <= EXPIRING_WINDOW_DAYS)
    .sort((a, b) => a.daysLeft - b.daysLeft);

  const expiredButImplanted = records.filter(
    (r) => r.status === "implantado" && !r.savings_active && r.date_implemented,
  ).length;

  const recent = [...records]
    .sort((a, b) => (b.created_at ?? "").localeCompare(a.created_at ?? ""))
    .slice(0, 6);

  return {
    total: records.length,
    implantados: byStatusCount("implantado"),
    emAndamento: byStatusCount("em_andamento"),
    descontinuados: byStatusCount("descontinuado"),
    cancelados: byStatusCount("cancelado"),
    activeAnnualSavings: activeRecords.reduce((sum, r) => sum + (r.annual_savings ?? 0), 0),
    realizedAnnualSavings: activeRecords.reduce(
      (sum, r) => sum + (r.realized_annual_savings ?? 0),
      0,
    ),
    totalInvestment: records.reduce((sum, r) => sum + (r.investment ?? 0), 0),
    activeCount: activeRecords.length,
    periodSavings: Math.round(periodSavings * 100) / 100,
    periodImplantedCount: implantedInPeriod.length,
    implantedByMonth,
    hasPeriod,
    byStatus: tally(
      records,
      (r) => r.status,
      (key) => STATUS_LABEL[key as KaizenStatus] ?? key,
    ),
    byBranch: tally(
      records,
      (r) => r.branch_code,
      (key) => unitLabel(key),
    ),
    bySavingsType: tally(
      records,
      (r) => r.savings_type ?? "—",
      (key) => SAVINGS_LABEL[key] ?? key,
    ),
    byCategory: tally(
      records,
      (r) => r.category ?? "sem_categoria",
      (key) => (key === "sem_categoria" ? "Sem categoria" : key),
    ),
    topAccountables: tally(
      records.filter((r) => r.accountable),
      (r) => r.accountable as string,
      (key) => key,
    ).slice(0, 6),
    expiringSoon,
    expiredButImplanted,
    recent,
  };
}
