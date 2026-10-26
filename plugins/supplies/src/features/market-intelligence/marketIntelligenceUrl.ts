/** URL persistence for market intelligence filters (PROC-0076).

Query contract: ``instrument``, ``currency``, ``granularity``,
``fx_kind``, ``from``, ``to``. Values are allowlist-validated on read —
anything outside the contract is ignored, never forwarded upstream.
*/

import type {
  MarketCurrency,
  MarketFxKind,
  MarketGranularity,
} from "./api";

export type MarketIntelligenceUrlState = {
  instrument: string;
  currency: MarketCurrency;
  granularity: MarketGranularity;
  fxKind: MarketFxKind;
  from: string;
  to: string;
};

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const CURRENCIES: readonly MarketCurrency[] = ["USD", "BRL"];
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
  const instrument = (params.get("instrument") ?? "").trim();
  const from = (params.get("from") ?? "").trim();
  const to = (params.get("to") ?? "").trim();
  return {
    instrument: instrument || undefined,
    currency: parseAllowlisted(params.get("currency"), CURRENCIES) ?? undefined,
    granularity:
      parseAllowlisted(params.get("granularity"), GRANULARITIES) ?? undefined,
    fxKind: parseAllowlisted(params.get("fx_kind"), FX_KINDS) ?? undefined,
    from: ISO_DATE.test(from) ? from : undefined,
    to: ISO_DATE.test(to) ? to : undefined,
  };
}

export function writeMarketIntelligenceToUrl(
  state: MarketIntelligenceUrlState,
): void {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams(window.location.search);
  if (state.instrument) params.set("instrument", state.instrument);
  else params.delete("instrument");
  if (state.currency) params.set("currency", state.currency);
  else params.delete("currency");
  if (state.granularity) params.set("granularity", state.granularity);
  else params.delete("granularity");
  if (state.fxKind) params.set("fx_kind", state.fxKind);
  else params.delete("fx_kind");
  if (state.from) params.set("from", state.from);
  else params.delete("from");
  if (state.to) params.set("to", state.to);
  else params.delete("to");

  const qs = params.toString();
  const nextUrl = `${window.location.pathname}${qs ? `?${qs}` : ""}${window.location.hash}`;
  window.history.replaceState(window.history.state, "", nextUrl);
}
