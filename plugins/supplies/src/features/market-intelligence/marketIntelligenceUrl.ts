/** URL persistence for market intelligence filters (PROC-0076 R4).
 *
 * Query contract: ``view``, ``metals``, ``mode``, ``granularity``,
 * ``indicator``, ``fx_kind``, ``ncm``, ``products``, ``direct_ncm``,
 * ``ipp_series``, ``from``, ``to``. Values are allowlist-validated
 * on read — anything outside the contract is ignored, never
 * forwarded upstream.
 *
 * Compatibility:
 * - R3 links ``view=ipp`` / ``view=comex`` resolve to
 *   ``view=indicators`` with the matching ``indicator`` sub-perspective.
 * - R2 links ``instrument=usd-brl`` map to ``view=fx``; a legacy metal
 *   instrument link selects the metal card on ``view=metals``.
 */

import type {
  MarketFxKind,
  MarketGranularity,
} from "./api";

export type MarketPerspective = "metals" | "fx" | "indicators";
export type MarketViewMode = "chart" | "table" | "compare";
export type MarketIndicatorKind = "ipp" | "comex";

export type MarketIntelligenceUrlState = {
  view: MarketPerspective;
  mode: MarketViewMode;
  granularity: MarketGranularity;
  fxKind: MarketFxKind;
  from: string;
  to: string;
  /** Perspective selections — free-form codes validated against the
  catalog (never forwarded unvalidated upstream). */
  metals: string[];
  indicator: MarketIndicatorKind;
  /** Comma-separated allowlisted NCM codes (multi-NCM aggregate). */
  ncm: string;
  /** Comma-separated selected SB1010 product codes (Comex picker). */
  comexProducts: string[];
  /** Comma-separated NCMs entered directly by code — the other half
   * of the Comex selection, independent of product association. */
  comexDirectNcms: string[];
  ippSeries: string;
};

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const INSTRUMENT_CODE = /^[a-z0-9-]{1,64}$/;
const PERSPECTIVES: readonly MarketPerspective[] = [
  "metals",
  "fx",
  "indicators",
];
const MODES: readonly MarketViewMode[] = ["chart", "table", "compare"];
const GRANULARITIES: readonly MarketGranularity[] = [
  "day",
  "week",
  "month",
  "year",
];
const FX_KINDS: readonly MarketFxKind[] = [
  "ptax_closing_sell",
  "ptax_closing_buy",
];
const INDICATORS: readonly MarketIndicatorKind[] = ["ipp", "comex"];
/** R3 perspective values that fold into ``indicators``. */
const LEGACY_INDICATORS: readonly MarketIndicatorKind[] = INDICATORS;

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
  const ncm = (params.get("ncm") ?? "")
    .split(",")
    .map((code) => code.trim())
    .filter((code) => /^[0-9]{8}$/.test(code))
    .join(",");
  const comexProducts = (params.get("products") ?? "")
    .split(",")
    .map((code) => code.trim())
    .filter((code) => /^[A-Za-z0-9_.\-/]{1,64}$/.test(code));
  const comexDirectNcms = (params.get("direct_ncm") ?? "")
    .split(",")
    .map((code) => code.trim())
    .filter((code) => /^[0-9]{8}$/.test(code));
  const ippSeries = (params.get("ipp_series") ?? "").trim();
  const from = (params.get("from") ?? "").trim();
  const to = (params.get("to") ?? "").trim();
  const legacyInstrument = (params.get("instrument") ?? "").trim();
  const rawView = (params.get("view") ?? "").trim();
  const metals = (params.get("metals") ?? "")
    .split(",")
    .map((code) => code.trim())
    .filter((code) => INSTRUMENT_CODE.test(code));

  let view = parseAllowlisted(rawView, PERSPECTIVES);
  let indicator = parseAllowlisted(
    params.get("indicator"),
    INDICATORS,
  );
  // R3 compatibility — a legacy perspective keeps its sub-selection.
  if (
    !view &&
    LEGACY_INDICATORS.includes(rawView as MarketIndicatorKind)
  ) {
    view = "indicators";
    indicator = indicator ?? (rawView as MarketIndicatorKind);
  }
  if (!view && legacyInstrument) {
    if (legacyInstrument === "usd-brl") view = "fx";
    else if (INSTRUMENT_CODE.test(legacyInstrument)) {
      view = "metals";
      if (!metals.includes(legacyInstrument)) {
        metals.push(legacyInstrument);
      }
    }
  }
  return {
    view: view ?? undefined,
    mode: parseAllowlisted(params.get("mode"), MODES) ?? undefined,
    granularity:
      parseAllowlisted(params.get("granularity"), GRANULARITIES) ?? undefined,
    fxKind: parseAllowlisted(params.get("fx_kind"), FX_KINDS) ?? undefined,
    indicator: indicator ?? undefined,
    metals: metals.length ? metals : undefined,
    ncm: ncm || undefined,
    comexProducts: comexProducts.length ? comexProducts : undefined,
    comexDirectNcms: comexDirectNcms.length
      ? comexDirectNcms
      : undefined,
    ippSeries: INSTRUMENT_CODE.test(ippSeries) ? ippSeries : undefined,
    from: ISO_DATE.test(from) ? from : undefined,
    to: ISO_DATE.test(to) ? to : undefined,
  };
}

export function writeMarketIntelligenceToUrl(
  state: MarketIntelligenceUrlState,
): void {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams(window.location.search);
  // Legacy R2/R3 params are superseded — never re-emitted.
  params.delete("instrument");
  params.delete("currency");
  if (state.view) params.set("view", state.view);
  else params.delete("view");
  if (state.mode) params.set("mode", state.mode);
  else params.delete("mode");
  if (state.granularity) params.set("granularity", state.granularity);
  else params.delete("granularity");
  if (state.metals.length) params.set("metals", state.metals.join(","));
  else params.delete("metals");
  if (state.indicator) params.set("indicator", state.indicator);
  else params.delete("indicator");
  if (state.fxKind) params.set("fx_kind", state.fxKind);
  else params.delete("fx_kind");
  if (state.ncm) params.set("ncm", state.ncm);
  else params.delete("ncm");
  if (state.comexProducts.length)
    params.set("products", state.comexProducts.join(","));
  else params.delete("products");
  if (state.comexDirectNcms.length)
    params.set("direct_ncm", state.comexDirectNcms.join(","));
  else params.delete("direct_ncm");
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
