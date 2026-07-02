import type { KaizenRecord, KaizenStatus } from "../types/kaizen";

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
  byStatus: CountBucket[];
  byBranch: CountBucket[];
  bySavingsType: CountBucket[];
  byCategory: CountBucket[];
  topAccountables: CountBucket[];
  expiringSoon: ValidityBucket[];
  expiredButImplanted: number;
  recent: KaizenRecord[];
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

export function computeKaizenStats(records: KaizenRecord[]): KaizenStats {
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
    byStatus: tally(
      records,
      (r) => r.status,
      (key) => STATUS_LABEL[key as KaizenStatus] ?? key,
    ),
    byBranch: tally(
      records,
      (r) => r.branch_code,
      (key) => `Filial ${key}`,
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
