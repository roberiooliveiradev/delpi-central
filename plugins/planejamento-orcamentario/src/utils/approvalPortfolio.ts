import type {
  CapexConsolidationGroupItem,
  CapexPlan,
  PersonnelPlan,
} from "../types/budgetPlanning";
import {
  getCapexReviewDetail,
  listCapexReviewQueue,
  listPersonnelReviewQueue,
} from "../api/budgetPlanningApi";
import { activeInvestments, sumEstimatedAmounts } from "./capexPlans";
import {
  BUDGET_BRANCHES,
  branchCityLabel,
  normalizeBranchCode,
} from "./orgCostCenters";

export type EnrichedCapexPlan = CapexPlan & {
  investment_count?: number;
  total_amount?: string;
};

export type ApprovalPortfolioItem = {
  key: string;
  unit_id: string;
  cost_center_id: string;
  area_id: string | null;
  branch: string | null;
  /** Nome amigável do CC quando disponível (consolidação / catálogo). */
  cost_center_name: string | null;
  /** Lucide key do CC (`org_cost_centers.icon_key`). */
  icon_key: string | null;
  /** Nome do responsável (owner) do centro de custo. */
  owner_name: string | null;
  capexPlan: EnrichedCapexPlan | null;
  personnelPlan: PersonnelPlan | null;
  capexPending: boolean;
  personnelPending: boolean;
  /** Elaboração em rascunho (ainda não enviado). */
  capexInProgress: boolean;
  personnelInProgress: boolean;
  capexAmount: number;
  personnelHeadcount: number;
  urgency: number;
};

/** Statuses visíveis no radar da diretoria (não só enviados). */
export const APPROVAL_PORTFOLIO_STATUSES = [
  "submitted",
  "draft",
  "changes_requested",
  "approved",
  "rejected",
] as const;

const PLAN_STATUS_RANK: Record<string, number> = {
  submitted: 50,
  changes_requested: 40,
  draft: 30,
  approved: 20,
  rejected: 10,
};

function pairKey(unitId: string, costCenterId: string): string {
  return `${unitId}::${costCenterId}`;
}

function amountOf(plan: EnrichedCapexPlan | null): number {
  if (!plan?.total_amount) return 0;
  const n = Number(plan.total_amount);
  return Number.isFinite(n) ? n : 0;
}

function headcountOf(plan: PersonnelPlan | null): number {
  const n = Number(plan?.totals?.headcount_dec_2027 ?? 0);
  return Number.isFinite(n) ? n : 0;
}

/** Rascunho CAPEX só é «em andamento» com ≥1 investimento. */
function capexDraftInProgress(plan: EnrichedCapexPlan): boolean {
  if (plan.status !== "draft") return false;
  const n = Number(plan.investment_count ?? 0);
  return Number.isFinite(n) && n >= 1;
}

/** Rascunho Pessoal só é «em andamento» com ≥1 cargo/linha. */
function personnelDraftInProgress(plan: PersonnelPlan): boolean {
  if (plan.status !== "draft") return false;
  const n = Number(plan.position_count ?? 0);
  return Number.isFinite(n) && n >= 1;
}

function statusRank(status?: string | null): number {
  return PLAN_STATUS_RANK[String(status || "")] ?? 0;
}

function preferPlan<T extends { status?: string | null }>(
  current: T | null,
  candidate: T,
): boolean {
  if (!current) return true;
  return statusRank(candidate.status) > statusRank(current.status);
}

/** Rótulo curto do status do plano para a lista compacta. */
export function approvalPlanStatusLabel(status?: string | null): string {
  switch (status) {
    case "submitted":
      return "Aguardando aprovação";
    case "draft":
      return "Em andamento";
    case "changes_requested":
      return "Ajustes solicitados";
    case "approved":
      return "Aprovado";
    case "rejected":
      return "Reprovado";
    default:
      return status?.trim() || "—";
  }
}

export function approvalPlanStatusTone(
  status?: string | null,
): "warning" | "info" | "success" | "muted" | "danger" {
  switch (status) {
    case "submitted":
      return "warning";
    case "draft":
    case "changes_requested":
      return "info";
    case "approved":
      return "success";
    case "rejected":
      return "danger";
    default:
      return "muted";
  }
}

