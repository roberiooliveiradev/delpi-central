import {
  chartTypeLabel,
  discoverResolvedFieldOptions,
  catalogFieldsFromRouteLabels,
  isDataSourceBlockType,
  buildViewDataLinkPatch,
  buildViewFrameFitPatch,
  patchFieldLabels,
  tablePresetLabel,
  type ComunicadoBlock,
  type ComunicadoDataSourceBlock,
  type ComunicadoTableViewBlock,
  type ChartViewProjection,
  type KpiViewProjection,
  type TableViewProjection,
} from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataSourceLinkSection } from "./DataSourceLinkSection";
import type { PanelLayout } from "./SelectedDataSidePanel";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { ChartAxesProjectionEditor } from "./ChartAxesProjectionEditor";
import { KpiMetricsProjectionEditor } from "./KpiMetricsProjectionEditor";
import { TableColumnsMultiSelect, resolveVisibleKeys } from "./TableColumnsMultiSelect";
import type { ValueFieldOption } from "./ValueFieldsMultiSelect";
import type { DataSourceLabelCatalog } from "@delpi/tv-dashboard-presentation";

type Props = {
  pane?: boolean;
  layout?: PanelLayout;
  /** Abre aba Dados do painel lateral (catálogo de fontes). */
  onOpenDataSources?: () => void;
  /** Rota da fonte ligada (labels de valueFields). */
  route?: TvDataRouteCatalogItem | null;
  labelCatalog?: DataSourceLabelCatalog | null;
  /**
   * `connection` — só vínculo com a fonte (aba Elemento / Design).
   * `full` — eixos, séries, colunas, métricas (aba Dados).
   * Misturar full na aba Elemento enche o painel e “esvazia” o Design.
   */
  mode?: "connection" | "full";
};

function viewValueFieldOptions(
  route: TvDataRouteCatalogItem | null | undefined,
  source: ComunicadoBlock | null,
): ValueFieldOption[] {
  const catalog = catalogFieldsFromRouteLabels(route?.valueFields, route?.valueFieldLabels);
  const resolved =
    source && "resolved" in source && source.resolved ? source.resolved : undefined;
  const sourceFieldLabels =
    source && isDataSourceBlockType(source.type)
      ? (source as ComunicadoDataSourceBlock).fieldLabels
      : undefined;
  return discoverResolvedFieldOptions(resolved, catalog, sourceFieldLabels);
}

