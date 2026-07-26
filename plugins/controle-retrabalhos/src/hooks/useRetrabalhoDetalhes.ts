import { useCallback, useEffect, useRef, useState } from "react";

import { fetchRetrabalhoDetalhes } from "../api/retrabalhoApi";
import type { RetrabalhoDetalhesData, RetrabalhoQueryFilters } from "../types/retrabalho";
import { DEFAULT_PAGE_SIZE } from "../types/retrabalho";

export type DetalhesLoadState = "idle" | "loading" | "success" | "error";

export function useRetrabalhoDetalhes(
  appliedFilters: RetrabalhoQueryFilters | null,
  page: number,
  pageSize = DEFAULT_PAGE_SIZE,
) {
  const [state, setState] = useState<DetalhesLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RetrabalhoDetalhesData | null>(null);
  const requestIdRef = useRef(0);

  const reload = useCallback(async () => {
    if (!appliedFilters?.filial || !appliedFilters.start_date || !appliedFilters.end_date) {
      setState("idle");
      setData(null);
      setError(null);
      return;
    }

    const requestId = ++requestIdRef.current;
    setState("loading");
    setError(null);

    try {
      const response = await fetchRetrabalhoDetalhes(appliedFilters, page, pageSize);
      if (requestId !== requestIdRef.current) return;
      setData(response);
      setState("success");
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      setState("error");
      setError(err instanceof Error ? err.message : "Falha ao carregar detalhes.");
      setData(null);
    }
  }, [appliedFilters, page, pageSize]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { state, error, data, reload, isLoading: state === "loading" };
}