/** Une filas CAPEX e Pessoal por filial+CC; inclui rascunhos (em andamento). */
export function mergeApprovalPortfolio(
  capexItems: EnrichedCapexPlan[],
  personnelItems: PersonnelPlan[],
): ApprovalPortfolioItem[] {
  const map = new Map<string, ApprovalPortfolioItem>();

  const ensure = (
    unit_id: string,
    cost_center_id: string,
    area_id?: string | null,
    branch?: string | null,
    cost_center_name?: string | null,
    icon_key?: string | null,
    owner_name?: string | null,
  ) => {
    const key = pairKey(unit_id, cost_center_id);
    const current = map.get(key) ?? {
      key,
      unit_id,
      cost_center_id,
      area_id: area_id ?? null,
      branch: branch ?? unit_id,
      cost_center_name: cost_center_name ?? null,
      icon_key: icon_key ?? null,
      owner_name: owner_name ?? null,
      capexPlan: null,
      personnelPlan: null,
      capexPending: false,
      personnelPending: false,
      capexInProgress: false,
      personnelInProgress: false,
      capexAmount: 0,
      personnelHeadcount: 0,
      urgency: 0,
    };
    if (area_id && !current.area_id) current.area_id = area_id;
    if (branch) current.branch = branch;
    if (cost_center_name && !current.cost_center_name) {
      current.cost_center_name = cost_center_name;
    }
    if (icon_key && !current.icon_key) {
      current.icon_key = icon_key;
    }
    if (owner_name && !current.owner_name) {
      current.owner_name = owner_name;
    }
    map.set(key, current);
    return current;
  };

  for (const plan of capexItems) {
    const unit_id = String(plan.unit_id || "");
    const cost_center_id = String(plan.cost_center_id || "");
    if (!unit_id || !cost_center_id) continue;
    const row = ensure(
      unit_id,
      cost_center_id,
      plan.area_id,
      plan.branch ?? plan.unit_id,
      plan.cost_center_name,
      plan.cost_center_icon_key,
      plan.cost_center_owner_name,
    );
    if (preferPlan(row.capexPlan, plan)) {
      row.capexPlan = plan;
      row.capexPending = plan.status === "submitted";
      row.capexInProgress = capexDraftInProgress(plan);
      row.capexAmount = amountOf(plan);
      if (plan.cost_center_icon_key) row.icon_key = plan.cost_center_icon_key;
      if (plan.cost_center_name) row.cost_center_name = plan.cost_center_name;
      if (plan.cost_center_owner_name) {
        row.owner_name = plan.cost_center_owner_name;
      }
    }
  }

  for (const plan of personnelItems) {
    const unit_id = String(plan.unit_id || "");
    const cost_center_id = String(plan.cost_center_id || "");
    if (!unit_id || !cost_center_id) continue;
    const row = ensure(
      unit_id,
      cost_center_id,
      plan.area_id,
      plan.branch ?? plan.unit_id,
      plan.cost_center_name,
      plan.cost_center_icon_key,
      plan.cost_center_owner_name,
    );
    if (preferPlan(row.personnelPlan, plan)) {
      row.personnelPlan = plan;
      row.personnelPending = plan.status === "submitted";
      row.personnelInProgress = personnelDraftInProgress(plan);
      row.personnelHeadcount = headcountOf(plan);
      if (plan.cost_center_icon_key && !row.icon_key) {
        row.icon_key = plan.cost_center_icon_key;
      }
      if (plan.cost_center_name && !row.cost_center_name) {
        row.cost_center_name = plan.cost_center_name;
      }
      if (plan.cost_center_owner_name && !row.owner_name) {
        row.owner_name = plan.cost_center_owner_name;
      }
    }
  }

  const items = Array.from(map.values()).map((row) => ({
    ...row,
    urgency:
      (row.capexPending ? 100 : 0) +
      (row.personnelPending ? 50 : 0) +
      (row.capexPlan?.status === "changes_requested" ? 40 : 0) +
      (row.personnelPlan?.status === "changes_requested" ? 20 : 0) +
      (row.capexInProgress ? 15 : 0) +
      (row.personnelInProgress ? 10 : 0) +
      (row.capexAmount > 0 ? Math.min(row.capexAmount / 1_000_000, 5) : 0),
  }));

  return items.sort((a, b) => {
    if (b.urgency !== a.urgency) return b.urgency - a.urgency;
    if (b.capexAmount !== a.capexAmount) return b.capexAmount - a.capexAmount;
    const byUnit = a.unit_id.localeCompare(b.unit_id);
    if (byUnit !== 0) return byUnit;
    return a.cost_center_id.localeCompare(b.cost_center_id);
  });
}