export function VisualDataViewInspector({
  pane = false,
  layout = "pane",
  onOpenDataSources,
  route = null,
  labelCatalog = null,
  mode = "full",
}: Props) {
  const {
    selected,
    blocks,
    updateSelected,
    updateBlock,
    openDataCatalog,
    openDataPanel,
    selectedKpiPart,
    selectedChartPart,
    selectedTablePart,
    selectChartPart,
    selectTablePart,
    reconcileTablePartsForVisibleKeys,
    reconcileChartPartForSeriesFields,
  } = useComunicadoEditor();
  const isRibbon = layout === "ribbon";
  const compactSelect = isRibbon ? "delpi-ui-select--compact" : undefined;
  const showProjectionEditors = mode === "full";

  if (
    !selected ||
    (selected.type !== "chart_view" &&
      selected.type !== "kpi_view" &&
      selected.type !== "table_view")
  ) {
    return null;
  }

  const hasSource = Boolean(selected.dataSourceId?.trim());
  const openSources = onOpenDataSources ?? (() => openDataCatalog("insert"));
  const tableBlock = selected.type === "table_view" ? (selected as ComunicadoTableViewBlock) : null;
  const linkedSource =
    hasSource
      ? blocks.find(
          (block) =>
            block.id === selected.dataSourceId && isDataSourceBlockType(block.type),
        ) ?? null
      : null;
  const valueFieldOptions = viewValueFieldOptions(route, linkedSource).map((item) => ({
    ...item,
    fieldType: route?.valueFieldTypes?.[item.field],
  }));
  const tableColumnOptions = valueFieldOptions.map((item) => ({
    key: item.field,
    label: item.label,
  }));

  const applyTableProjection = (next: TableViewProjection | undefined) => {
    const prevVisible = resolveVisibleKeys(tableColumnOptions, tableBlock?.tableProjection);
    const nextVisible = resolveVisibleKeys(tableColumnOptions, next);
    reconcileTablePartsForVisibleKeys(prevVisible, nextVisible);
    const framePatch = buildViewFrameFitPatch({
      ...selected,
      tableProjection: next,
    } as ComunicadoBlock);
    updateSelected({
      tableProjection: next,
      ...(framePatch ?? {}),
    } as Partial<ComunicadoTableViewBlock>);
  };

  const applyKpiProjection = (next: KpiViewProjection | undefined) => {
    const framePatch = buildViewFrameFitPatch({
      ...selected,
      kpiProjection: next,
    } as ComunicadoBlock);
    updateSelected({
      kpiProjection: next,
      ...(framePatch ?? {}),
    } as Partial<ComunicadoBlock>);
  };

  const applyChartProjection = (next: ChartViewProjection | undefined) => {
    const prevFields = (selected.type === "chart_view" ? selected.chartProjection?.series : null)?.map(
      (item) => item.field,
    ) ?? [];
    const nextFields = (next?.series ?? []).map((item) => item.field);
    reconcileChartPartForSeriesFields(prevFields, nextFields);
    const framePatch = buildViewFrameFitPatch({
      ...selected,
      chartProjection: next,
    } as ComunicadoBlock);
    updateSelected({
      chartProjection: next,
      ...(framePatch ?? {}),
    } as Partial<ComunicadoBlock>);
  };

  const connectionBody = (
    <>
      {selected.type === "chart_view" ? (
        <p className="td-deck-inspector__meta">Gráfico: {chartTypeLabel(selected.chartType)}</p>
      ) : selected.type === "kpi_view" ? (
        <p className="td-deck-inspector__meta">Card KPI</p>
      ) : (
        <p className="td-deck-inspector__meta">Tabela: {tablePresetLabel(selected.tablePreset)}</p>
      )}
      {!hasSource && !isRibbon ? (
        <div className="td-deck-inspector__onboarding">
          <p className="td-deck-inspector__hint">{TV_DASHBOARD_HELP_TOOLTIPS.data.connectFlow}</p>
        </div>
      ) : null}
      {!hasSource && isRibbon ? (
        <p className="td-deck-inspector__hint">{TV_DASHBOARD_HELP_TOOLTIPS.data.connectFlowRibbon}</p>
      ) : null}
      <DataSourceLinkSection
        embedded
        blocks={blocks}
        selectedId={selected.id}
        sourceId={selected.dataSourceId ?? ""}
        compactSelect={compactSelect}
        pane={!isRibbon}
        labelCatalog={labelCatalog}
        onChangeSourceId={(value) => {
            const sourceId = value || undefined;
            if (!sourceId) {
              updateSelected({ dataSourceId: undefined } as Partial<ComunicadoBlock>);
              return;
            }
            const source = blocks.find(
              (block) => block.id === sourceId && isDataSourceBlockType(block.type),
            );
            const resolved =
              source && "resolved" in source ? source.resolved : undefined;
            const patch = buildViewDataLinkPatch({
              viewType: selected.type,
              dataSourceId: sourceId,
              resolved,
              fieldTypes: route?.valueFieldTypes ?? null,
              currentFrame: selected.frame,
              existing: {
                kpiProjection: "kpiProjection" in selected ? selected.kpiProjection : undefined,
                chartProjection:
                  "chartProjection" in selected ? selected.chartProjection : undefined,
                tableProjection:
                  "tableProjection" in selected ? selected.tableProjection : undefined,
              },
              chartType: selected.type === "chart_view" ? selected.chartType : undefined,
            });
            updateSelected(patch as Partial<ComunicadoBlock>);
          }}
        onOpenCatalog={openSources}
        catalogLabel="Inserir nova fonte…"
        emptyHint={
          hasSource
            ? undefined
            : "Escolha uma fonte deste slide ou insira uma nova no catálogo."
        }
      />
      {showProjectionEditors &&
      hasSource &&
      selected.type === "chart_view" &&
      valueFieldOptions.length > 0 ? (
        <DeckField
          id="td-view-chart-axes"
          label="Eixos e séries"
          hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartAxesProjection}
        >
          <ChartAxesProjectionEditor
            idPrefix="td-view-chart-axis"
            options={valueFieldOptions}
            chartProjection={"chartProjection" in selected ? selected.chartProjection : undefined}
            chartType={selected.chartType}
            compact={isRibbon}
            onChange={applyChartProjection}
            focusedSeriesField={
              selectedChartPart?.kind === "series"
                ? selected.chartProjection?.series?.[selectedChartPart.seriesIndex ?? -1]?.field ??
                  null
                : null
            }
            onSeriesActivate={(_field, seriesIndex) => {
              if (seriesIndex < 0) return;
              selectChartPart(selected.id, { kind: "series", seriesIndex });
            }}
          />
        </DeckField>
      ) : null}
      {showProjectionEditors &&
      hasSource &&
      selected.type === "kpi_view" &&
      valueFieldOptions.length > 0 ? (
        <DeckField
          id="td-view-kpi-metrics"
          label="Métricas neste KPI"
          hint={TV_DASHBOARD_HELP_TOOLTIPS.data.kpiMetricsProjection}
        >
          <KpiMetricsProjectionEditor
            idPrefix="td-view-kpi-metric"
            options={valueFieldOptions}
            kpiProjection={"kpiProjection" in selected ? selected.kpiProjection : undefined}
            compact={isRibbon}
            onChange={applyKpiProjection}
            focusedMetricField={
              selectedKpiPart?.kind === "metricCard" ? selectedKpiPart.field : null
            }
          />
        </DeckField>
      ) : null}
      {showProjectionEditors &&
      hasSource &&
      selected.type === "table_view" &&
      tableColumnOptions.length > 0 ? (
        <DeckField
          id="td-view-table-columns"
          label="Colunas neste visual"
          hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableColumns}
        >
          <TableColumnsMultiSelect
            idPrefix="td-view-table-col"
            options={tableColumnOptions}
            tableProjection={tableBlock?.tableProjection}
            compact={isRibbon}
            onChange={applyTableProjection}
            focusedColumnKey={
              selectedTablePart?.kind === "headerCell" && selectedTablePart.colIndex != null
                ? resolveVisibleKeys(tableColumnOptions, tableBlock?.tableProjection)[
                    selectedTablePart.colIndex
                  ] ?? null
                : null
            }
            onSelectColumn={(key) => {
              const visibleKeys = resolveVisibleKeys(
                tableColumnOptions,
                tableBlock?.tableProjection,
              );
              const colIndex = visibleKeys.indexOf(key);
              if (colIndex < 0) return;
              selectTablePart(selected.id, { kind: "headerCell", colIndex });
            }}
            sourceFieldLabels={
              linkedSource && isDataSourceBlockType(linkedSource.type)
                ? (linkedSource as ComunicadoDataSourceBlock).fieldLabels
                : undefined
            }
            onRenameField={
              linkedSource && isDataSourceBlockType(linkedSource.type)
                ? (key, label) => {
                    const source = linkedSource as ComunicadoDataSourceBlock;
                    updateBlock(source.id, {
                      fieldLabels: patchFieldLabels(source.fieldLabels, key, label),
                    } as Partial<ComunicadoBlock>);
                  }
                : undefined
            }
          />
        </DeckField>
      ) : null}
      {!showProjectionEditors && hasSource && !isRibbon ? (
        <div className="td-deck-inspector__actions" style={{ paddingTop: 8 }}>
          <button
            type="button"
            className="td-btn td-btn--sm"
            onClick={() => openDataPanel()}
          >
            {selected.type === "chart_view"
              ? "Eixos e séries na aba Dados"
              : selected.type === "table_view"
                ? "Colunas na aba Dados"
                : "Métricas na aba Dados"}
          </button>
        </div>
      ) : null}
    </>
  );

  if (isRibbon) {
    return (
      <>
        <div className="td-deck-ribbon__panel-zone">
          <h4 className="td-deck-ribbon__panel-zone-title">Conexão</h4>
          <div className="td-deck-ribbon__field-grid">{connectionBody}</div>
        </div>
      </>
    );
  }

  return (
    <>
      <DeckPropertySection
        pane={pane}
        title="Conexão de dados"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.data.viewBinding}
        defaultOpen={showProjectionEditors || !hasSource}
      >
        {connectionBody}
      </DeckPropertySection>
    </>
  );
}
