import {
  parsePeriodPresetId,
  type PeriodPresetId,
} from "./periodPreset";

export type OverviewFilterUrlState = {
  branch: string;
  from: string;
  to: string;
  period: PeriodPresetId | null;
};

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

function readSearchParams(): URLSearchParams {
  if (typeof window === "undefined") return new URLSearchParams();
  return new URLSearchParams(window.location.search);
}

export function readOverviewFiltersFromUrl(): Partial<OverviewFilterUrlState> {
  const params = readSearchParams();
  const branch = (params.get("branch") ?? "").trim();
  const from = (params.get("from") ?? "").trim();
  const to = (params.get("to") ?? "").trim();
  const period = parsePeriodPresetId(params.get("period"));
  return {
    branch: branch || "",
    from: ISO_DATE.test(from) ? from : "",
    to: ISO_DATE.test(to) ? to : "",
    period,
  };
}

export function writeOverviewFiltersToUrl(state: OverviewFilterUrlState): void {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams(window.location.search);
  if (state.branch) params.set("branch", state.branch);
  else params.delete("branch");
  if (state.from) params.set("from", state.from);
  else params.delete("from");
  if (state.to) params.set("to", state.to);
  else params.delete("to");
  if (state.period && state.period !== "custom") params.set("period", state.period);
  else params.delete("period");

  const qs = params.toString();
  const nextUrl = `${window.location.pathname}${qs ? `?${qs}` : ""}${window.location.hash}`;
  window.history.replaceState(window.history.state, "", nextUrl);
}

export function buildOverviewQueryString(state: OverviewFilterUrlState): string {
  const params = new URLSearchParams();
  if (state.branch) params.set("branch", state.branch);
  if (state.from) params.set("from", state.from);
  if (state.to) params.set("to", state.to);
  if (state.period && state.period !== "custom") params.set("period", state.period);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}
