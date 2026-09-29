import { useEffect, useMemo, useState } from "react";

import {
  listMFunctions,
  type MFunctionCatalogItem,
} from "../api/tvDashboardApi";

/**
 * Capability de expressões tipadas descoberta do catálogo vivo
 * (`GET /data/m/functions` — mesmo registry que `expressions.functions`
 * projeta no capability surface do backend).
 *
 * Sem catálogo → authoring desabilitado (graceful); o backend continua
 * sendo a autoridade final da validação.
 */
export type ParamExpressionSupport = {
  /** Catálogo carregado com ao menos uma função scalar. */
  enabled: boolean;
  loading: boolean;
  /** Funções `kind === "scalar"` (PARAMETER-phase usa só scalar). */
  functions: MFunctionCatalogItem[];
  registryVersion: string | null;
};

const DISABLED_SUPPORT: ParamExpressionSupport = {
  enabled: false,
  loading: false,
  functions: [],
  registryVersion: null,
};

let cachedItems: MFunctionCatalogItem[] | null = null;
let cachedRegistryVersion: string | null = null;
let inflight: Promise<MFunctionCatalogItem[]> | null = null;

/** Só para testes — limpa o cache compartilhado. */
export function resetParamExpressionCatalogCacheForTests(): void {
  cachedItems = null;
  cachedRegistryVersion = null;
  inflight = null;
}

function loadScalarFunctions(): Promise<MFunctionCatalogItem[]> {
  if (cachedItems) return Promise.resolve(cachedItems);
  if (!inflight) {
    inflight = listMFunctions()
      .then((catalog) => {
        cachedItems = (catalog.items ?? []).filter(
          (item) => !item.kind || item.kind === "scalar",
        );
        cachedRegistryVersion = catalog.registryVersion;
        return cachedItems;
      })
      .catch((error) => {
        inflight = null;
        throw error;
      });
  }
  return inflight;
}

export function useParamExpressionCapability(options?: {
  enabled?: boolean;
}): ParamExpressionSupport {
  const enabled = options?.enabled !== false;
  const [functions, setFunctions] = useState<MFunctionCatalogItem[] | null>(
    () => cachedItems,
  );
  const [loading, setLoading] = useState(enabled && cachedItems == null);

  useEffect(() => {
    if (!enabled) return;
    if (cachedItems != null) {
      setFunctions(cachedItems);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    void loadScalarFunctions()
      .then((items) => {
        if (!cancelled) {
          setFunctions(items);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFunctions([]);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [enabled]);

  return useMemo(() => {
    if (!enabled) return DISABLED_SUPPORT;
    if (functions == null) {
      return { ...DISABLED_SUPPORT, loading: true };
    }
    return {
      enabled: functions.length > 0 && !loading,
      loading,
      functions,
      registryVersion: cachedRegistryVersion,
    };
  }, [enabled, functions, loading]);
}
