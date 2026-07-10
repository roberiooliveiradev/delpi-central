import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Factory, Package, ShieldCheck } from "lucide-react";
import { FieldLabel } from "@delpi/plugin-ui/index";
import {
  createDataSourceBlock,
  DATA_REFRESH_SEC_MAX,
  DATA_REFRESH_SEC_MIN,
  type ComunicadoDataBinding,
} from "@delpi/tv-dashboard-presentation";

import { listDataRoutes, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

const CATEGORY_ORDER = ["production", "quality", "supplies", "products", "strategic"] as const;

const CATEGORY_LABELS: Record<string, string> = {
  production: "Produção",
  quality: "Qualidade",
  supplies: "Suprimentos",
  products: "Produtos",
  strategic: "Estratégico",
};

type ParamSchema = Record<string, { type?: string; label?: string; default?: string | number; optional?: boolean }>;

function CategoryIcon({ category }: { category: string }) {
  if (category === "quality") return <ShieldCheck size={16} aria-hidden />;
  if (category === "supplies" || category === "products") return <Package size={16} aria-hidden />;
  return <Factory size={16} aria-hidden />;
}

type Props = {
  /** Chamado após inserir fonte no palco (ex.: voltar aba Elemento). */
  onInserted?: () => void;
};

export function DataRoutesSidePanel({ onInserted }: Props) {
  const { config, addDataSourceBlock, globalRefreshSec } = useComunicadoEditor();
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pickedRoute, setPickedRoute] = useState<TvDataRouteCatalogItem | null>(null);
  const [label, setLabel] = useState("");
  const [refreshSec, setRefreshSec] = useState<string>("");
  const [params, setParams] = useState<ComunicadoDataBinding["params"]>({});

  useEffect(() => {
    setLoading(true);
    setError(null);
    void listDataRoutes()
      .then(setRoutes)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

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

  const slideFilters = config.dataFilters ?? {};

  function pickRoute(route: TvDataRouteCatalogItem) {
    setPickedRoute(route);
    setLabel(route.label);
    const defaults = Object.fromEntries(
      Object.entries(route.paramSchema ?? {})
        .map(([key, schema]) => {
          const def = (schema as { default?: string | number }).default;
          return def !== undefined ? [key, def] : null;
        })
        .filter(Boolean) as Array<[string, string | number]>,
    );
    setParams(defaults);
    setRefreshSec("");
  }

  function handleInsert() {
    if (!pickedRoute) return;
    const defaultParams = { ...params };
    for (const [key, value] of Object.entries(slideFilters)) {
      if ((defaultParams[key] === undefined || defaultParams[key] === "") && value != null && value !== "") {
        defaultParams[key] = value;
      }
    }
    const block = createDataSourceBlock(pickedRoute.operationId, {
      label: label.trim() || pickedRoute.label,
      defaultParams,
      refreshSec: refreshSec.trim() ? Number(refreshSec) : undefined,
    });
    addDataSourceBlock(block);
    setPickedRoute(null);
    setQuery("");
    onInserted?.();
  }

  if (pickedRoute) {
    const schema = (pickedRoute.paramSchema as ParamSchema) ?? {};
    return (
      <div className="td-data-routes-panel">
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--ghost td-data-routes-panel__back"
          onClick={() => setPickedRoute(null)}
        >
          <ArrowLeft size={16} aria-hidden="true" />
          Voltar ao catálogo
        </button>
        <DeckPropertySection title="Configurar fonte" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.sourceConfig}>
          <p className="td-deck-inspector__meta">{pickedRoute.label}</p>
          <DeckField id="td-data-source-label" label="Rótulo">
            <input id="td-data-source-label" value={label} onChange={(event) => setLabel(event.target.value)} />
          </DeckField>
          <DeckField
            id="td-data-source-refresh"
            label="Atualizar a cada (s)"
            hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.dataBlockRefreshInterval}
          >
            <input
              id="td-data-source-refresh"
              type="number"
              min={DATA_REFRESH_SEC_MIN}
              max={DATA_REFRESH_SEC_MAX}
              placeholder={`Padrão (${globalRefreshSec}s)`}
              value={refreshSec}
              onChange={(event) => setRefreshSec(event.target.value)}
            />
          </DeckField>
          {Object.entries(schema).map(([key, field]) => {
            const inherited = slideFilters[key] !== undefined && (params?.[key] === undefined || params?.[key] === "");
            return (
              <DeckField
                key={key}
                id={`td-data-source-param-${key}`}
                label={`${field.label ?? key}${inherited ? " (herdado do slide)" : ""}`}
              >
                <input
                  id={`td-data-source-param-${key}`}
                  type={field.type === "integer" ? "number" : "text"}
                  value={params?.[key] === undefined || params?.[key] === null ? "" : String(params[key])}
                  onChange={(event) => {
                    const raw = event.target.value;
                    setParams((previous) => {
                      const next = { ...(previous ?? {}) };
                      if (!raw.trim()) {
                        delete next[key];
                      } else if (field.type === "integer") {
                        next[key] = Number(raw);
                      } else {
                        next[key] = raw.trim();
                      }
                      return next;
                    });
                  }}
                />
              </DeckField>
            );
          })}
          <button type="button" className="td-btn td-btn--primary td-btn--sm" onClick={handleInsert}>
            Inserir fonte de dados
          </button>
        </DeckPropertySection>
      </div>
    );
  }

  return (
    <div className="td-data-routes-panel">
      <FieldLabel hint={TV_DASHBOARD_HELP_TOOLTIPS.data.catalogSearch}>Catálogo api-delpi</FieldLabel>
      <input
        type="search"
        className="td-data-routes-panel__search"
        placeholder="Buscar por nome ou categoria…"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      {loading ? <p className="td-subtitle">Carregando catálogo…</p> : null}
      {error ? <p className="td-error">{error}</p> : null}
      <div className="td-data-route-groups td-data-route-groups--panel">
        {grouped.map((group) => (
          <section key={group.key} className="td-data-route-group">
            <h3 className="td-data-route-group__title">
              <CategoryIcon category={group.key} />
              {group.label}
            </h3>
            <ul className="td-data-route-list">
              {group.routes.map((route) => (
                <li key={route.operationId}>
                  <button type="button" className="td-data-route-list__item" onClick={() => pickRoute(route)}>
                    <span className="td-data-route-list__label">{route.label}</span>
                    <span className="td-data-route-list__meta">{route.operationId}</span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
