import { useCallback, useEffect, useState } from "react";

import { searchActiveCustomers } from "../../../api/commercialPortfolioApi";
import type { TotvsCustomerHit } from "../../../types/portfolio";

const DEFAULT_DEBOUNCE_MS = 300;
const MIN_QUERY_LENGTH = 2;

export type UseActiveCustomerSearchResult = {
  query: string;
  setQuery: (value: string) => void;
  hits: TotvsCustomerHit[];
  searching: boolean;
  error: string | null;
  queryReady: boolean;
  reset: () => void;
};

/**
 * Busca remota de clientes ativos TOTVS (mesmo contrato da admin de carteira).
 */
export function useActiveCustomerSearch(options?: {
  debounceMs?: number;
  pageSize?: number;
  enabled?: boolean;
}): UseActiveCustomerSearchResult {
  const debounceMs = options?.debounceMs ?? DEFAULT_DEBOUNCE_MS;
  const pageSize = options?.pageSize ?? 15;
  const enabled = options?.enabled !== false;

  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<TotvsCustomerHit[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const queryReady = query.trim().length >= MIN_QUERY_LENGTH;

  useEffect(() => {
    if (!enabled) {
      setHits([]);
      setError(null);
      setSearching(false);
      return;
    }
    const normalized = query.trim();
    if (normalized.length < MIN_QUERY_LENGTH) {
      setHits([]);
      setError(null);
      setSearching(false);
      return;
    }
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      setSearching(true);
      setError(null);
      searchActiveCustomers(normalized, { pageSize, signal: controller.signal })
        .then((result) => {
          if (!controller.signal.aborted) {
            setHits(result.items);
            setError(null);
          }
        })
        .catch((err: unknown) => {
          if (controller.signal.aborted) return;
          setHits([]);
          setError(
            err instanceof Error && err.message.trim()
              ? err.message
              : "Não foi possível buscar clientes no cadastro.",
          );
        })
        .finally(() => {
          if (!controller.signal.aborted) setSearching(false);
        });
    }, debounceMs);
    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [debounceMs, enabled, pageSize, query]);

  const reset = useCallback(() => {
    setQuery("");
    setHits([]);
    setError(null);
    setSearching(false);
  }, []);

  return { query, setQuery, hits, searching, error, queryReady, reset };
}
