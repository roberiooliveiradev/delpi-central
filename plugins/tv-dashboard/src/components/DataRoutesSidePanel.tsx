import { useEffect, useState } from "react";
import { ArrowLeft, Factory, Package, ShieldCheck } from "lucide-react";
import {
  DataRouteCatalogPanel,
  FieldLabel,
  NativeTextControl,
  resolveDataRouteDisplayKinds,
  summarizeRouteParams,
} from "@delpi/plugin-ui/index";
import {
  createDataSourceBlock,
  DATA_REFRESH_SEC_MAX,
  DATA_REFRESH_SEC_MIN,
  type ComunicadoDataBinding,
} from "@delpi/tv-dashboard-presentation";

import { listDataRoutes, type BranchScope, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { DataCatalogMode } from "./comunicadoEditorContextCore";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataParamFields, type DataParamSchema, visibleParamSchema } from "./DataParamFields";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import {
  DATE_RANGE_PRESET_PARAM,
  defaultDateRangePreset,
  findDateRangeKeys,
} from "../utils/dateRangePresets";

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

function CategoryIcon({ category }: { category: string }) {
  if (category === "quality") return <ShieldCheck size={16} aria-hidden />;
  if (category === "supplies" || category === "products") return <Package size={16} aria-hidden />;
  return <Factory size={16} aria-hidden />;
}

type Props = {
  /** Chamado após inserir/substituir fonte (ex.: fechar modal ou voltar aba Elemento). */
  onInserted?: () => void;
  branchScope?: BranchScope | null;
  layout?: "ribbon" | "pane";
  /** Modal já tem título — omite o FieldLabel duplicado. */
  hideHeading?: boolean;
  /** insert = nova fonte no palco; replace = troca a rota do bloco selecionado. */
  mode?: DataCatalogMode;
};

export function DataRoutesSidePanel({
  onInserted,
  branchScope = null,
  layout = "pane",
  hideHeading = false,
  mode = "insert",
}: Props) {
  const { config, addDataSourceBlock, replaceSelectedDataRoute, globalRefreshSec } =
    useComunicadoEditor();
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
    const defaults: NonNullable<ComunicadoDataBinding["params"]> = Object.fromEntries(
      Object.entries(route.paramSchema ?? {})
        .map(([key, schema]) => {
          const def = (schema as { default?: string | number }).default;
          return def !== undefined ? [key, def] : null;
        })
        .filter(Boolean) as Array<[string, string | number]>,
    );
    const pair = findDateRangeKeys(Object.keys(route.paramSchema ?? {}));
    const preset = defaultDateRangePreset(pair);
    if (preset) {
      defaults[DATE_RANGE_PRESET_PARAM] = preset;
    }
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
    if (mode === "replace") {
      replaceSelectedDataRoute(block);
    } else {
      addDataSourceBlock(block);
    }
    setPickedRoute(null);
    onInserted?.();
  }

  if (pickedRoute) {
    const schema = visibleParamSchema(
      pickedRoute.paramSchema as DataParamSchema,
      pickedRoute.fixedQueryParams as Record<string, unknown> | undefined,
    );
    const inheritedKeys = new Set(
      Object.keys(slideFilters).filter((key) => params?.[key] === undefined || params?.[key] === ""),
    );
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
            <NativeTextControl
              id="td-data-source-label"
              className={layout === "ribbon" ? "delpi-ui-native-control--compact" : undefined}
              value={label}
              onChange={setLabel}
            />
          </DeckField>
          <DeckField
            id="td-data-source-refresh"
            label="Atualizar na TV a cada (s)"
            hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.dataBlockRefreshInterval}
          >
            <NativeTextControl
              id="td-data-source-refresh"
              type="number"
              className={layout === "ribbon" ? "delpi-ui-native-control--compact" : undefined}
              min={DATA_REFRESH_SEC_MIN}
              max={DATA_REFRESH_SEC_MAX}
              placeholder={`Padrão (${globalRefreshSec}s)`}
              value={refreshSec}
              onChange={setRefreshSec}
            />
          </DeckField>
          <DataParamFields
            schema={schema}
            values={params}
            inheritedKeys={inheritedKeys}
            branchScope={branchScope}
            idPrefix="td-data-source-param"
            layout={layout}
            onChange={(key, raw) => {
              setParams((previous) => {
                const next = { ...(previous ?? {}) };
                const fieldType = schema[key]?.type;
                if (!raw.trim()) {
                  delete next[key];
                } else if (fieldType === "integer" || fieldType === "number") {
                  next[key] = Number(raw);
                } else if (fieldType === "boolean") {
                  next[key] = raw === "true";
                } else {
                  next[key] = raw;
                }
                return next;
              });
            }}
          />
          <button type="button" className="td-btn td-btn--primary td-btn--sm" onClick={handleInsert}>
            {mode === "replace" ? "Aplicar rota" : "Inserir fonte de dados"}
          </button>
        </DeckPropertySection>
      </div>
    );
  }

  return (
    <div
      className={[
        "td-data-routes-panel",
        hideHeading ? "td-data-routes-panel--compact" : null,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {hideHeading ? null : (
        <FieldLabel label="Fontes de dados" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.catalogSearch} />
      )}
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
          params: summarizeRouteParams(route.paramSchema, route.fixedQueryParams),
        }))}
        onSelect={(item) => {
          const route = routes.find((entry) => entry.operationId === item.id);
          if (route) pickRoute(route);
        }}
        density={hideHeading ? "comfortable" : "compact"}
        confirmLabel={mode === "replace" ? "Usar esta rota" : "Usar esta fonte"}
        searchPlaceholder="Buscar fonte ou descrição…"
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
