import {
  chartTypeLabel,
  discoverResolvedFieldOptions,
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
import { TableColumnsMultiSelect } from "./TableColumnsMultiSelect";
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
};

function viewValueFieldOptions(
  route: TvDataRouteCatalogItem | null | undefined,
  source: ComunicadoBlock | null,
): ValueFieldOption[] {
  const labels = route?.valueFieldLabels ?? {};
  const catalog = (route?.valueFields ?? [])
    .map((field) => String(field).trim())
    .filter(Boolean)
    .map((field) => ({
      field,
      label: labels[field]?.trim() || field,
    }));
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
}: Props) {
  const {
    selected,
    blocks,
    updateSelected,
    updateBlock,
    openDataCatalog,
    selectedKpiPart,
    selectedChartPart,
    selectChartPart,
  } = useComunicadoEditor();
  const isRibbon = layout === "ribbon";
  const compactSelect = isRibbon ? "delpi-ui-select--compact" : undefined;

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
      {hasSource && selected.type === "chart_view" && valueFieldOptions.length > 0 ? (
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
              selectChartPart(selected.id, { kind: "series", seriesIndex });
            }}
          />
        </DeckField>
      ) : null}
      {hasSource && selected.type === "kpi_view" && valueFieldOptions.length > 0 ? (
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
      {hasSource && selected.type === "table_view" && tableColumnOptions.length > 0 ? (
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
        defaultOpen={!hasSource}
      >
        {connectionBody}
      </DeckPropertySection>
    </>
  );
}
