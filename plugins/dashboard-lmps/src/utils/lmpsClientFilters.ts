import type { LmpsDashboardSummary } from "../api/lmpApi";
import type { LmpDashboardItem, LmpListingKind } from "../types/lmp";

export type LmpsMultiFilterState = {
  branches: string[];
  listingTypes: string[];
  statuses: string[];
};

const LISTING_TYPE_TO_KIND: Record<string, LmpListingKind> = {
  LMP: "LMP",
  Amostra: "AMOSTRA",
  Outro: "OUTRO",
};

export function needsClientSideFilter(filters: LmpsMultiFilterState): boolean {
  return (
    filters.branches.length > 1 ||
    filters.listingTypes.length > 1 ||
    filters.statuses.length > 1
  );
}

export function resolveLmpsApiFilters(filters: LmpsMultiFilterState) {
  return {
    branch: filters.branches.length === 1 ? filters.branches[0] : undefined,
    listing_type:
      filters.listingTypes.length === 1 ? filters.listingTypes[0] : "Todos",
    status: filters.statuses.length === 1 ? filters.statuses[0] : "Todos",
  };
}

export function filterLmpsDashboardItems(
  items: LmpDashboardItem[],
  filters: LmpsMultiFilterState
): LmpDashboardItem[] {
  const { branches, listingTypes, statuses } = filters;

  if (branches.length === 0 && listingTypes.length === 0 && statuses.length === 0) {
    return items;
  }

  const listingKinds = listingTypes.map(
    (value) => LISTING_TYPE_TO_KIND[value] ?? value.toUpperCase()
  );

  return items.filter((item) => {
    if (branches.length > 0 && !branches.includes(String(item.branch ?? "").trim())) {
      return false;
    }

    if (
      listingKinds.length > 0 &&
      !listingKinds.includes(String(item.listing_kind ?? "").trim() as LmpListingKind)
    ) {
      return false;
    }

    if (statuses.length > 0 && !statuses.includes(String(item.status ?? "").trim())) {
      return false;
    }

    return true;
  });
}

export function computeLmpsSummaryFromItems(
  items: LmpDashboardItem[],
  fallback?: LmpsDashboardSummary | null
): LmpsDashboardSummary {
  const total = items.length;
  const onTime = items.filter((item) => item.status === "Pontual").length;
  const avgLead =
    total === 0
      ? 0
      : items.reduce((sum, item) => sum + (item.lead_time_util ?? 0), 0) / total;

  return {
    total_lmps: total,
    total_items: total,
    percent_dentro_prazo: total === 0 ? 0 : (onTime / total) * 100,
    avg_lead_time: avgLead,
    goal_label: fallback?.goal_label,
    comparable_goal: fallback?.comparable_goal,
    target: fallback?.target,
    has_goal: fallback?.has_goal,
  };
}

export function hasActiveLmpsFilters(filters: LmpsMultiFilterState): boolean {
  return (
    filters.branches.length > 0 ||
    filters.listingTypes.length > 0 ||
    filters.statuses.length > 0
  );
}