export type ApprovalPortfolioUnitGroup = {
  unit_id: string;
  /** Ex.: «Filial 01 · Jaraguá do Sul/SC». */
  title: string;
  items: ApprovalPortfolioItem[];
};

/** Agrupa o radar por filial (01 → 02 → demais). */
export function groupApprovalPortfolioByUnit(
  items: ApprovalPortfolioItem[],
): ApprovalPortfolioUnitGroup[] {
  const byUnit = new Map<string, ApprovalPortfolioItem[]>();
  for (const item of items) {
    const unit = normalizeBranchCode(item.unit_id) || String(item.unit_id || "").trim() || "—";
    const list = byUnit.get(unit) ?? [];
    list.push(item);
    byUnit.set(unit, list);
  }

  const known = BUDGET_BRANCHES.map((b) => b.code);
  const ordered = [
    ...known.filter((code) => byUnit.has(code)),
    ...Array.from(byUnit.keys())
      .filter((code) => !known.includes(code as (typeof known)[number]))
      .sort((a, b) => a.localeCompare(b)),
  ];

  return ordered.map((unit_id) => ({
    unit_id,
    title: `Filial ${unit_id} · ${branchCityLabel(unit_id)}`,
    items: byUnit.get(unit_id) ?? [],
  }));
}

/** Aplica totais/nomes da consolidação por CC no portfolio (sem sobrescrever status do plano). */
export function applyConsolidationAmountsToPortfolio(
  items: ApprovalPortfolioItem[],
  groups: CapexConsolidationGroupItem[],
): ApprovalPortfolioItem[] {
  if (!groups.length) return items;
  const byKey = new Map<string, CapexConsolidationGroupItem>();
  for (const g of groups) {
    const unit = String(g.unit_id || "");
    const cc = String(g.cost_center_id || g.code || "");
    if (!unit || !cc) continue;
    byKey.set(pairKey(unit, cc), g);
  }

  return items.map((row) => {
    const g = byKey.get(row.key);
    if (!g) return row;
    const amount = Number(g.total_amount);
    const nextAmount = Number.isFinite(amount) && amount > 0 ? amount : row.capexAmount;
    const name =
      row.cost_center_name ||
      (g.description && g.description !== g.code ? g.description : null);
    return {
      ...row,
      capexAmount: nextAmount,
      cost_center_name: name,
    };
  });
}

export function portfolioPendingCounts(items: ApprovalPortfolioItem[]): {
  centersWithPending: number;
  centersInProgress: number;
  centersTracked: number;
  capexPending: number;
  personnelPending: number;
  capexPendingAmount: number;
} {
  let centersWithPending = 0;
  let centersInProgress = 0;
  let capexPending = 0;
  let personnelPending = 0;
  let capexPendingAmount = 0;
  for (const row of items) {
    if (row.capexPending || row.personnelPending) centersWithPending += 1;
    else if (row.capexInProgress || row.personnelInProgress) centersInProgress += 1;
    if (row.capexPending) {
      capexPending += 1;
      capexPendingAmount += row.capexAmount;
    }
    if (row.personnelPending) personnelPending += 1;
  }
  return {
    centersWithPending,
    centersInProgress,
    centersTracked: items.length,
    capexPending,
    personnelPending,
    capexPendingAmount,
  };
}

/** Converte itens do portfolio CAPEX pendente em shape de gráfico quando não há consolidação. */
export function portfolioToChartItems(
  items: ApprovalPortfolioItem[],
  limit = 12,
): CapexConsolidationGroupItem[] {
  return items
    .filter((i) => i.capexPending && i.capexAmount > 0)
    .slice(0, limit)
    .map((i) => ({
      code: i.cost_center_id,
      description:
        i.cost_center_name?.trim() ||
        `Filial ${i.unit_id} · ${i.cost_center_id}`,
      investment_count: i.capexPlan?.investment_count ?? 0,
      total_amount: String(i.capexAmount),
      unit_id: i.unit_id,
      cost_center_id: i.cost_center_id,
      area_id: i.area_id,
    }));
}

/** Extrai valor do agrupamento por status de plano (ex.: draft / submitted). */
export function amountFromPlanStatusGroups(
  items: CapexConsolidationGroupItem[],
  status: string,
): number {
  const row = items.find((i) => String(i.code || i.plan_status || "") === status);
  if (!row) return 0;
  const n = Number(row.total_amount);
  return Number.isFinite(n) ? n : 0;
}

