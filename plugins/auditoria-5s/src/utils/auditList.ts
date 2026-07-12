import type { AuditArea, AuditListItem } from "../api/audit5sApi";
import { auditNeedsNcAttention } from "../constants/audit5s";

export function formatAuditDate(value: string): string {
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}

export function scorePercentClass(
  value: number | null | undefined,
  status?: string,
): string {
  if (status && auditNeedsNcAttention(status)) {
    return "a5s-score-pill--attention";
  }
  if (value == null) return "a5s-score-pill--empty";
  if (value >= 80) return "a5s-score-pill--high";
  if (value >= 60) return "a5s-score-pill--mid";
  return "a5s-score-pill--low";
}

export type AuditListStats = {
  total: number;
  completed: number;
  inProgress: number;
  closed: number;
};

export function computeAuditListStats(items: AuditListItem[]): AuditListStats {
  let completed = 0;
  let inProgress = 0;
  let closed = 0;

  for (const item of items) {
    switch (item.status) {
      case "draft":
        inProgress += 1;
        break;
      case "evaluation_complete":
      case "nc_in_progress":
        completed += 1;
        break;
      case "closed":
        closed += 1;
        break;
      default:
        inProgress += 1;
    }
  }

  return {
    total: items.length,
    completed,
    inProgress,
    closed,
  };
}

export function percentOf(value: number, total: number): number {
  if (total <= 0) return 0;
  return Math.round((value / total) * 100);
}

export type AuditListFilters = {
  search: string;
  areaId: string;
  status: string;
  periodStart: string;
  periodEnd: string;
};

export const EMPTY_AUDIT_LIST_FILTERS: AuditListFilters = {
  search: "",
  areaId: "",
  status: "",
  periodStart: "",
  periodEnd: "",
};

export function filterAuditList(
  items: AuditListItem[],
  filters: AuditListFilters,
  areaNameById: Map<string, string>,
): AuditListItem[] {
  const search = filters.search.trim().toLowerCase();

  return items.filter((item) => {
    if (filters.areaId) {
      const areaName = areaNameById.get(filters.areaId);
      if (areaName && item.area_name !== areaName) {
        return false;
      }
    }

    if (filters.status && item.status !== filters.status) {
      return false;
    }

    if (filters.periodStart && item.audit_date < filters.periodStart) {
      return false;
    }

    if (filters.periodEnd && item.audit_date > filters.periodEnd) {
      return false;
    }

    if (!search) {
      return true;
    }

    const haystack = [
      item.audit_code,
      item.area_name,
      item.area_responsible,
      item.shift,
    ]
      .join(" ")
      .toLowerCase();

    return haystack.includes(search);
  });
}

export function buildAreaNameMap(areas: AuditArea[]): Map<string, string> {
  return new Map(areas.map((area) => [area.id, area.name]));
}
