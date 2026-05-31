import type { AdminAuditLog } from "../../../../data/api/adminTypes";

export type AuditSummaryView = {
  total: string;
  pageEvents: string;
  uniqueActions: string;
  uniqueUsers: string;
  timelineDays: string;
};

function formatCount(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(Math.max(0, value));
}

function countUnique(values: Array<string | null | undefined>): number {
  return new Set(values.filter(Boolean)).size;
}

export function computeAuditSummary(
  logs: AdminAuditLog[],
  total: number | undefined,
  timelineDayCount: number,
): AuditSummaryView {
  const resolvedTotal = typeof total === "number" ? total : logs.length;

  return {
    total: formatCount(resolvedTotal),
    pageEvents: formatCount(logs.length),
    uniqueActions: formatCount(countUnique(logs.map((log) => log.action))),
    uniqueUsers: formatCount(countUnique(logs.map((log) => log.userId))),
    timelineDays: formatCount(timelineDayCount),
  };
}
