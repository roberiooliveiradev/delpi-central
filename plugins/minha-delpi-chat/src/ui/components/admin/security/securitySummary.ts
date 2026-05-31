import type { AdminSecuritySummary } from "../../../../data/api/adminTypes";

export function formatSecurityCount(value: number | undefined): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

export type SecuritySummaryView = {
  blocked: string;
  flagged: string;
  scanned: string;
  totalEvents: string;
};

export function buildSecuritySummaryView(
  summary: AdminSecuritySummary | null | undefined,
): SecuritySummaryView {
  if (!summary) {
    return {
      blocked: "—",
      flagged: "—",
      scanned: "—",
      totalEvents: "—",
    };
  }

  return {
    blocked: formatSecurityCount(summary.blockedCount),
    flagged: formatSecurityCount(summary.flaggedCount),
    scanned: formatSecurityCount(summary.scannedCount),
    totalEvents: formatSecurityCount(summary.totalEvents),
  };
}
