/** Filter state for the market intelligence page (PROC-0076 R4).

One active perspective at a time: ``view`` selects the perspective
(Metals / FX / Indicators), ``mode`` selects the analysis panel
(chart/table/compare). URL state is merged with catalog constraints —
``day|week`` only exist where a daily source exists (FX; metals once
a homologated daily source ships), and ``compare`` only applies to
the multi-instrument metals perspective. Invalid combinations are
normalized locally so the BFF never receives a guaranteed-422
request.
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
const DEFAULT_INDICATOR: MarketIntelligenceUrlState["indicator"] = "ipp";

/** Only monthly sources reject ``day|week`` — IPP/Comex are monthly;
 * the metals contract already accepts daily/weekly granularity
 * (V006) and the FX series is daily. The UI still disables
 * frequencies the catalog doesn't advertise, so an out-of-contract
 * URL value reaches an honest BFF validation, not a silent rewrite. */
function normalizeGranularity(
  view: MarketPerspective | "",
  granularity: MarketGranularity,
): MarketGranularity {
  if (
    view === "indicators" &&
    (granularity === "day" || granularity === "week")
  ) {
    return "month";
  }
  return granularity;
}

/** ``compare`` requires ≥2 compatible series — exclusive to the
 * metals multi-instrument perspective. */
function normalizeMode(
  view: MarketPerspective | "",
  mode: MarketViewMode,
): MarketViewMode {
  if (view !== "metals" && mode === "compare") return "chart";
  return mode;
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

type FiltersState = Omit<MarketIntelligenceUrlState, "view"> & {
  view: MarketPerspective | "";
};

function normalizeState(state: FiltersState): FiltersState {
  return {
    ...state,
    mode: normalizeMode(state.view, state.mode),
    granularity: normalizeGranularity(state.view, state.granularity),
  };
}

export function useMarketIntelligenceFilters(
  defaultView: MarketPerspective,
) {
  const initial = useMemo<FiltersState>(() => {
    const fromUrl = readMarketIntelligenceFromUrl();
    const range = defaultRange();
    return normalizeState({
      view: fromUrl.view ?? "",
      mode: fromUrl.mode ?? DEFAULT_MODE,
      granularity: fromUrl.granularity ?? DEFAULT_GRANULARITY,
      fxKind: fromUrl.fxKind ?? DEFAULT_FX_KIND,
      metals: fromUrl.metals ?? [],
      indicator: fromUrl.indicator ?? DEFAULT_INDICATOR,
      ncm: fromUrl.ncm ?? "",
      comexProducts: fromUrl.comexProducts ?? [],
      comexDirectNcms: fromUrl.comexDirectNcms ?? [],
      ippSeries: fromUrl.ippSeries ?? "",
      from: fromUrl.from ?? range.from,
      to: fromUrl.to ?? range.to,
    });
  }, []);

  const [state, setState] = useState<FiltersState>(initial);

  /** URL selection wins; otherwise the catalog-driven default view. */
  const effectiveState = useMemo<MarketIntelligenceUrlState>(
    () => ({
      ...state,
      view: state.view || defaultView,
      granularity: normalizeGranularity(
        state.view || defaultView,
        state.granularity,
      ),
      mode: normalizeMode(state.view || defaultView, state.mode),
    }),
    [state, defaultView],
  );

  const patch = useCallback((update: Partial<FiltersState>) => {
    setState((prev) => {
      const merged = { ...prev, ...update };
      return normalizeState({
        ...merged,
        view: merged.view || prev.view,
      });
    });
  }, []);

  // URL persistence (F5 + shareable links).
  useEffect(() => {
    writeMarketIntelligenceToUrl(effectiveState);
  }, [effectiveState]);

  // Back/forward navigation re-reads the query string.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const onPopState = () => {
      const fromUrl = readMarketIntelligenceFromUrl();
      setState((prev) =>
        normalizeState({
          ...prev,
          view: fromUrl.view ?? prev.view,
          mode: fromUrl.mode ?? prev.mode,
          granularity: fromUrl.granularity ?? prev.granularity,
          fxKind: fromUrl.fxKind ?? prev.fxKind,
          metals: fromUrl.metals ?? prev.metals,
          indicator: fromUrl.indicator ?? prev.indicator,
          ncm: fromUrl.ncm ?? prev.ncm,
          comexProducts: fromUrl.comexProducts ?? prev.comexProducts,
          comexDirectNcms:
            fromUrl.comexDirectNcms ?? prev.comexDirectNcms,
          ippSeries: fromUrl.ippSeries ?? prev.ippSeries,
          from: fromUrl.from ?? prev.from,
          to: fromUrl.to ?? prev.to,
        }),
      );
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const toggleMetal = useCallback(
    (code: string) => {
      setState((prev) => ({
        ...prev,
        metals: prev.metals.includes(code)
          ? prev.metals.filter((entry) => entry !== code)
          : [...prev.metals, code],
      }));
    },
    [],
  );

  return {
    state: effectiveState,
    setView: (view: MarketPerspective) => patch({ view }),
    setMode: (mode: MarketViewMode) => patch({ mode }),
    setGranularity: (granularity: MarketGranularity) =>
      patch({ granularity }),
    setFxKind: (fxKind: MarketFxKind) => patch({ fxKind }),
    setIndicator: (
      indicator: MarketIntelligenceUrlState["indicator"],
    ) => patch({ indicator }),
    setNcm: (ncm: string) => patch({ ncm }),
    setComexProducts: (comexProducts: string[]) =>
      patch({ comexProducts }),
    setComexDirectNcms: (comexDirectNcms: string[]) =>
      patch({ comexDirectNcms }),
    setIppSeries: (ippSeries: string) => patch({ ippSeries }),
    toggleMetal,
    setFrom: (from: string) => patch({ from }),
    setTo: (to: string) => patch({ to }),
  };
}
