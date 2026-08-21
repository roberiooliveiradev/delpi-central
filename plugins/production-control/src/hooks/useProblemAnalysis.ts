import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchProblemDetectorItems, fetchProblemDetectors } from "../api/ppcApi";
import type {
  PpcBranch,
  ProblemDetectorItemsPayload,
  ProblemDetectorsPayload,
} from "../types";

/** Teto do BFF — cobre o universo típico do detector sem paginar na UI. */
const DETECTOR_ITEMS_PAGE_SIZE = 200;

/**
 * Cards do catálogo e registros do detector ativo.
 *
 * Sem detector na URL, abre o primeiro card — o catálogo já vem ordenado pela
 * API, então a área nunca chega vazia quando há detector disponível.
 */
export function useProblemAnalysis(branch: PpcBranch, detectorId: string | null) {
  const [detectors, setDetectors] = useState<ProblemDetectorsPayload | null>(null);
  const [items, setItems] = useState<ProblemDetectorItemsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [itemsLoading, setItemsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  const activeId = useMemo(() => {
    const known = detectors?.detectors ?? [];
    if (detectorId && known.some((detector) => detector.id === detectorId)) {
      return detectorId;
    }
    return known[0]?.id ?? null;
  }, [detectorId, detectors]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchProblemDetectors({ branch, signal: controller.signal })
      .then((payload) => {
        setDetectors(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar análise.");
        setDetectors(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, reloadToken]);

  useEffect(() => {
    if (!activeId) {
      setItems(null);
      return;
    }
    const controller = new AbortController();
    setItemsLoading(true);
    fetchProblemDetectorItems({
      branch,
      detectorId: activeId,
      page: 1,
      pageSize: DETECTOR_ITEMS_PAGE_SIZE,
      signal: controller.signal,
    })
      .then((payload) => {
        setItems(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar registros.");
        setItems(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setItemsLoading(false);
      });
    return () => controller.abort();
  }, [activeId, branch, reloadToken]);

  return { detectors, items, activeId, loading, itemsLoading, error, reload };
}
