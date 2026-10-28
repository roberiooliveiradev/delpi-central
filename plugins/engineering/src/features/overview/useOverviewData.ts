import { useCallback, useEffect, useRef, useState } from "react";

import { getEngineeringOverview } from "../../api/engineeringOverviewApi";
import { HomeApiError } from "../../api/httpClient";
import type { OverviewResponse } from "../../types/overview";
import {
  applyBranch,
  applyCompetence,
  applyDateEnd,
  applyDateStart,
  applyPreset,
  readFiltersFromSearch,
  toApiFilters,
  writeFiltersToUrl,
  type OverviewFilterState,
} from "./overviewFilters";

export type OverviewDataState =
  | { phase: "loading" }
  | { phase: "error"; error: HomeApiError }
  | { phase: "ready"; overview: OverviewResponse };

export function useOverviewData() {
  const [filters, setFilters] = useState<OverviewFilterState>(() =>
    readFiltersFromSearch(
      typeof window !== "undefined" ? window.location.search : "",
    ),
  );
  const [state, setState] = useState<OverviewDataState>({ phase: "loading" });
  const [refreshing, setRefreshing] = useState(false);
  const requestSeq = useRef(0);
  const controllerRef = useRef<AbortController | null>(null);

  const load = useCallback(
    async (current: OverviewFilterState, isRefresh: boolean) => {
      const seq = ++requestSeq.current;
      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;
      if (!isRefresh) setState({ phase: "loading" });
      setRefreshing(true);
      try {
        const overview = await getEngineeringOverview(
          toApiFilters(current),
          controller.signal,
        );
        if (seq !== requestSeq.current) return;
        setState({ phase: "ready", overview });
      } catch (error) {
        if (seq !== requestSeq.current) return;
        if ((error as Error)?.name === "AbortError") return;
        setState({
          phase: "error",
          error:
            error instanceof HomeApiError
              ? error
              : new HomeApiError(
                  "network_error",
                  "Falha ao carregar a visão geral.",
                ),
        });
      } finally {
        if (seq === requestSeq.current) setRefreshing(false);
      }
    },
    [],
  );

  const update = useCallback(
    (next: OverviewFilterState) => {
      setFilters(next);
      writeFiltersToUrl(next);
      void load(next, true);
    },
    [load],
  );

  useEffect(() => {
    writeFiltersToUrl(filters);
    const pending = queueMicrotask(() => void load(filters, false));
    return () => {
      void pending;
      requestSeq.current += 1;
      controllerRef.current?.abort();
      controllerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    state,
    filters,
    refreshing,
    setPreset: (preset: OverviewFilterState["preset"]) =>
      update(applyPreset(preset, filters)),
    setCompetence: (competence: string) =>
      update(applyCompetence(competence, filters)),
    setDateStart: (value: string) => update(applyDateStart(value, filters)),
    setDateEnd: (value: string) => update(applyDateEnd(value, filters)),
    setBranch: (branch: string) => update(applyBranch(branch, filters)),
    reload: () => void load(filters, true),
  };
}
