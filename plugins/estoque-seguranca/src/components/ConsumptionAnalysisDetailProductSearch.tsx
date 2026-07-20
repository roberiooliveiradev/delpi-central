import { useEffect, useRef, useState } from "react";

import { fetchConsumptionAnalysisItems } from "../api/safetyStockApi";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import {
  DEFAULT_ANALYSIS_QUERY_PARAMS,
  type ConsumptionAnalysisItem,
} from "../types/consumptionAnalysis";

const MIN_SEARCH_LENGTH = 2;
const MAX_RESULTS = 8;

type ConsumptionAnalysisDetailProductSearchProps = {
  branch: string;
  onNavigate: (item: ConsumptionAnalysisItem) => void;
};

/** Busca no cabeçalho do modal para abrir a análise de outro produto. */
export function ConsumptionAnalysisDetailProductSearch({
  branch,
  onNavigate,
}: ConsumptionAnalysisDetailProductSearchProps) {
  const [term, setTerm] = useState("");
  const [results, setResults] = useState<ConsumptionAnalysisItem[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const debouncedTerm = useDebouncedValue(term, 350);

  useEffect(() => {
    const trimmed = debouncedTerm.trim();
    if (!branch || trimmed.length < MIN_SEARCH_LENGTH) {
      setResults([]);
      setOpen(false);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    let cancelled = false;
    setLoading(true);
    setOpen(true);

    fetchConsumptionAnalysisItems(
      {
        ...DEFAULT_ANALYSIS_QUERY_PARAMS,
        branch,
        search: trimmed,
        analysisStatus: "",
        includeBlocked: true,
        sortBy: "product_code",
        sortDirection: "asc",
      },
      1,
      MAX_RESULTS,
      { signal: controller.signal },
    )
      .then((data) => {
        if (cancelled) return;
        setResults(data.items);
      })
      .catch(() => {
        if (cancelled) return;
        setResults([]);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [debouncedTerm, branch]);

  useEffect(() => {
    if (!open) return;
    const handlePointerDown = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [open]);

  const handleSelect = (item: ConsumptionAnalysisItem) => {
    setTerm("");
    setResults([]);
    setOpen(false);
    onNavigate(item);
  };

  return (
    <div className="ess-detail-search" ref={containerRef}>
      <input
        type="search"
        value={term}
        placeholder="Buscar outro produto…"
        aria-label="Buscar outro produto"
        onChange={(event) => setTerm(event.target.value)}
        onFocus={() => {
          if (results.length > 0) setOpen(true);
        }}
      />
      {open ? (
        <ul className="ess-detail-search__results" role="listbox" aria-label="Produtos encontrados">
          {loading ? <li className="ess-detail-search__empty">Buscando…</li> : null}
          {!loading && results.length === 0 ? (
            <li className="ess-detail-search__empty">Nenhum produto encontrado.</li>
          ) : null}
          {!loading
            ? results.map((result) => (
                <li key={`${result.branch}-${result.product_code}`}>
                  <button
                    type="button"
                    className="ess-detail-search__option"
                    onClick={() => handleSelect(result)}
                  >
                    <strong>{result.product_code}</strong>
                    <span>{result.product_description}</span>
                  </button>
                </li>
              ))
            : null}
        </ul>
      ) : null}
    </div>
  );
}
