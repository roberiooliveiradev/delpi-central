/** Filter state for the market intelligence page (PROC-0076 R3).

One active perspective at a time: ``view`` selects the source
(IBGE IPP / Comex / PTAX), ``mode`` selects the analysis panel
(chart/table). URL state is merged with catalog constraints —
``day`` granularity only exists for FX, invalid combinations are
normalized locally so the BFF never receives a guaranteed-422 request.
*/

import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  MarketFxKind,
  MarketGranularity,
} from "./api";
import {
  readMarketIntelligenceFromUrl,
  writeMarketIntelligenceToUrl,
  type MarketIntelligenceUrlState,
  type MarketPerspective,
  type MarketViewMode,
} from "./marketIntelligenceUrl";

const DEFAULT_FX_KIND: MarketFxKind = "ptax_closing_sell";
const DEFAULT_GRANULARITY: MarketGranularity = "month";
const DEFAULT_MODE: MarketViewMode = "chart";

/** Only FX has a daily series — IPP/Comex are monthly sources. */
function normalizeGranularity(
  view: MarketPerspective | "",
  granularity: MarketGranularity,
): MarketGranularity {
  if (view !== "fx" && granularity === "day") return "month";
  return granularity;
}

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function defaultRange(): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setMonth(from.getMonth() - 12);
  return { from: isoDate(from), to: isoDate(to) };
}

export function useMarketIntelligenceFilters(
  defaultView: MarketPerspective,
) {
  const initial = useMemo(() => {
    const fromUrl = readMarketIntelligenceFromUrl();
    const range = defaultRange();
    const view = fromUrl.view ?? "";
    const granularity = normalizeGranularity(
      view,
      fromUrl.granularity ?? DEFAULT_GRANULARITY,
    );
    return {
      view,
      mode: fromUrl.mode ?? DEFAULT_MODE,
      granularity,
      fxKind: fromUrl.fxKind ?? DEFAULT_FX_KIND,
      ncm: fromUrl.ncm ?? "",
      ippSeries: fromUrl.ippSeries ?? "",
      from: fromUrl.from ?? range.from,
      to: fromUrl.to ?? range.to,
    } satisfies Omit<MarketIntelligenceUrlState, "view"> & {
      view: MarketPerspective | "";
    };
  }, []);

  const [state, setState] =
    useState<Omit<MarketIntelligenceUrlState, "view"> & {
      view: MarketPerspective | "";
    }>(initial);

  /** URL selection wins; otherwise the catalog-driven default view
  (first perspective with usable observations). */
  const effectiveState = useMemo<MarketIntelligenceUrlState>(
    () => ({
      ...state,
      view: state.view || defaultView,
      granularity: normalizeGranularity(
        state.view || defaultView,
        state.granularity,
      ),
    }),
    [state, defaultView],
  );

  const patch = useCallback(
    (
      update: Partial<
        Omit<MarketIntelligenceUrlState, "view"> & {
          view: MarketPerspective | "";
        }
      >,
    ) => {
      setState((prev) => {
        const next = { ...prev, ...update };
        next.granularity = normalizeGranularity(
          next.view || prev.view || "fx",
          next.granularity,
        );
        return next;
      });
    },
    [],
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
        view: fromUrl.view ?? prev.view,
        mode: fromUrl.mode ?? prev.mode,
        granularity: normalizeGranularity(
          fromUrl.view ?? prev.view ?? "fx",
          fromUrl.granularity ?? prev.granularity,
        ),
        fxKind: fromUrl.fxKind ?? prev.fxKind,
        ncm: fromUrl.ncm ?? prev.ncm,
        ippSeries: fromUrl.ippSeries ?? prev.ippSeries,
        from: fromUrl.from ?? prev.from,
        to: fromUrl.to ?? prev.to,
      }));
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  return {
    state: effectiveState,
    setView: (view: MarketPerspective) => patch({ view }),
    setMode: (mode: MarketViewMode) => patch({ mode }),
    setGranularity: (granularity: MarketGranularity) =>
      patch({ granularity }),
    setFxKind: (fxKind: MarketFxKind) => patch({ fxKind }),
    setNcm: (ncm: string) => patch({ ncm }),
    setIppSeries: (ippSeries: string) => patch({ ippSeries }),
    setFrom: (from: string) => patch({ from }),
    setTo: (to: string) => patch({ to }),
  };
}
