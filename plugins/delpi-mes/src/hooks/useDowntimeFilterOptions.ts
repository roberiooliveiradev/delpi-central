import { useCallback, useEffect, useRef, useState } from "react";

import { getDowntimeFilterOptions } from "../api/mesApi";
import type { BranchCode } from "../constants/routes";
import type { DowntimeFilterOptionsResponse } from "../types/mes";

/** Opções de filtro (motivos do catálogo + origens válidas) — um fetch por
 * filial, sem exigir a permissão administrativa de Cadastros. */
export function useDowntimeFilterOptions(branch: BranchCode) {
  const [data, setData] = useState<DowntimeFilterOptionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => {
    queueMicrotask(() => {
      setData(null);
      setError(null);
      setLoading(true);
    });
    const next = new AbortController();
    controller.current?.abort();
    controller.current = next;
    getDowntimeFilterOptions(branch, next.signal)
      .then((response) => {
        setData(response);
        setError(null);
      })
      .catch((reason: unknown) => {
        if (!next.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Falha ao carregar as opções de filtro.");
        }
      })
      .finally(() => {
        if (!next.signal.aborted) setLoading(false);
      });
    return () => next.abort();
  }, [branch, reloadKey]);

  const retry = useCallback(() => setReloadKey((key) => key + 1), []);
  return { data, error, loading, retry };
}
