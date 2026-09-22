import { useEffect, useMemo, useState } from "react";
import {
  createDataSourceBlock,
  type ComunicadoBlock,
  type ComunicadoDataSourceBlock,
  type DataTransform,
} from "@delpi/tv-dashboard-presentation";

import {
  createDataBuilderSession,
  dataBuilderTurn,
  listDataRoutes,
  materializeDataBuilderSession,
  previewDataBuilderSession,
  suggestDataRoutes,
  type BranchScope,
  type DataBuilderDraft,
  type DataBuilderPreviewTable,
  type DataBuilderSession,
  type TvDataRouteCatalogItem,
} from "../api/tvDashboardApi";
import { DATA_BUILDER_CHAT_CONTENT as C } from "../content/dataBuilderChatContent";
import { applyDataParamRawUpdates } from "../utils/applyDataParamUpdates";
import { buildRouteDefaultParams } from "../utils/buildRouteDefaultParams";
import { previewTvDataRoute } from "../utils/previewTvDataRoute";
import { shouldRequestDataRouteSuggestions } from "../utils/shouldRequestDataRouteSuggestions";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import type { DataCatalogMode } from "./comunicadoEditorContextCore";
import { DataParamFields, type DataParamSchema, visibleParamSchema } from "./DataParamFields";
import {
  DATA_ROUTE_CATALOG_CONTENT,
  DataRouteCatalogPanel,
  resolveDataRouteDisplayKinds,
  summarizeRouteParams,
  type DataRouteCatalogItem,
  type DataRouteCatalogSuggestion,
  type DataRoutePreviewPayload,
  type DataRouteTestParams,
} from "@delpi/plugin-ui/index";

type Props = {
  mode?: DataCatalogMode;
  branchScope?: BranchScope | null;
  onInserted?: () => void;
};

const SUGGEST_DEBOUNCE_MS = 350;
const SUGGEST_LIMIT = 8;

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

function remapTransformSourceIds(
  transform: DataTransform | undefined,
  idMap: Record<string, string>,
): DataTransform | undefined {
  if (!transform || !("steps" in transform) || !Array.isArray(transform.steps)) {
    return transform;
  }
  const steps = transform.steps.map((step) => {
    if (!step || typeof step !== "object") return step;
    const row = { ...(step as Record<string, unknown>) };
    if (row.op === "merge" && typeof row.sourceId === "string" && idMap[row.sourceId]) {
      row.sourceId = idMap[row.sourceId];
    }
    return row;
  });
  return { ...transform, steps } as DataTransform;
}

function normalizePreview(preview: unknown): DataBuilderPreviewTable | null {
  if (!preview || typeof preview !== "object") return null;
  const row = preview as Record<string, unknown>;
  const columns = Array.isArray(row.columns) ? row.columns.map(String) : [];
  const rows = Array.isArray(row.rows) ? (row.rows as Array<Array<unknown>>) : [];
  const rowCount = typeof row.rowCount === "number" ? row.rowCount : rows.length;
  if (!columns.length && !rows.length) {
    return { columns: [], rows: [], rowCount };
  }
  return { columns, rows, rowCount };
}

