/** Shared display helpers for the market-intelligence panels
 * (PROC-0076 R5.S2) — pure formatting/label lookups against the
 * feature content layer. No business math lives here: every metric
 * stays BFF-computed, these helpers only render it.
 */

import { MARKET_INTELLIGENCE_CONTENT } from "./content";

export function parsePointValue(raw: string | null): number | null {
  if (raw === null || raw === undefined) return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatMarketDecimal(raw: string | null | undefined): string {
  if (raw === null || raw === undefined) return "—";
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) return "—";
  return parsed.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

export function formatMarketPercent(raw: string | null | undefined): string {
  if (raw === null || raw === undefined) return "—";
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) return "—";
  const sign = parsed > 0 ? "+" : "";
  return `${sign}${parsed.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`;
}

export function marketCoverageLabel(coverage: string | undefined): string {
  if (!coverage) return "—";
  return (
    MARKET_INTELLIGENCE_CONTENT.table.coverageLabels[coverage] ?? coverage
  );
}

export function marketDataStatusBadgeVariant(
  status: string | undefined,
): "success" | "warning" | "danger" | "info" | "neutral" {
  if (status === "ok") return "success";
  if (status === "partial") return "warning";
  if (status === "no_data") return "neutral";
  return "info";
}

export function marketUnavailableReasonLabel(
  reason: string | null | undefined,
): string {
  const states = MARKET_INTELLIGENCE_CONTENT.states;
  switch (reason) {
    case "provider_unavailable":
      return states.providerUnavailable;
    case "feed_failed":
      return states.feedFailed;
    case "feed_disabled":
      return states.feedDisabled;
    case "feed_not_collected":
      return states.feedNotCollected;
    case "window_empty":
      return states.windowEmpty;
    case "granularity_not_supported":
      return states.granularityNotSupported;
    case "source_use_pending":
      return states.sourceUsePending;
    default:
      return states.moduleUnavailable;
  }
}
