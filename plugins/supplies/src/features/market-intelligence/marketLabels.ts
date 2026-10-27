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

/** pt-BR date — full ISO dates/datetimes become `27/10/2026`; month
 * competences (`2026-10`) become `10/2026`; anything else is passed
 * through verbatim (e.g. ISO week `2026-W43`). Never slices an ISO
 * string blindly: parsing failures fall back to the raw value. */
export function formatMarketDate(raw: string | null | undefined): string {
  if (!raw) return "—";
  const text = String(raw).trim();
  const dayMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  if (dayMatch) return `${dayMatch[3]}/${dayMatch[2]}/${dayMatch[1]}`;
  const monthMatch = /^(\d{4})-(\d{2})$/.exec(text);
  if (monthMatch) return `${monthMatch[2]}/${monthMatch[1]}`;
  const weekMatch = /^(\d{4})-W(\d{2})$/.exec(text);
  if (weekMatch) return `Semana ${weekMatch[2]}/${weekMatch[1]}`;
  const stamp = new Date(text);
  if (!Number.isNaN(stamp.getTime())) {
    return stamp.toLocaleDateString("pt-BR");
  }
  return text;
}

/** pt-BR datetime — `27/10/2026 às 04:48`. The instant is parsed by
 * `Date` (never string-sliced) and rendered in the platform display
 * locale. */
export function formatMarketDateTime(
  raw: string | null | undefined,
): string {
  if (!raw) return "—";
  const stamp = new Date(String(raw));
  if (Number.isNaN(stamp.getTime())) return formatMarketDate(raw);
  return `${stamp.toLocaleDateString("pt-BR")} às ${stamp.toLocaleTimeString(
    "pt-BR",
    { hour: "2-digit", minute: "2-digit" },
  )}`;
}

/** Ingestion run outcome codes → pt-BR labels — internal statuses are
 * never shown raw (R5.S3). */
export function marketRunOutcomeLabel(
  outcome: string | null | undefined,
): string {
  if (!outcome) return "—";
  return (
    MARKET_INTELLIGENCE_CONTENT.statusCards.runOutcome[outcome] ?? outcome
  );
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
