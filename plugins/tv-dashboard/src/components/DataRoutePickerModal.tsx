import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Factory, Package, ShieldCheck, X } from "lucide-react";
import {
  blockTypeForDisplayMode,
  createDataBlock,
  listDataPresentationOptions,
  type ComunicadoDataDisplayMode,
} from "@delpi/tv-dashboard-presentation";

import { listDataRoutes, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";

type Props = {
  open: boolean;
  onClose: () => void;
  onSelect: (block: ReturnType<typeof createDataBlock>) => void;
};

const CATEGORY_ORDER = ["production", "quality", "supplies", "products", "strategic"] as const;

const CATEGORY_LABELS: Record<string, string> = {
  production: "Produção",
  quality: "Qualidade",
  supplies: "Suprimentos",
  products: "Produtos",
  strategic: "Estratégico",
};

function CategoryIcon({ category }: { category: string }) {
  if (category === "quality") return <ShieldCheck size={16} aria-hidden />;
  if (category === "supplies" || category === "products") return <Package size={16} aria-hidden />;
  return <Factory size={16} aria-hidden />;
}

function routeDisplayModes(route: TvDataRouteCatalogItem): string[] | undefined {
  return route.suggestedDisplayModes ?? route.allowedDisplayModes;
}

export function DataRoutePickerModal({ open, onClose, onSelect }: Props) {
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pickedRoute, setPickedRoute] = useState<TvDataRouteCatalogItem | null>(null);

  useEffect(() => {
    if (!open) {
      setPickedRoute(null);
      setQuery("");
      return;
    }
    setLoading(true);
    setError(null);
    void listDataRoutes()
      .then(setRoutes)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [open]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return routes;
    return routes.filter(
      (route) =>
        route.label.toLowerCase().includes(q) ||
        route.operationId.toLowerCase().includes(q) ||
        route.category.toLowerCase().includes(q),
    );
  }, [query, routes]);

  const grouped = useMemo(() => {
    const buckets = new Map<string, TvDataRouteCatalogItem[]>();
    for (const route of filtered) {
      const key = route.category || "outros";
      const list = buckets.get(key) ?? [];
      list.push(route);
      buckets.set(key, list);
    }
    const orderedKeys = [
      ...CATEGORY_ORDER.filter((key) => buckets.has(key)),
      ...[...buckets.keys()].filter((key) => !CATEGORY_ORDER.includes(key as (typeof CATEGORY_ORDER)[number])),
    ];
    return orderedKeys.map((key) => ({
      key,
      label: CATEGORY_LABELS[key] ?? key,
      routes: buckets.get(key) ?? [],
    }));
  }, [filtered]);

  const presentationOptions = useMemo(() => {
    if (!pickedRoute) return [];
    return listDataPresentationOptions(routeDisplayModes(pickedRoute));
  }, [pickedRoute]);

  if (!open) return null;

  function buildBlock(route: TvDataRouteCatalogItem, displayMode: ComunicadoDataDisplayMode) {
    const modes = routeDisplayModes(route);
    const blockType = blockTypeForDisplayMode(displayMode, modes);
    const defaultParams = Object.fromEntries(
      Object.entries(route.paramSchema ?? {})
        .map(([key, schema]) => {
          const def = (schema as { default?: string | number }).default;
          return def !== undefined ? [key, def] : null;
        })
        .filter(Boolean) as Array<[string, string | number]>,
    );
    return createDataBlock(route.operationId, {
      blockType,
      label: route.label,
      displayMode,
      defaultParams,
    });
  }

  function handleConfirm(displayMode: ComunicadoDataDisplayMode) {
    if (!pickedRoute) return;
    onSelect(buildBlock(pickedRoute, displayMode));
    onClose();
  }

  return (
    <div className="td-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="td-modal td-modal--wide"
        role="dialog"
        aria-modal="true"
        aria-label={pickedRoute ? "Formato de apresentação" : "Catálogo de dados"}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="td-modal__header">
          {pickedRoute ? (
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              onClick={() => setPickedRoute(null)}
            >
              <ArrowLeft size={16} aria-hidden="true" />
              Voltar
            </button>
          ) : null}
          <h2>{pickedRoute ? "Formato de apresentação" : "Inserir dados"}</h2>
          <button type="button" className="td-icon-btn" onClick={onClose} aria-label="Fechar">
            <X size={18} />
          </button>
        </header>
        <div className="td-modal__body">
          {!pickedRoute ? (
            <>
              <input
                type="search"
                placeholder="Buscar por nome ou categoria…"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              {loading ? <p className="td-subtitle">Carregando catálogo…</p> : null}
              {error ? <p className="td-error">{error}</p> : null}
              <div className="td-data-route-groups">
                {grouped.map((group) => (
                  <section key={group.key} className="td-data-route-group">
                    <h3 className="td-data-route-group__title">
                      <CategoryIcon category={group.key} />
                      {group.label}
                    </h3>
                    <ul className="td-data-route-list">
                      {group.routes.map((route) => (
                        <li key={route.operationId}>
                          <button
                            type="button"
                            className="td-data-route-list__item"
                            onClick={() => setPickedRoute(route)}
                          >
                            <span className="td-data-route-list__label">{route.label}</span>
                            <span className="td-data-route-list__meta">{route.operationId}</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </section>
                ))}
              </div>
            </>
          ) : (
            <>
              <p className="td-subtitle">{pickedRoute.label}</p>
              <ul className="td-data-route-list">
                {presentationOptions.map((option) => (
                  <li key={option.displayMode}>
                    <button
                      type="button"
                      className="td-data-route-list__item"
                      onClick={() => handleConfirm(option.displayMode)}
                    >
                      <span className="td-data-route-list__label">{option.label}</span>
                      <span className="td-data-route-list__meta">{option.description}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
