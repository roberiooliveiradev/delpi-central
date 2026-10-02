/**
 * Corpos dos grupos/flyouts da aba «Dados» da ribbon.
 *
 * Tudo aqui consome o mesmo estado do painel lateral (`useComunicadoEditor`)
 * via `useDataRibbonModel` + hooks canônicos (link, view/text projection,
 * `applyDataParamUpdates`). Nenhum estado paralelo: mudar na ribbon atualiza
 * o painel e vice-versa no mesmo commit de estado (§40/§92 do redesign).
 */
import {
  dataModelOptionsForInspector,
  dataSourceOptionsForInspector,
  resolveDataBlockRefreshSec,
  TEXT_FIELD_AGGREGATION_OPTIONS,
  VIEW_AGGREGATION_OPTIONS,
  type KpiMetricProjection,
  type KpiViewProjection,
  type ViewAggregation,
} from "@delpi/tv-dashboard-presentation";

import { resolveParamFieldLabel } from "../content/dataParamCatalog";
import { TV_DASHBOARD_HELP_TOOLTIPS as H } from "../content/helpTooltips";
import {
  primaryTargetIds,
  type DataRibbonModel,
  type RibbonExpressionParam,
} from "../hooks/useDataRibbonModel";
import { usePrimaryDataTargetLink } from "../hooks/usePrimaryDataTargetLink";
import { useTextProjectionModel } from "../hooks/useTextProjectionModel";
import { useViewProjectionModel } from "../hooks/useViewProjectionModel";
import { buildParamValueUpdates } from "../utils/applyDataParamUpdates";
import { isDateParam, periodParamFieldKeys } from "../utils/dateRangePresets";
import {
  buildExpressionParamValue,
  isParamExpressionValue,
} from "../utils/paramExpressions";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import type { ExpressionEditRequest } from "./comunicadoEditorContextCore";
import {
  DataParamFields,
  type DataParamSchema,
} from "./DataParamFields";
import { DataRefreshIntervalField } from "./DataRefreshIntervalField";
import {
  DataSourceLinkSection,
  MODEL_TARGET_PREFIX,
} from "./DataSourceLinkSection";
import { DeckField } from "./deck/DeckField";
import { ExpressionSummaryCard } from "./ExpressionSummaryCard";
import {
  ChartAxesProjectionEditor,
  type ChartAxisFieldOption,
} from "./ChartAxesProjectionEditor";
import { KpiMetricsProjectionEditor } from "./KpiMetricsProjectionEditor";
import { TableColumnsMultiSelect } from "./TableColumnsMultiSelect";
import { TdRibbonSelect } from "./tdRibbonUi";

const FLYOUT_HINT = "td-deck-inspector__hint";

function RibbonHint({ children }: { children: string }) {
  return <p className={FLYOUT_HINT}>{children}</p>;
}

/* ------------------------------------------------------------------ */
/* Fonte                                                               */
/* ------------------------------------------------------------------ */

/** Select unificado Fonte/DataModel — mesma regra do `DataSourceLinkSection`. */
export function DataRibbonSourceSelect({ model }: { model: DataRibbonModel }) {
  const { blocks, config } = useComunicadoEditor();
  const link = usePrimaryDataTargetLink({
    fieldTypes: model.route?.valueFieldTypes ?? undefined,
  });
  const primary = model.primary;
  const { sourceId, modelId } = primaryTargetIds(primary);

  const sourceOptions = dataSourceOptionsForInspector(
    blocks,
    primary?.id,
    model.labelCatalog,
  );
  const modelOptions = dataModelOptionsForInspector({
    dataModels: config.dataModels ?? [],
  });
  const empty = sourceOptions.length === 0 && modelOptions.length === 0;

  return (
    <TdRibbonSelect
      aria-label="Fonte de dados"
      disabled={!primary || empty}
      value={modelId ? `${MODEL_TARGET_PREFIX}${modelId}` : sourceId}
      onChange={(value) => {
        if (!primary) return;
        if (value.startsWith(MODEL_TARGET_PREFIX)) {
          link.linkModel(primary, value.slice(MODEL_TARGET_PREFIX.length));
          return;
        }
        if (value) link.linkSource(primary, value);
        else link.unlink();
      }}
      options={[
        {
          value: "",
          label: empty ? "Nenhuma fonte no slide" : "Fonte…",
        },
        ...modelOptions.map((item) => ({
          value: `${MODEL_TARGET_PREFIX}${item.value}`,
          label: `Modelo · ${item.label}`,
        })),
        ...sourceOptions,
      ]}
    />
  );
}

