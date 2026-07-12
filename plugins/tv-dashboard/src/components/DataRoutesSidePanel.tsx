import { useEffect, useState } from "react";
import { ArrowLeft, Factory, Package, ShieldCheck } from "lucide-react";
import { DataRouteCatalogPanel, FieldLabel, NativeTextControl, resolveDataRouteDisplayKinds } from "@delpi/plugin-ui/index";
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

const CATEGORY_ORDER = [
  "production",
  "quality",
  "supplies",
  "commercial",
  "products",
  "financial",
  "engineering",
  "hr",
  "scheduling",
  "strategic",
  "system",
  "other",
] as const;

const CATEGORY_LABELS: Record<string, string> = {
  production: "Produção",
  quality: "Qualidade",
  supplies: "Suprimentos",
  commercial: "Comercial",
  products: "Produtos",
  financial: "Financeiro",
  engineering: "Engenharia",
  hr: "Recursos Humanos",
  scheduling: "Agendamento",
  strategic: "Estratégico",
  system: "Sistema",
  other: "Outros",
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
        <DeckPropertySection pane title="Configurar fonte" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.sourceConfig}>
          <p className="td-deck-inspector__meta">{pickedRoute.label}</p>
          {pickedRoute.description ? (
            <p className="td-subtitle td-data-routes-panel__desc">{pickedRoute.description}</p>
          ) : null}
          <DeckField id="td-data-source-label" label="Rótulo">
            <NativeTextControl id="td-data-source-label" value={label} onChange={setLabel} />
          </DeckField>
          <DeckField
            id="td-data-source-refresh"
            label="Atualizar a cada (s)"
            hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.dataBlockRefreshInterval}
          >
            <NativeTextControl
              id="td-data-source-refresh"
              type="number"
              min={DATA_REFRESH_SEC_MIN}
              max={DATA_REFRESH_SEC_MAX}
              placeholder={`Padrão (${globalRefreshSec}s)`}
              value={refreshSec}
              onChange={setRefreshSec}
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
                <NativeTextControl
                  id={`td-data-source-param-${key}`}
                  type={field.type === "integer" ? "number" : "text"}
                  value={params?.[key] === undefined || params?.[key] === null ? "" : String(params[key])}
                  onChange={(raw) => {
                    setParams((previous) => {
                      const next = { ...(previous ?? {}) };
                      if (!raw.trim()) {
                        delete next[key];
                      } else if (field.type === "integer") {
                        next[key] = Number(raw);
                      } else {
                        next[key] = raw;
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
      <FieldLabel label="Fontes de dados" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.catalogSearch} />
      <DataRouteCatalogPanel
        items={routes.map((route) => ({
          id: route.operationId,
          label: route.label,
          category: route.category,
          description: route.description,
          path: route.path,
          httpMethod: "GET",
          metaShape: route.metaShape,
          displayKinds: resolveDataRouteDisplayKinds({
            metaShape: route.metaShape,
            allowedDisplayModes: route.allowedDisplayModes ?? route.suggestedDisplayModes,
          }),
        }))}
        onSelect={(item) => {
          const route = routes.find((entry) => entry.operationId === item.id);
          if (route) pickRoute(route);
        }}
        searchPlaceholder="Buscar fonte, descrição ou path…"
        emptyMessage="Nenhuma fonte com esses filtros."
        loading={loading}
        error={error}
        categoryLabels={CATEGORY_LABELS}
        categoryOrder={CATEGORY_ORDER}
        renderCategoryIcon={(category) => <CategoryIcon category={category} />}
      />
    </div>
  );
}
