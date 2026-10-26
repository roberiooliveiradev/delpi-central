/** Filter state for the market intelligence page (PROC-0076).

Merges URL state with catalog constraints: instrument, currency and
granularity are only emitted when allowed by the selected instrument —
invalid combinations are normalized locally so the BFF never receives a
guaranteed-422 request.
*/

import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  MarketCurrency,
  MarketFxKind,
  MarketGranularity,
  MarketInstrumentFilter,
} from "./api";
import {
  readMarketIntelligenceFromUrl,
  writeMarketIntelligenceToUrl,
  type MarketIntelligenceUrlState,
} from "./marketIntelligenceUrl";

const DEFAULT_FX_KIND: MarketFxKind = "ptax_closing_sell";
const DEFAULT_CURRENCY: MarketCurrency = "USD";
const DEFAULT_GRANULARITY: MarketGranularity = "month";

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function defaultRange(): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setMonth(from.getMonth() - 12);
  return { from: isoDate(from), to: isoDate(to) };
}

function normalizeForInstrument(
  state: MarketIntelligenceUrlState,
  instrument: MarketInstrumentFilter | undefined,
): MarketIntelligenceUrlState {
  if (!instrument) return state;
  const next = { ...state };
  if (!instrument.currencies.includes(next.currency)) {
    next.currency = instrument.currencies[0] ?? DEFAULT_CURRENCY;
  }
  if (!instrument.granularities.includes(next.granularity)) {
    next.granularity = instrument.granularities[0] ?? DEFAULT_GRANULARITY;
  }
  return next;
}

export function useMarketIntelligenceFilters(
  instruments: readonly MarketInstrumentFilter[],
  defaultInstrument: string | null,
) {
  const initial = useMemo(() => {
    const fromUrl = readMarketIntelligenceFromUrl();
    const range = defaultRange();
    return {
      instrument: fromUrl.instrument ?? "",
      currency: fromUrl.currency ?? DEFAULT_CURRENCY,
      granularity: fromUrl.granularity ?? DEFAULT_GRANULARITY,
      fxKind: fromUrl.fxKind ?? DEFAULT_FX_KIND,
      from: fromUrl.from ?? range.from,
      to: fromUrl.to ?? range.to,
    } satisfies MarketIntelligenceUrlState;
  }, []);

  const [state, setState] = useState<MarketIntelligenceUrlState>(initial);

  const instrument = useMemo(
    () =>
      instruments.find((entry) => entry.code === state.instrument) ??
      instruments.find((entry) => entry.code === defaultInstrument),
    [instruments, state.instrument, defaultInstrument],
  );

  const effectiveState = useMemo(
    () =>
      normalizeForInstrument(
        { ...state, instrument: instrument?.code ?? "" },
        instrument,
      ),
    [state, instrument],
  );

  const patch = useCallback(
    (update: Partial<MarketIntelligenceUrlState>) => {
      setState((prev) => {
        const next = { ...prev, ...update };
        return normalizeForInstrument(
          next,
          instruments.find((entry) => entry.code === next.instrument),
        );
      });
    },
    [instruments],
  );

  // URL persistence (F5 + shareable links).
  useEffect(() => {
    writeMarketIntelligenceToUrl(effectiveState);
  }, [effectiveState]);

  // Back/forward navigation re-reads the query string.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const onPopState = () => {
      const fromUrl = readMarketIntelligenceFromUrl();
      setState((prev) => ({
        ...prev,
        instrument: fromUrl.instrument ?? prev.instrument,
        currency: fromUrl.currency ?? prev.currency,
        granularity: fromUrl.granularity ?? prev.granularity,
        fxKind: fromUrl.fxKind ?? prev.fxKind,
        from: fromUrl.from ?? prev.from,
        to: fromUrl.to ?? prev.to,
      }));
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const apiParams = useMemo(
    () => ({
      instrument: effectiveState.instrument,
      currency: effectiveState.currency,
      fx_kind: effectiveState.fxKind,
      date_from: effectiveState.from,
      date_to: effectiveState.to,
    }),
    [effectiveState],
  );

  return {
    state: effectiveState,
    instrument,
    apiParams,
    setInstrument: (code: string) => patch({ instrument: code }),
    setCurrency: (currency: MarketCurrency) => patch({ currency }),
    setGranularity: (granularity: MarketGranularity) =>
      patch({ granularity }),
    setFxKind: (fxKind: MarketFxKind) => patch({ fxKind }),
    setFrom: (from: string) => patch({ from }),
    setTo: (to: string) => patch({ to }),
  };
}