/** Flyout «Fonte» — seletor canônico + atalho do catálogo. */
export function DataRibbonSourceFlyout({ model }: { model: DataRibbonModel }) {
  const { blocks, config, openDataCatalog } = useComunicadoEditor();
  const link = usePrimaryDataTargetLink({
    fieldTypes: model.route?.valueFieldTypes ?? undefined,
  });
  const primary = model.primary;
  const { sourceId, modelId } = primaryTargetIds(primary);

  if (!primary) {
    return <RibbonHint>Selecione um elemento com dados no palco.</RibbonHint>;
  }

  return (
    <>
      <DataSourceLinkSection
        embedded
        blocks={blocks}
        selectedId={primary.id}
        sourceId={sourceId}
        modelId={modelId}
        dataModels={config.dataModels ?? []}
        compactSelect="delpi-ui-select--compact"
        labelCatalog={model.labelCatalog}
        onChangeSourceId={(id) =>
          id ? link.linkSource(primary, id) : link.unlink()
        }
        onChangeModelId={(id) => link.linkModel(primary, id)}
        onOpenCatalog={() => openDataCatalog("replace")}
      />
      {model.targetCount > 1 ? (
        <RibbonHint>
          {`Fonte aplicada à referência — ${model.targetCount} elementos ligados na seleção.`}
        </RibbonHint>
      ) : null}
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Campo / Agregação                                                   */
/* ------------------------------------------------------------------ */

function patchKpiPrimaryMetric(
  projection: KpiViewProjection | null | undefined,
  patch: Partial<KpiMetricProjection>,
): KpiViewProjection {
  const metrics = [...(projection?.metrics ?? [])];
  const index = metrics.findIndex((metric) => metric.visible !== false);
  if (index < 0) {
    metrics.push({
      field: patch.field ?? "",
      aggregation: "first",
      visible: true,
      ...patch,
    });
  } else {
    metrics[index] = { ...metrics[index], ...patch };
  }
  return { ...projection, metrics };
}

/**
 * Controles inline expandidos de «Campo + Agregação» — KPI e texto/forma.
 * Gráfico/tabela voltam como tile de flyout (editor multi-coluna é largo).
 * Retorna null quando o contexto não tem projeção escalar.
 */
export function DataRibbonFieldControls({
  model,
}: {
  model: DataRibbonModel;
}) {
  const view = useViewProjectionModel(model.primary, model.route);
  const text = useTextProjectionModel(model.primary, model.route);

  if (view.viewType === "kpi_view" && view.view) {
    const projection =
      "kpiProjection" in view.view ? view.view.kpiProjection : null;
    const primary =
      projection?.metrics?.find((metric) => metric.visible !== false) ?? null;
    if (view.valueFieldOptions.length === 0) {
      return (
        <RibbonHint>Vincule uma fonte para escolher o campo.</RibbonHint>
      );
    }
    return (
      <>
        <TdRibbonSelect
          aria-label="Campo do KPI"
          value={primary?.field ?? ""}
          onChange={(value) =>
            view.applyKpiProjection(
              patchKpiPrimaryMetric(projection, { field: value }),
            )
          }
          options={[
            { value: "", label: "Campo…" },
            ...view.valueFieldOptions.map((opt) => ({
              value: opt.field,
              label: opt.label,
            })),
          ]}
        />
        <TdRibbonSelect
          aria-label="Agregação"
          value={primary?.aggregation ?? "first"}
          onChange={(value) =>
            view.applyKpiProjection(
              patchKpiPrimaryMetric(projection, {
                aggregation: value as ViewAggregation,
              }),
            )
          }
          options={VIEW_AGGREGATION_OPTIONS}
        />
      </>
    );
  }

  if (text.visualBox) {
    return (
      <>
        <TdRibbonSelect
          aria-label="Campo dinâmico"
          value={text.projection.field ?? ""}
          onChange={(value) =>
            text.patchProjection({ field: value || undefined })
          }
          options={[
            { value: "", label: "Campo…" },
            ...text.fieldOptions.map((opt) => ({
              value: opt.field,
              label: opt.label,
            })),
          ]}
        />
        <TdRibbonSelect
          aria-label="Agregação"
          value={text.projection.aggregation ?? "first"}
          onChange={(value) =>
            text.patchProjection({
              aggregation: value as ViewAggregation,
            })
          }
          options={TEXT_FIELD_AGGREGATION_OPTIONS}
        />
      </>
    );
  }

  return null;
}

/**
 * Flyout «Campo» — editores canônicos de projeção por tipo de visual
 * (mesmos componentes do painel lateral; `compact` reusa o CSS de flyout).
 */
export function DataRibbonFieldFlyout({ model }: { model: DataRibbonModel }) {
  const view = useViewProjectionModel(model.primary, model.route);
  const text = useTextProjectionModel(model.primary, model.route);

  if (!model.primary) {
    return <RibbonHint>Selecione um elemento com dados no palco.</RibbonHint>;
  }

  if (view.viewType === "kpi_view" && view.view && "kpiProjection" in view.view) {
    return (
      <KpiMetricsProjectionEditor
        idPrefix="td-ribbon-kpi"
        options={view.valueFieldOptions}
        kpiProjection={view.view.kpiProjection}
        onChange={view.applyKpiProjection}
        compact
      />
    );
  }

  if (view.viewType === "chart_view" && view.view && "chartProjection" in view.view) {
    return (
      <ChartAxesProjectionEditor
        idPrefix="td-ribbon-chart"
        options={view.valueFieldOptions as ChartAxisFieldOption[]}
        chartProjection={view.view.chartProjection}
        chartType={view.view.chartType}
        onChange={view.applyChartProjection}
        compact
      />
    );
  }

  if (view.viewType === "table_view" && view.view && "tableProjection" in view.view) {
    return (
      <TableColumnsMultiSelect
        idPrefix="td-ribbon-table"
        options={view.tableColumnOptions}
        tableProjection={view.view.tableProjection}
        onChange={view.applyTableProjection}
        onRenameField={view.renameField}
        sourceFieldLabels={view.sourceFieldLabels}
        compact
      />
    );
  }

  if (text.visualBox) {
    return (
      <>
        <DeckField label="Campo dinâmico" id="td-ribbon-text-field">
          <TdRibbonSelect
            aria-label="Campo dinâmico"
            value={text.projection.field ?? ""}
            onChange={(value) =>
              text.patchProjection({ field: value || undefined })
            }
            options={[
              { value: "", label: "Campo…" },
              ...text.fieldOptions.map((opt) => ({
                value: opt.field,
                label: opt.label,
              })),
            ]}
          />
        </DeckField>
        <DeckField label="Agregação" id="td-ribbon-text-aggregation">
          <TdRibbonSelect
            aria-label="Agregação"
            value={text.projection.aggregation ?? "first"}
            onChange={(value) =>
              text.patchProjection({ aggregation: value as ViewAggregation })
            }
            options={TEXT_FIELD_AGGREGATION_OPTIONS}
          />
        </DeckField>
      </>
    );
  }

  return (
    <RibbonHint>
      Este elemento usa a fonte diretamente — configure parâmetros no grupo
      «Mais» e colunas na Grade.
    </RibbonHint>
  );
}

/* ------------------------------------------------------------------ */
/* Período / Atualização                                               */
/* ------------------------------------------------------------------ */

/** Flyout «Período» — recorte do `DataParamFields` canônico (preset + datas). */
export function DataRibbonPeriodFlyout({ model }: { model: DataRibbonModel }) {
  const periodKeys = periodParamFieldKeys(Object.keys(model.paramSchema));

  if ((!model.bindingTarget && !model.bindingModel) || Object.keys(model.paramSchema).length === 0) {
    return <RibbonHint>Vincule uma fonte para configurar o período.</RibbonHint>;
  }

  return (
    <>
      {model.bindingModel ? (
        <RibbonHint>Aplica às rotas compatíveis do modelo ligado.</RibbonHint>
      ) : null}
      <DataParamFields
        schema={model.paramSchema}
        values={model.params}
        divergedKeys={model.bindingModel ? model.modelDivergedKeys : undefined}
        layout="pane"
        idPrefix="td-ribbon-period"
        openEndedDateRange={Boolean(model.route?.openEndedDateRange)}
        expressionSupport={model.expressionSupport}
        fixedQueryParams={model.bindingModel ? undefined : model.route?.fixedQueryParams}
        onlyParams={periodKeys}
        filterLayer={model.bindingModel ? "multi" : undefined}
        resolved={model.resolved}
        onChange={model.updateParams}
      />
    </>
  );
}

/**
 * Flyout «Atualização» — `refreshSec` da fonte (mesmo campo do inspector).
 * Visual ligado a DataModel: modelo não tem refreshSec próprio — expõe a
 * ação manual «Atualizar dados» (force refresh do modelo, ignora cache).
 */
export function DataRibbonRefreshFlyout({ model }: { model: DataRibbonModel }) {
  const { globalRefreshSec, refreshDataPreview, refreshingSourceIds } =
    useComunicadoEditor();

  if (model.bindingModel) {
    const refreshing = refreshingSourceIds.includes(model.bindingModel.id);
    return (
      <>
        <button
          type="button"
          className="td-btn td-btn--sm"
          disabled={refreshing}
          aria-busy={refreshing}
          onClick={() =>
            void refreshDataPreview({
              force: true,
              blockIds: [model.bindingModel!.id],
            })
          }
        >
          {refreshing ? "Atualizando…" : "Atualizar dados"}
        </button>
        <RibbonHint>{H.data.modelForceRefresh}</RibbonHint>
      </>
    );
  }

  if (!model.binding) {
    return <RibbonHint>Vincule uma fonte para definir o intervalo.</RibbonHint>;
  }

  return (
    <DataRefreshIntervalField
      refreshSec={model.binding.refreshSec}
      inheritedRefreshSec={resolveDataBlockRefreshSec(undefined, globalRefreshSec)}
      compact
      id="td-ribbon-refresh"
      onChange={(sec) => {
        const next = { ...model.binding };
        if (sec == null) delete next.refreshSec;
        else next.refreshSec = sec;
        model.applyBinding(next);
      }}
    />
  );
}

/* ------------------------------------------------------------------ */
/* Expressão                                                           */
/* ------------------------------------------------------------------ */

function defaultExpressionAst(isDate: boolean) {
  return isDate
    ? { kind: "identifier" as const, value: "today" }
    : { kind: "literal" as const, value: "" };
}



/**
 * Flyout «Expressão» — cartões-resumo por parâmetro + «Nova expressão».
 * A edição acontece só no drawer (draft local até «Aplicar»); este flyout
 * nunca avalia nem persiste AST diretamente.
 */
export function DataRibbonExpressionFlyout({
  model,
}: {
  model: DataRibbonModel;
}) {
  const { openExpressionEditor } = useComunicadoEditor();
  const capable = model.expressionParams;

  if (!model.bindingTarget && !model.bindingModel) {
    return <RibbonHint>Vincule uma fonte para usar expressões.</RibbonHint>;
  }
  if (capable.length === 0) {
    return (
      <RibbonHint>
        {model.bindingModel
          ? "Nenhum parâmetro do modelo aceita expressão."
          : "Esta fonte não expõe parâmetros editáveis por expressão."}
      </RibbonHint>
    );
  }

  const openRequest = (item: RibbonExpressionParam) => {
    const current = model.params?.[item.key];
    const spec = isParamExpressionValue(current)
      ? current
      : buildExpressionParamValue(
          defaultExpressionAst(isDateParam(item.key, item.field)),
        );
    const request: ExpressionEditRequest = {
      paramKey: item.key,
      paramLabel: item.label,
      spec,
      expectedReturnTypes: item.expectedReturnTypes,
      refParamKeys: Object.keys(model.paramSchema).map((key) => ({
        key,
        label: resolveParamFieldLabel(
          key,
          model.paramSchema[key]?.label,
        ),
      })),
      previewBlockId: model.bindingTarget?.id ?? null,
      apply: (nextSpec) =>
        model.updateParams(
          buildParamValueUpdates(item.key, nextSpec, {
            schema: model.paramSchema as DataParamSchema,
            values: model.params,
          }),
        ),
    };
    openExpressionEditor(request);
  };

  return (
    <>
      {capable.map((item) => {
        const current = model.params?.[item.key];
        const spec = isParamExpressionValue(current) ? current : null;
        return (
          <DeckField
            key={item.key}
            id={`td-ribbon-expr-${item.key}`}
            label={item.label}
            hint={H.data.paramExpression}
          >
            {spec ? (
              <ExpressionSummaryCard
                spec={spec}
                paramKey={item.key}
                resolved={model.resolved}
                onEdit={() => openRequest(item)}
              />
            ) : (
              <button
                type="button"
                className="td-btn td-btn--sm td-btn--ghost"
                onClick={() => openRequest(item)}
              >
                Nova expressão…
              </button>
            )}
          </DeckField>
        );
      })}
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Mais (demais parâmetros + ações do painel)                          */
/* ------------------------------------------------------------------ */

/** Flyout «Mais» — params fora do grupo Período + navegação para o painel. */
export function DataRibbonMoreFlyout({ model }: { model: DataRibbonModel }) {
  const { setDataPanelOpen, setDataPanelIntent, setSelectionPanelTab } =
    useComunicadoEditor();
  const link = usePrimaryDataTargetLink({
    fieldTypes: model.route?.valueFieldTypes ?? undefined,
  });
  const periodKeys = periodParamFieldKeys(Object.keys(model.paramSchema));

  return (
    <>
      {(model.bindingTarget || model.bindingModel) &&
      Object.keys(model.paramSchema).length > 0 ? (
        <DataParamFields
          schema={model.paramSchema}
          values={model.params}
          divergedKeys={model.bindingModel ? model.modelDivergedKeys : undefined}
          layout="pane"
          idPrefix="td-ribbon-more"
          openEndedDateRange={Boolean(model.route?.openEndedDateRange)}
          expressionSupport={model.expressionSupport}
          fixedQueryParams={model.bindingModel ? undefined : model.route?.fixedQueryParams}
          excludeParams={periodKeys}
          filterLayer={model.bindingModel ? "multi" : undefined}
          resolved={model.resolved}
          onChange={model.updateParams}
        />
      ) : (
        <RibbonHint>
          Selecione um elemento com dados ou vincule uma fonte.
        </RibbonHint>
      )}
      <button
        type="button"
        className="td-btn td-btn--sm td-btn--ghost"
        onClick={() => {
          setDataPanelOpen(true);
          setDataPanelIntent("binding");
          setSelectionPanelTab("data");
        }}
      >
        Abrir painel de dados…
      </button>
      {model.primary && (model.binding || model.bindingModel) ? (
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--ghost"
          onClick={() => link.unlink()}
        >
          {model.bindingModel ? "Desvincular modelo" : "Desvincular fonte"}
        </button>
      ) : null}
    </>
  );
}