export function DataBuilderChatPanel({
  mode = "insert",
  branchScope = null,
  onInserted,
}: Props) {
  const { addDataSourceBlock, replaceSelectedDataRoute, playlistId, playlistDefaults, config } =
    useComunicadoEditor();
  const [session, setSession] = useState<DataBuilderSession | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewTable, setPreviewTable] = useState<DataBuilderPreviewTable | null>(null);
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const [routesLoading, setRoutesLoading] = useState(false);
  const [routesError, setRoutesError] = useState<string | null>(null);
  const [catalogQuery, setCatalogQuery] = useState("");
  const [suggestions, setSuggestions] = useState<DataRouteCatalogSuggestion[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [suggestionsQuery, setSuggestionsQuery] = useState("");
  const [suggestionsDegraded, setSuggestionsDegraded] = useState(false);
  const [sourceFiltersOpen, setSourceFiltersOpen] = useState(false);
  const [previewExpanded, setPreviewExpanded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setBusy(true);
    void createDataBuilderSession()
      .then((created) => {
        if (!cancelled) {
          setSession(created);
          setPreviewTable(normalizePreview(created.preview));
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message || C.sessionError);
      })
      .finally(() => {
        if (!cancelled) setBusy(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setRoutesLoading(true);
    setRoutesError(null);
    void listDataRoutes()
      .then((items) => {
        if (!cancelled) setRoutes(items || []);
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setRoutes([]);
          setRoutesError(err.message || C.catalogEmpty);
        }
      })
      .finally(() => {
        if (!cancelled) setRoutesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const trimmed = catalogQuery.trim();
    if (!shouldRequestDataRouteSuggestions(trimmed)) {
      setSuggestions([]);
      setSuggestionsQuery("");
      setSuggestionsLoading(false);
      setSuggestionsDegraded(false);
      return;
    }
    let cancelled = false;
    const handle = window.setTimeout(() => {
      setSuggestionsLoading(true);
      void suggestDataRoutes(trimmed, SUGGEST_LIMIT)
        .then((payload) => {
          if (cancelled) return;
          setSuggestionsQuery(payload.query || trimmed);
          setSuggestionsDegraded(Boolean(payload.degraded));
          setSuggestions(
            (payload.suggestions || []).map((route) => ({
              reason: String(route.reason || "").trim(),
              item: {
                id: route.operationId,
                label: route.label,
                category: route.category,
                description: route.description,
                whenToUse: route.whenToUse,
                path: route.path,
                httpMethod: "GET" as const,
                metaShape: route.metaShape,
                valueFields: route.valueFields,
                displayKinds: resolveDataRouteDisplayKinds({
                  metaShape: route.metaShape,
                  allowedDisplayModes: route.allowedDisplayModes ?? route.suggestedDisplayModes,
                }),
                params: summarizeRouteParams(route.paramSchema, route.fixedQueryParams),
              },
            })),
          );
        })
        .catch(() => {
          if (cancelled) return;
          setSuggestions([]);
          setSuggestionsQuery(trimmed);
          setSuggestionsDegraded(true);
        })
        .finally(() => {
          if (!cancelled) setSuggestionsLoading(false);
        });
    }, SUGGEST_DEBOUNCE_MS);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [catalogQuery]);

  const draft: DataBuilderDraft = session?.draft ?? { sources: [], status: "draft" };
  const primarySource =
    draft.sources?.find((source) => source.localId === draft.primaryLocalId) ||
    draft.sources?.[0] ||
    null;
  const primaryRoute = useMemo(() => {
    if (!primarySource?.operationId) return null;
    return routes.find((route) => route.operationId === primarySource.operationId) || null;
  }, [primarySource?.operationId, routes]);

  const catalogItems = useMemo(
    () =>
      routes.map((route) => {
        const defaults = buildRouteDefaultParams(route);
        const params = summarizeRouteParams(route.paramSchema, route.fixedQueryParams).map(
          (param) => {
            const fromDefaults = defaults[param.key];
            if (fromDefaults === undefined || fromDefaults === null || fromDefaults === "") {
              return param;
            }
            return { ...param, default: fromDefaults as string | number | boolean };
          },
        );
        return {
          id: route.operationId,
          label: route.label,
          category: route.category,
          description: route.description,
          whenToUse: route.whenToUse,
          path: route.path,
          httpMethod: "GET" as const,
          metaShape: route.metaShape,
          valueFields: route.valueFields,
          displayKinds: resolveDataRouteDisplayKinds({
            metaShape: route.metaShape,
            allowedDisplayModes: route.allowedDisplayModes ?? route.suggestedDisplayModes,
          }),
          params,
        };
      }),
    [routes],
  );

  function applySession(next: DataBuilderSession) {
    setSession(next);
    const table = normalizePreview(next.preview);
    if (table) setPreviewTable(table);
  }

  async function runTurn(body: { action?: Record<string, unknown> }) {
    if (!session?.id || busy) return;
    setBusy(true);
    setError(null);
    try {
      const next = await dataBuilderTurn(session.id, body);
      applySession(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : C.sessionError);
    } finally {
      setBusy(false);
    }
  }

  function handleAddRoute(route: TvDataRouteCatalogItem, params?: DataRouteTestParams) {
    if (!route.operationId) return;
    const defaults = buildRouteDefaultParams(route);
    void runTurn({
      action: {
        type: "add_source",
        operationId: route.operationId,
        params: { ...defaults, ...(params ?? {}) },
      },
    });
  }

  async function handleTestCatalogRoute(
    item: DataRouteCatalogItem,
    params: DataRouteTestParams,
  ): Promise<DataRoutePreviewPayload> {
    const route = routes.find((entry) => entry.operationId === item.id);
    if (!route) {
      throw new Error("Rota não encontrada no catálogo.");
    }
    const block = createDataSourceBlock(route.operationId, {
      defaultParams: { ...buildRouteDefaultParams(route), ...params },
    });
    if (!block.dataBinding) {
      throw new Error("Bloco de fonte sem dataBinding.");
    }
    return previewTvDataRoute({
      route,
      block: block as typeof block & { dataBinding: NonNullable<typeof block.dataBinding> },
      config,
      playlistId,
      playlistDefaults,
    });
  }

  async function handlePreview() {
    if (!session?.id || busy) return;
    setBusy(true);
    setError(null);
    try {
      const result = await previewDataBuilderSession(session.id);
      if (result.session) applySession(result.session);
      const table = normalizePreview(result.preview);
      setPreviewTable(table);
      setPreviewExpanded(Boolean(table));
      if (!result.ok && result.message) setError(result.message);
      else if (table && !table.columns.length && !table.rowCount) setError(C.previewEmpty);
    } catch (err) {
      setError(err instanceof Error ? err.message : C.previewError);
    } finally {
      setBusy(false);
    }
  }

  function handlePrimaryParamsChange(updates: Record<string, string>) {
    if (!primarySource || !primaryRoute) return;
    const schema = visibleParamSchema(
      (primaryRoute.paramSchema || {}) as DataParamSchema,
      primaryRoute.fixedQueryParams,
    );
    const nextParams = applyDataParamRawUpdates(
      primarySource.params as Record<string, string | number | boolean | null | undefined>,
      updates,
      schema,
    );
    void runTurn({
      action: {
        type: "set_params",
        localId: primarySource.localId,
        params: nextParams,
      },
    });
  }

  async function handleUseOnSlide() {
    if (!session?.id || busy) return;
    setBusy(true);
    setError(null);
    try {
      const result = await materializeDataBuilderSession(session.id);
      const blocks = result.blocks || [];
      if (!blocks.length) {
        setError(result.message || C.materializeError);
        return;
      }

      const idMap: Record<string, string> = {};
      const prepared: ComunicadoDataSourceBlock[] = [];
      for (const block of blocks) {
        if (!block || typeof block !== "object") continue;
        const row = block as ComunicadoBlock;
        if (row.type !== "data_source") continue;
        const draftLocalId = String((row as { draftLocalId?: string }).draftLocalId || "");
        const nextBlock = { ...row } as ComunicadoDataSourceBlock;
        delete (nextBlock as { draftLocalId?: string }).draftLocalId;
        prepared.push(nextBlock);
        if (draftLocalId) idMap[draftLocalId] = nextBlock.id;
      }

      const finalized =
        prepared.length > 1
          ? prepared.map((block) => {
              const transform = remapTransformSourceIds(block.dataTransform, idMap);
              return transform ? { ...block, dataTransform: transform } : block;
            })
          : prepared;

      for (let index = 0; index < finalized.length; index += 1) {
        const nextBlock = finalized[index];
        if (mode === "replace" && index === 0) {
          replaceSelectedDataRoute(nextBlock);
        } else {
          addDataSourceBlock(nextBlock);
        }
      }

      if (result.session) applySession(result.session);
      onInserted?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : C.materializeError);
    } finally {
      setBusy(false);
    }
  }

  const canMaterialize = Boolean(session?.id) && draft.sources.length > 0 && !busy;
  const table = previewTable;
  const primarySchema = primaryRoute
    ? visibleParamSchema(
        (primaryRoute.paramSchema || {}) as DataParamSchema,
        primaryRoute.fixedQueryParams,
      )
    : {};

  const draftCount = draft.sources?.length ?? 0;
  const draftCountLabel = C.draftCount.replace("{count}", String(draftCount));

  return (
    <div className="td-data-builder-chat">
      <header className="td-data-builder-chat__chrome">
        <p className="td-data-builder-chat__mode-hint">{C.catalogHint}</p>
      </header>

      <div className="td-data-builder-chat__main">
        <div className="td-data-builder-chat__catalog" data-discovery="search">
          <DataRouteCatalogPanel
            items={catalogItems}
            onSelect={(item, params) => {
              const route = routes.find((entry) => entry.operationId === item.id);
              if (route) handleAddRoute(route, params);
            }}
            onTestRoute={handleTestCatalogRoute}
            density="compact"
            confirmLabel={C.addSuggestion}
            searchPlaceholder={DATA_ROUTE_CATALOG_CONTENT.searchPlaceholder}
            emptyMessage={C.catalogEmpty}
            loading={routesLoading}
            error={routesError}
            categoryLabels={CATEGORY_LABELS}
            categoryOrder={CATEGORY_ORDER}
            suggestions={suggestions}
            suggestionsLoading={suggestionsLoading}
            suggestionsQuery={suggestionsQuery}
            suggestionsDegraded={suggestionsDegraded}
            onQueryChange={setCatalogQuery}
          />
          {busy ? <p className="td-data-builder-chat__status">{C.loading}</p> : null}
          {error ? (
            <p className="td-data-builder-chat__status td-data-builder-chat__status--error" role="alert">
              {error}
            </p>
          ) : null}
        </div>
      </div>

      <footer className="td-data-builder-chat__draft-tray" aria-label={C.draftTitle}>
        <div className="td-data-builder-chat__draft-tray-bar">
          <div className="td-data-builder-chat__draft-tray-meta">
            <span className="td-data-builder-chat__draft-title">{C.draftTitle}</span>
            <span className="td-data-builder-chat__draft-meta">{draftCountLabel}</span>
          </div>
          <div className="td-data-builder-chat__actions">
            {table && previewExpanded ? (
              <button
                type="button"
                className="td-btn td-btn--sm td-btn--ghost"
                onClick={() => setPreviewExpanded(false)}
              >
                {C.hidePreview}
              </button>
            ) : null}
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              disabled={!canMaterialize}
              onClick={() => void handlePreview()}
            >
              {C.preview}
            </button>
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--primary"
              disabled={!canMaterialize}
              onClick={() => void handleUseOnSlide()}
            >
              {C.useOnSlide}
            </button>
          </div>
        </div>

        {draftCount === 0 ? (
          <p className="td-data-builder-chat__draft-empty">{C.draftEmpty}</p>
        ) : (
          <>
            <ul className="td-data-builder-chat__draft-chips">
              {draft.sources.map((source) => (
                <li key={source.localId}>
                  <span className="td-data-builder-chat__draft-chip">
                    {source.label || source.operationId}
                    {source.localId === draft.primaryLocalId ? ` · ${C.primaryMark}` : ""}
                    <button
                      type="button"
                      className="td-data-builder-chat__draft-chip-remove"
                      disabled={busy}
                      aria-label={C.removeSource}
                      onClick={() =>
                        void runTurn({
                          action: { type: "remove_source", localId: source.localId },
                        })
                      }
                    >
                      ×
                    </button>
                  </span>
                </li>
              ))}
            </ul>
            {primarySource && primaryRoute ? (
              <div className="td-data-builder-chat__draft-filters">
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--ghost"
                  aria-expanded={sourceFiltersOpen}
                  onClick={() => setSourceFiltersOpen((open) => !open)}
                >
                  {sourceFiltersOpen ? C.hideFilters : C.adjustFilters}
                </button>
                {sourceFiltersOpen ? (
                  <div className="td-data-builder-chat__config-source">
                    <h4 className="td-data-builder-chat__draft-title">{C.configSourceTitle}</h4>
                    <DataParamFields
                      schema={primarySchema}
                      values={primarySource.params || {}}
                      branchScope={branchScope}
                      openEndedDateRange={Boolean(primaryRoute.openEndedDateRange)}
                      onChange={handlePrimaryParamsChange}
                    />
                  </div>
                ) : null}
              </div>
            ) : null}
          </>
        )}

        {draft.transform?.steps?.length ? (
          <p className="td-data-builder-chat__draft-meta">
            Transform: {draft.transform.steps.map((step) => String(step.op || "?")).join(" → ")}
          </p>
        ) : null}

        {table && previewExpanded ? (
          <div className="td-data-builder-chat__preview" aria-label={C.previewTitle}>
            <h4 className="td-data-builder-chat__draft-title">{C.previewTitle}</h4>
            {table.columns.length ? (
              <div className="td-data-builder-chat__preview-scroll">
                <table>
                  <thead>
                    <tr>
                      {table.columns.map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {table.rows.map((row, rowIndex) => (
                      <tr key={`r-${rowIndex}`}>
                        {row.map((cell, cellIndex) => (
                          <td key={`c-${rowIndex}-${cellIndex}`}>{String(cell ?? "")}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="td-data-builder-chat__draft-empty">{C.previewEmpty}</p>
            )}
          </div>
        ) : null}
      </footer>
    </div>
  );
}
