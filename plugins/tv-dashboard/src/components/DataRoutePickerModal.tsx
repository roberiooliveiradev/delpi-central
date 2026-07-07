import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import {
  createDataBlock,
  defaultDataBlockTypeForRoute,
  type ComunicadoDataBlockType,
} from "@delpi/tv-dashboard-presentation";

import { listDataRoutes, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";

type Props = {
  open: boolean;
  onClose: () => void;
  onSelect: (block: ReturnType<typeof createDataBlock>) => void;
};

export function DataRoutePickerModal({ open, onClose, onSelect }: Props) {
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
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

  if (!open) return null;

  function handlePick(route: TvDataRouteCatalogItem, blockType?: ComunicadoDataBlockType) {
    const type = blockType ?? defaultDataBlockTypeForRoute(route.allowedDisplayModes);
    const defaultParams = Object.fromEntries(
      Object.entries(route.paramSchema ?? {})
        .map(([key, schema]) => {
          const def = (schema as { default?: string | number }).default;
          return def !== undefined ? [key, def] : null;
        })
        .filter(Boolean) as Array<[string, string | number]>,
    );
    onSelect(
      createDataBlock(route.operationId, {
        blockType: type,
        label: route.label,
        defaultParams,
      }),
    );
    onClose();
  }

  return (
    <div className="td-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="td-modal td-modal--wide"
        role="dialog"
        aria-modal="true"
        aria-label="Catálogo de indicadores"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="td-modal__header">
          <h2>Inserir indicador</h2>
          <button type="button" className="td-icon-btn" onClick={onClose} aria-label="Fechar">
            <X size={18} />
          </button>
        </header>
        <div className="td-modal__body">
          <input
            type="search"
            placeholder="Buscar por nome ou categoria…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          {loading ? <p className="td-subtitle">Carregando catálogo…</p> : null}
          {error ? <p className="td-error">{error}</p> : null}
          <ul className="td-data-route-list">
            {filtered.map((route) => (
              <li key={route.operationId}>
                <button type="button" className="td-data-route-list__item" onClick={() => handlePick(route)}>
                  <span className="td-data-route-list__label">{route.label}</span>
                  <span className="td-data-route-list__meta">{route.category}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