async function enrichCapexPlans(
  plans: CapexPlan[],
  signal?: AbortSignal,
): Promise<EnrichedCapexPlan[]> {
  return Promise.all(
    plans.map(async (plan) => {
      try {
        const detail = await getCapexReviewDetail(plan.id, signal);
        const active = activeInvestments(detail.investments ?? []);
        return {
          ...plan,
          ...detail,
          investment_count: active.length,
          total_amount: sumEstimatedAmounts(active),
        };
      } catch {
        return { ...plan, investment_count: undefined, total_amount: undefined };
      }
    }),
  );
}

async function listCapexQueueAllStatuses(
  exerciseId: string,
  signal?: AbortSignal,
  extra?: { unit_id?: string; cost_center_id?: string },
): Promise<CapexPlan[]> {
  const pages = await Promise.all(
    APPROVAL_PORTFOLIO_STATUSES.map((status) =>
      listCapexReviewQueue(
        {
          exercise_id: exerciseId,
          status,
          unit_id: extra?.unit_id,
          cost_center_id: extra?.cost_center_id,
          page: 1,
          page_size: 100,
        },
        signal,
      ),
    ),
  );
  return pages.flatMap((p) => p.items ?? []);
}

async function listPersonnelQueueAllStatuses(
  exerciseId: string,
  signal?: AbortSignal,
  extra?: { unit_id?: string; cost_center_id?: string },
): Promise<PersonnelPlan[]> {
  const pages = await Promise.all(
    APPROVAL_PORTFOLIO_STATUSES.map((status) =>
      listPersonnelReviewQueue(
        {
          exercise_id: exerciseId,
          status,
          unit_id: extra?.unit_id,
          cost_center_id: extra?.cost_center_id,
          page: 1,
          page_size: 100,
        },
        signal,
      ),
    ),
  );
  return pages.flatMap((p) => p.items ?? []);
}

export async function fetchApprovalPortfolio(input: {
  exerciseId: string;
  includeCapex: boolean;
  includePersonnel: boolean;
  signal?: AbortSignal;
}): Promise<ApprovalPortfolioItem[]> {
  const [capexRaw, personnelRaw] = await Promise.all([
    input.includeCapex
      ? listCapexQueueAllStatuses(input.exerciseId, input.signal)
      : Promise.resolve([] as CapexPlan[]),
    input.includePersonnel
      ? listPersonnelQueueAllStatuses(input.exerciseId, input.signal)
      : Promise.resolve([] as PersonnelPlan[]),
  ]);

  // Detalhe/valor só para o que exige decisão (evita N+1 em todos os rascunhos).
  const toEnrich = (capexRaw ?? []).filter(
    (p) => p.status === "submitted" || p.status === "changes_requested",
  );
  const enrichedList = input.includeCapex
    ? await enrichCapexPlans(toEnrich, input.signal)
    : [];
  const enrichedById = new Map(enrichedList.map((p) => [p.id, p]));
  const capex = (capexRaw ?? []).map((p) => enrichedById.get(p.id) ?? p);

  return mergeApprovalPortfolio(capex, personnelRaw ?? []);
}

/** Carrega planos do CC (qualquer status) para o workspace. */
export async function fetchApprovalPlansForCostCenter(input: {
  exerciseId: string;
  unitId: string;
  costCenterId: string;
  includeCapex: boolean;
  includePersonnel: boolean;
  signal?: AbortSignal;
}): Promise<ApprovalPortfolioItem | null> {
  const extra = { unit_id: input.unitId, cost_center_id: input.costCenterId };
  const [capexRaw, personnelRaw] = await Promise.all([
    input.includeCapex
      ? listCapexQueueAllStatuses(input.exerciseId, input.signal, extra)
      : Promise.resolve([] as CapexPlan[]),
    input.includePersonnel
      ? listPersonnelQueueAllStatuses(input.exerciseId, input.signal, extra)
      : Promise.resolve([] as PersonnelPlan[]),
  ]);

  const toEnrich = (capexRaw ?? []).filter(
    (p) =>
      p.status === "submitted" ||
      p.status === "changes_requested" ||
      p.status === "draft",
  );
  const enrichedList = input.includeCapex
    ? await enrichCapexPlans(toEnrich, input.signal)
    : [];
  const enrichedById = new Map(enrichedList.map((p) => [p.id, p]));
  const capex = (capexRaw ?? []).map((p) => enrichedById.get(p.id) ?? p);

  const merged = mergeApprovalPortfolio(capex, personnelRaw ?? []);
  return (
    merged.find(
      (i) => i.unit_id === input.unitId && i.cost_center_id === input.costCenterId,
    ) ?? null
  );
}
