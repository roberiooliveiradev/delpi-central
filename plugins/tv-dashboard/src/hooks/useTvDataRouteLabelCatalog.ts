import type { DataSourceLabelCatalog } from "@delpi/tv-dashboard-presentation";
import { useEffect, useMemo, useState } from "react";

import { listDataRoutes, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { buildLabelCatalogFromRoutes } from "../utils/hydrateComunicadoDataBindings";

/**
 * Cache de sessão do catálogo de rotas — Elemento, Dados e demais painéis
 * compartilham o mesmo fetch para `resolveDataSourceLabel` / valueFields.
 */
let cachedRoutes: TvDataRouteCatalogItem[] | null = null;
let inflight: Promise<TvDataRouteCatalogItem[]> | null = null;

/** Só para testes — limpa o cache compartilhado. */
export function resetTvDataRouteLabelCatalogCacheForTests(): void {
  cachedRoutes = null;
  inflight = null;
}

export function loadTvDataRoutesForLabelCatalog(): Promise<TvDataRouteCatalogItem[]> {
  if (cachedRoutes) return Promise.resolve(cachedRoutes);
  if (!inflight) {
    inflight = listDataRoutes()
      .then((routes) => {
        cachedRoutes = routes;
        return routes;
      })
      .catch((error) => {
        inflight = null;
        throw error;
      });
  }
  return inflight;
}

/**
 * Catálogo vivo de labels de fonte (`operationId` → label do TV).
 * Usar em qualquer inspector de bloco que chame `DataSourceLinkSection`
 * ou `resolveDataSourceLabel` — não refetch ad hoc por tipo (texto vs gráfico).
 */
export function useTvDataRouteLabelCatalog(options?: { enabled?: boolean }): {
  routes: TvDataRouteCatalogItem[];
  labelCatalog: DataSourceLabelCatalog;
} {
  const enabled = options?.enabled !== false;
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>(() => cachedRoutes ?? []);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    void loadTvDataRoutesForLabelCatalog()
      .then((next) => {
        if (!cancelled) setRoutes(next);
      })
      .catch(() => {
        if (!cancelled) setRoutes([]);
      });
    return () => {
      cancelled = true;
    };
  }, [enabled]);

  const labelCatalog = useMemo(() => buildLabelCatalogFromRoutes(routes), [routes]);

  return { routes, labelCatalog };
}
