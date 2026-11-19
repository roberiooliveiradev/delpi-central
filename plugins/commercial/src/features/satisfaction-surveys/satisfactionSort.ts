import type {
  SatisfactionCampaign,
  SatisfactionCampaignStatus,
} from "../../types/satisfactionSurvey";

/**
 * Ordenação em memória da lista de campanhas (tabela e cards compartilham
 * o mesmo estado — sem persistência). Sem chave, a ordem é a que
 * `filterCampaigns` devolve (início mais recente primeiro).
 */
export type CampaignSortKey =
  | "name"
  | "period"
  | "status"
  | "participants"
  | "responded"
  | "response_rate";

export type CampaignSortDirection = "asc" | "desc";

export type CampaignSortState = {
  sortKey: CampaignSortKey | null;
  sortDirection: CampaignSortDirection;
};

export const EMPTY_CAMPAIGN_SORT: CampaignSortState = {
  sortKey: null,
  sortDirection: "asc",
};

export const CAMPAIGN_SORT_KEYS: readonly CampaignSortKey[] = [
  "name",
  "period",
  "status",
  "participants",
  "responded",
  "response_rate",
];

export function isCampaignSortKey(value: string): value is CampaignSortKey {
  return (CAMPAIGN_SORT_KEYS as readonly string[]).includes(value);
}

/** Ciclo de vida aprovado: Agendada → Aberta → Encerrada. */
const STATUS_ORDER: Record<SatisfactionCampaignStatus, number> = {
  scheduled: 0,
  open: 1,
  closed: 2,
};

function compareByKey(
  sortKey: CampaignSortKey,
  left: SatisfactionCampaign,
  right: SatisfactionCampaign,
): number {
  switch (sortKey) {
    case "name":
      return left.name.localeCompare(right.name, "pt-BR", {
        sensitivity: "base",
        numeric: true,
      });
    case "period":
      return Date.parse(left.starts_at) - Date.parse(right.starts_at);
    case "status":
      return STATUS_ORDER[left.status] - STATUS_ORDER[right.status];
    case "participants":
      return left.counts.participants - right.counts.participants;
    case "responded":
      return left.counts.responded - right.counts.responded;
    case "response_rate":
      return (left.response_rate ?? 0) - (right.response_rate ?? 0);
  }
}

/**
 * Aplica a ordenação escolhida sobre as linhas já filtradas.
 * `response_rate` vazio (`null`) fica sempre por último, nas duas direções.
 */
export function sortCampaigns(
  rows: readonly SatisfactionCampaign[],
  sortKey: CampaignSortKey | null,
  sortDirection: CampaignSortDirection,
): SatisfactionCampaign[] {
  if (!sortKey || !isCampaignSortKey(sortKey)) return rows.slice();

  const direction = sortDirection === "desc" ? -1 : 1;
  return rows.slice().sort((left, right) => {
    if (sortKey === "response_rate") {
      if (left.response_rate == null && right.response_rate == null) return 0;
      if (left.response_rate == null) return 1;
      if (right.response_rate == null) return -1;
    }
    return compareByKey(sortKey, left, right) * direction;
  });
}

/** Clique num critério: mesma chave inverte a direção; chave nova começa ascendente. */
export function nextCampaignSortState(
  current: CampaignSortState,
  nextKey: CampaignSortKey,
): CampaignSortState {
  if (current.sortKey === nextKey) {
    return {
      sortKey: nextKey,
      sortDirection: current.sortDirection === "asc" ? "desc" : "asc",
    };
  }
  return { sortKey: nextKey, sortDirection: "asc" };
}
