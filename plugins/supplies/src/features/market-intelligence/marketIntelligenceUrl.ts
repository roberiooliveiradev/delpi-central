/** URL persistence for market intelligence filters (PROC-0076 R3).

Query contract: ``view``, ``mode``, ``granularity``, ``fx_kind``,
``ncm``, ``ipp_series``, ``from``, ``to``. Values are
allowlist-validated on read — anything outside the contract is
ignored, never forwarded upstream.

Legacy links (R2) keep resolving: ``instrument=usd-brl`` maps to
``view=fx``; metal instruments no longer drive a perspective, so a
legacy metal link falls back to the catalog-driven default view.
*/

import type {
  MarketFxKind,
  MarketGranularity,
} from "./api";

export type MarketPerspective = "ipp" | "comex" | "fx";
export type MarketViewMode = "chart" | "table";

export type MarketIntelligenceUrlState = {
  view: MarketPerspective;
  mode: MarketViewMode;
  granularity: MarketGranularity;
  fxKind: MarketFxKind;
  from: string;
  to: string;
  /** Perspective selections — free-form codes validated against the
  catalog (never forwarded unvalidated upstream). */
  ncm: string;
  ippSeries: string;
};

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const PERSPECTIVES: readonly MarketPerspective[] = ["ipp", "comex", "fx"];
const MODES: readonly MarketViewMode[] = ["chart", "table"];
const GRANULARITIES: readonly MarketGranularity[] = ["day", "month", "year"];
const FX_KINDS: readonly MarketFxKind[] = [
  "ptax_closing_sell",
  "ptax_closing_buy",
];

function readSearchParams(): URLSearchParams {
  if (typeof window === "undefined") return new URLSearchParams();
  return new URLSearchParams(window.location.search);
}

function parseAllowlisted<T extends string>(
  raw: string | null,
  allowed: readonly T[],
): T | null {
  if (!raw) return null;
  const value = raw.trim() as T;
  return allowed.includes(value) ? value : null;
}

export function readMarketIntelligenceFromUrl(): Partial<MarketIntelligenceUrlState> {
  const params = readSearchParams();
  const ncm = (params.get("ncm") ?? "").trim();
  const ippSeries = (params.get("ipp_series") ?? "").trim();
  const from = (params.get("from") ?? "").trim();
  const to = (params.get("to") ?? "").trim();
  const legacyInstrument = (params.get("instrument") ?? "").trim();
  const view =
    parseAllowlisted(params.get("view"), PERSPECTIVES) ??
    // R2 legacy link: the fx instrument selected the PTAX perspective.
    (legacyInstrument === "usd-brl" ? "fx" : null);
  return {
    view: view ?? undefined,
    mode: parseAllowlisted(params.get("mode"), MODES) ?? undefined,
    granularity:
      parseAllowlisted(params.get("granularity"), GRANULARITIES) ?? undefined,
    fxKind: parseAllowlisted(params.get("fx_kind"), FX_KINDS) ?? undefined,
    ncm: /^[0-9]{8}$/.test(ncm) ? ncm : undefined,
    ippSeries: /^[a-z0-9-]{1,64}$/.test(ippSeries)
      ? ippSeries
      : undefined,
    from: ISO_DATE.test(from) ? from : undefined,
    to: ISO_DATE.test(to) ? to : undefined,
  };
}

export function writeMarketIntelligenceToUrl(
  state: MarketIntelligenceUrlState,
): void {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams(window.location.search);
  // Legacy R2 params are superseded by `view` — never re-emitted.
  params.delete("instrument");
  params.delete("currency");
  if (state.view) params.set("view", state.view);
  else params.delete("view");
  if (state.mode) params.set("mode", state.mode);
  else params.delete("mode");
  if (state.granularity) params.set("granularity", state.granularity);
  else params.delete("granularity");
  if (state.fxKind) params.set("fx_kind", state.fxKind);
  else params.delete("fx_kind");
  if (state.ncm) params.set("ncm", state.ncm);
  else params.delete("ncm");
  if (state.ippSeries) params.set("ipp_series", state.ippSeries);
  else params.delete("ipp_series");
  if (state.from) params.set("from", state.from);
  else params.delete("from");
  if (state.to) params.set("to", state.to);
  else params.delete("to");

  const qs = params.toString();
  const nextUrl = `${window.location.pathname}${qs ? `?${qs}` : ""}${window.location.hash}`;
  window.history.replaceState(window.history.state, "", nextUrl);
}
