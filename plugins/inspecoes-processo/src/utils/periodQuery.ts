import { getThisMonthRange, parseIsoDate } from "./dateRange";

export type DashboardPeriod =
  | { mode: "all" }
  | { mode: "range"; startDate: string; endDate: string };

function currentSearch(search?: string): string {
  return search ?? (typeof window !== "undefined" ? window.location.search : "");
}

export function periodFromSearch(search?: string): DashboardPeriod {
  const params = new URLSearchParams(currentSearch(search));
  if (params.get("period") === "all") {
    return { mode: "all" };
  }
  const startDate = params.get("start_date")?.trim() ?? "";
  const endDate = params.get("end_date")?.trim() ?? "";
  if (parseIsoDate(startDate) && parseIsoDate(endDate)) {
    return { mode: "range", startDate, endDate };
  }
  const fallback = getThisMonthRange();
  return { mode: "range", startDate: fallback.startDate, endDate: fallback.endDate };
}

export function syncPeriodInUrl(period: DashboardPeriod): void {
  if (typeof window === "undefined") return;

  const url = new URL(window.location.href);
  if (period.mode === "all") {
    url.searchParams.delete("start_date");
    url.searchParams.delete("end_date");
    url.searchParams.set("period", "all");
  } else {
    url.searchParams.delete("period");
    url.searchParams.set("start_date", period.startDate);
    url.searchParams.set("end_date", period.endDate);
  }

  const next = `${url.pathname}${url.search}${url.hash}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (next !== current) {
    window.history.replaceState(null, "", next);
  }
}
