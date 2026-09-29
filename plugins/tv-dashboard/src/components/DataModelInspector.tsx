import { useEffect, useMemo, useState } from "react";
import {
  discoverResolvedFieldOptions,
  resolveDataBlockErrorText,
  type DataParamValue,
  type TvDataModel,
  type TvDataModelInput,
} from "@delpi/tv-dashboard-presentation";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useParamExpressionCapability } from "../hooks/useParamExpressionCapability";
import { useTvDataRouteLabelCatalog } from "../hooks/useTvDataRouteLabelCatalog";
import {
  applyDataParamRawUpdates,
  type DataParamUpdateValue,
} from "../utils/applyDataParamUpdates";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataParamFields, visibleParamSchema } from "./DataParamFields";
import type { PanelLayout } from "./SelectedDataSidePanel";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  model: TvDataModel;
  pane?: boolean;
  layout?: PanelLayout;
};

/**
 * Inspector de DataModel — objeto lógico de dados (nunca visual).
 * Inspect inputs/transform, preview output (ready/loading/error/empty),
 * rename label e delete via mutation ops do backend.
 */
export function DataModelInspector({ model, pane = false, layout = "pane" }: Props) {
  const {
    getDataPreviewResolved,
    refreshingSourceIds,
    refreshDataPreview,
    saveDataModel,
    deleteDataModel,
  } = useComunicadoEditor();
  const { routes } = useTvDataRouteLabelCatalog();
  const isRibbon = layout === "ribbon";
  // Capability do catálogo vivo (`/data/m/functions`) — modo Expressão nos inputs.
  const expressionSupport = useParamExpressionCapability();

  const [labelDraft, setLabelDraft] = useState(model.label ?? "");
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  /** Rascunho local por input — save explícito via `upsert_data_model` governado. */
  const [paramDrafts, setParamDrafts] = useState<
    Record<string, Record<string, DataParamValue | null | undefined>>
  >({});

  useEffect(() => {
    setParamDrafts({});
    setLabelDraft(model.label ?? "");
  }, [model.id, model.label]);

  const resolved = getDataPreviewResolved?.(model.id);
  const loading = refreshingSourceIds.includes(model.id);
  const errorText = resolveDataBlockErrorText(resolved);

  const outputFields = useMemo(
    () => discoverResolvedFieldOptions(resolved, undefined, model.fieldLabels),
    [resolved, model.fieldLabels],
  );

  const routeById = useMemo(() => {
    const map = new Map<string, (typeof routes)[number]>();
    for (const route of routes) {
      if (route.operationId) map.set(route.operationId, route);
    }
    return map;
  }, [routes]);
  const routeLabelById = useMemo(() => {
    const map = new Map<string, string>();
    for (const [operationId, route] of routeById) {
      map.set(operationId, route.label ?? operationId);
    }
    return map;
  }, [routeById]);

  const isEmpty =
    !loading &&
    !errorText &&
    resolved != null &&
    outputFields.length === 0;

  const status = loading
    ? "Carregando modelo…"
    : errorText
      ? `Erro no modelo: ${errorText}`
      : isEmpty
        ? "Resultado vazio — o modelo respondeu sem campos."
        : resolved
          ? "Pronto"
          : "Sem preview ainda — atualize para carregar.";

  const saveLabel = () => {
    const next = { ...model, label: labelDraft.trim() || undefined };
    if (next.label === model.label) return;
    setBusy(true);
    setActionError(null);
    void saveDataModel(next)
      .catch((err: unknown) => {
        setActionError(err instanceof Error ? err.message : "Falha ao salvar o modelo.");
      })
      .finally(() => setBusy(false));
  };

  const stableParamsJson = (params: Record<string, unknown> | undefined) => {
    const keys = Object.keys(params ?? {}).sort();
    const normalized: Record<string, unknown> = {};
    for (const key of keys) {
      const value = params?.[key];
      if (value !== undefined && value !== null && value !== "") normalized[key] = value;
    }
    return JSON.stringify(normalized);
  };

  const patchInputParams = (
    input: TvDataModelInput,
    updates: Record<string, DataParamUpdateValue>,
  ) => {
    const route = routeById.get(input.operationId);
    const schema = visibleParamSchema(
      route?.paramSchema as Parameters<typeof visibleParamSchema>[0],
      route?.fixedQueryParams,
    );
    const base = paramDrafts[input.id] ?? input.params ?? {};
    const next = applyDataParamRawUpdates(base, updates, schema);
    setParamDrafts((prev) => ({ ...prev, [input.id]: next }));
  };

  const saveInputParams = (input: TvDataModelInput) => {
    const draft = paramDrafts[input.id];
    if (!draft) return;
    const nextModel: TvDataModel = {
      ...model,
      inputs: model.inputs.map((item) =>
        item.id === input.id
          ? { ...item, params: { ...(draft as Record<string, DataParamValue>) } }
          : item,
      ),
    };
    setBusy(true);
    setActionError(null);
    void saveDataModel(nextModel)
      .then(() => {
        setParamDrafts((prev) => {
          const next = { ...prev };
          delete next[input.id];
          return next;
        });
      })
      .catch((err: unknown) => {
        setActionError(
          err instanceof Error ? err.message : "Falha ao salvar os parâmetros do modelo.",
        );
      })
      .finally(() => setBusy(false));
  };

  const discardInputParams = (input: TvDataModelInput) => {
    setParamDrafts((prev) => {
      const next = { ...prev };
      delete next[input.id];
      return next;
    });
  };

  const onDelete = () => {
    setBusy(true);
    setActionError(null);
    void deleteDataModel(model.id)
      .catch((err: unknown) => {
        setActionError(
          err instanceof Error ? err.message : "Não foi possível excluir o modelo.",
        );
      })
      .finally(() => setBusy(false));
  };

  if (isRibbon) {
    return (
      <p className="td-deck-inspector__hint">
        Modelo «{model.label?.trim() || model.id}» — {model.inputs.length} rota(s). Detalhes no
        painel Dados.
      </p>
    );
  }

  return (
    <>
      <DeckPropertySection
        pane={pane}
        title="Modelo de dados"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.data.modelInspector}
        defaultOpen
      >
        <p className="td-deck-inspector__meta" title={model.id}>
          {model.inputs.length === 1
            ? "1 rota de dados"
            : `${model.inputs.length} rotas de dados`}
          {model.transform ? " · transform" : ""}
        </p>
        <DeckField label="Nome do modelo">
          <div className="td-deck-ribbon__toolbar-row">
            <NativeTextControl
              value={labelDraft}
              onChange={setLabelDraft}
              placeholder={model.id}
            />
            <button
              type="button"
              className="td-btn td-btn--sm"
              disabled={busy}
              onClick={saveLabel}
            >
              Salvar
            </button>
          </div>
        </DeckField>
        <p
          className={
            errorText
              ? "td-deck-inspector__hint td-deck-inspector__hint--error"
              : "td-deck-inspector__hint"
          }
          role={errorText ? "alert" : undefined}
        >
          {status}
        </p>
        {actionError ? (
          <p className="td-deck-inspector__hint td-deck-inspector__hint--error" role="alert">
            {actionError}
          </p>
        ) : null}
        <div className="td-deck-ribbon__toolbar-row">
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={loading}
            onClick={() =>
              void refreshDataPreview({ force: true, blockIds: [model.id] })
            }
          >
            {loading ? "Carregando…" : "Atualizar preview"}
          </button>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            disabled={busy}
            onClick={onDelete}
          >
            Excluir modelo
          </button>
        </div>
      </DeckPropertySection>

      <DeckPropertySection pane={pane} title="Rotas do modelo" defaultOpen>
        <ul className="td-project-sources-list">
          {model.inputs.map((input) => {
            const route = routeById.get(input.operationId);
            const inputSchema = visibleParamSchema(
              route?.paramSchema as Parameters<typeof visibleParamSchema>[0],
              route?.fixedQueryParams,
            );
            const draft = paramDrafts[input.id];
            const hasDraft = draft != null && stableParamsJson(draft) !== stableParamsJson(input.params);
            return (
              <li key={input.id} className="td-project-sources-list__item--static">
                <span className="td-project-sources-list__label">
                  {input.label?.trim() || routeLabelById.get(input.operationId) || input.operationId}
                </span>
                <span className="td-project-sources-list__meta">
                  {input.operationId}
                  {input.id === model.primaryInputId ? " · principal" : ""}
                  {input.transform ? " · transform" : ""}
                  {input.params && Object.keys(input.params).length > 0
                    ? ` · ${Object.keys(input.params).length} parâmetro(s)`
                    : ""}
                </span>
                {route && Object.keys(inputSchema).length > 0 ? (
                  <details className="td-data-model-input-params">
                    <summary>Parâmetros</summary>
                    <DataParamFields
                      schema={inputSchema}
                      values={(draft ?? input.params) as
                        | Record<string, DataParamValue | null | undefined>
                        | undefined}
                      idPrefix={`td-model-input-${input.id}`}
                      expressionSupport={expressionSupport}
                      fixedQueryParams={route.fixedQueryParams}
                      onChange={(updates) => patchInputParams(input, updates)}
                    />
                    {hasDraft ? (
                      <div className="td-deck-ribbon__toolbar-row">
                        <button
                          type="button"
                          className="td-btn td-btn--sm"
                          disabled={busy}
                          onClick={() => saveInputParams(input)}
                        >
                          Salvar parâmetros
                        </button>
                        <button
                          type="button"
                          className="td-btn td-btn--sm td-btn--ghost"
                          disabled={busy}
                          onClick={() => discardInputParams(input)}
                        >
                          Descartar
                        </button>
                      </div>
                    ) : null}
                  </details>
                ) : null}
              </li>
            );
          })}
        </ul>
      </DeckPropertySection>

      {outputFields.length > 0 ? (
        <DeckPropertySection pane={pane} title="Campos de saída" defaultOpen={false}>
          <ul className="td-project-sources-list">
            {outputFields.map((item) => (
              <li key={item.field} className="td-project-sources-list__item--static">
                <span className="td-project-sources-list__label">{item.label}</span>
                <span className="td-project-sources-list__meta">{item.field}</span>
              </li>
            ))}
          </ul>
        </DeckPropertySection>
      ) : null}
    </>
  );
}
