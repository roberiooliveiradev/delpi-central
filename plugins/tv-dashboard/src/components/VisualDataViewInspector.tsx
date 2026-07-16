import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  TABLE_VIEW_MAX_COLS_CAP,
  TABLE_VIEW_MAX_ROWS_CAP,
  chartTypeLabel,
  dataSourceOptionsForInspector,
  discoverResolvedFieldOptions,
  isDataSourceBlockType,
  normalizeTableViewLimit,
  buildViewDataLinkPatch,
  buildViewFrameFitPatch,
  tablePresetLabel,
  type ComunicadoBlock,
  type ComunicadoTableViewBlock,
  type ChartViewProjection,
  type KpiViewProjection,
  type TableViewProjection,
} from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import type { PanelLayout } from "./SelectedDataSidePanel";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import { ChartAxesProjectionEditor } from "./ChartAxesProjectionEditor";
import { KpiMetricsProjectionEditor } from "./KpiMetricsProjectionEditor";
import { TableColumnsMultiSelect } from "./TableColumnsMultiSelect";
import type { ValueFieldOption } from "./ValueFieldsMultiSelect";

type Props = {
  pane?: boolean;
  layout?: PanelLayout;
  /** Abre aba Dados do painel lateral (catálogo de fontes). */
  onOpenDataSources?: () => void;
  /** Rota da fonte ligada (labels de valueFields). */
  route?: TvDataRouteCatalogItem | null;
};

function parseLimitInput(raw: string, cap: number): number | undefined {
  const trimmed = raw.trim();
  if (!trimmed) return undefined;
  return normalizeTableViewLimit(Number(trimmed), cap);
}

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
  return discoverResolvedFieldOptions(resolved, catalog);
}

export function VisualDataViewInspector({
  pane = false,
  layout = "pane",
  onOpenDataSources,
  route = null,
}: Props) {
  const {
    selected,
    blocks,
    updateSelected,
    openDataPanel,
    selectedKpiPart,
    selectedChartPart,
    selectChartPart,
  } = useComunicadoEditor();
  const isRibbon = layout === "ribbon";
  const compactSelect = isRibbon ? "delpi-ui-select--compact" : undefined;
  const compactNative = isRibbon ? "delpi-ui-native-control--compact" : undefined;

  if (
    !selected ||
    (selected.type !== "chart_view" &&
      selected.type !== "kpi_view" &&
      selected.type !== "table_view")
  ) {
    return null;
  }

  const sourceOptions = dataSourceOptionsForInspector(blocks, selected.id);
  const hasSource = Boolean(selected.dataSourceId?.trim());
  const openSources = onOpenDataSources ?? openDataPanel;
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
          <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={() => openSources()}>
            Abrir fontes de dados
          </button>
        </div>
      ) : null}
      {!hasSource && isRibbon ? (
        <>
          <p className="td-deck-inspector__hint">{TV_DASHBOARD_HELP_TOOLTIPS.data.connectFlowRibbon}</p>
          <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={() => openSources()}>
            Abrir fontes de dados
          </button>
        </>
      ) : null}
      <DeckField id="td-view-data-source" label="Fonte de dados">
        <FormSelectControl
          id="td-view-data-source"
          className={compactSelect}
          ariaLabel="Fonte de dados"
          value={selected.dataSourceId ?? ""}
          onChange={(value) => {
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
            });
            updateSelected(patch as Partial<ComunicadoBlock>);
          }}
          options={[
            {
              value: "",
              label: sourceOptions.length === 0 ? "Insira uma fonte (aba Dados)" : "Selecione…",
            },
            ...sourceOptions,
          ]}
        />
      </DeckField>
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
          />
        </DeckField>
      ) : null}
    </>
  );

  const truncationBody = tableBlock ? (
    <div className={isRibbon ? "td-deck-ribbon__field-grid" : undefined}>
      <DeckField
        id="td-view-max-rows"
        label="Máximo de linhas"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableMaxRows}
      >
        <NativeTextControl
          id="td-view-max-rows"
          type="number"
          className={compactNative}
          min={1}
          max={TABLE_VIEW_MAX_ROWS_CAP}
          placeholder={`Todas (até ${TABLE_VIEW_MAX_ROWS_CAP})`}
          value={tableBlock.maxRows ?? ""}
          onChange={(value) =>
            updateSelected({
              maxRows: parseLimitInput(value, TABLE_VIEW_MAX_ROWS_CAP),
            } as Partial<ComunicadoTableViewBlock>)
          }
        />
      </DeckField>
      <DeckField
        id="td-view-max-cols"
        label="Máximo de colunas"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableMaxCols}
      >
        <NativeTextControl
          id="td-view-max-cols"
          type="number"
          className={compactNative}
          min={1}
          max={TABLE_VIEW_MAX_COLS_CAP}
          placeholder={`Todas (até ${TABLE_VIEW_MAX_COLS_CAP})`}
          value={tableBlock.maxCols ?? ""}
          onChange={(value) =>
            updateSelected({
              maxCols: parseLimitInput(value, TABLE_VIEW_MAX_COLS_CAP),
            } as Partial<ComunicadoTableViewBlock>)
          }
        />
      </DeckField>
    </div>
  ) : null;

  if (isRibbon) {
    return (
      <>
        <div className="td-deck-ribbon__panel-zone">
          <h4 className="td-deck-ribbon__panel-zone-title">Conexão</h4>
          <div className="td-deck-ribbon__field-grid">{connectionBody}</div>
        </div>
        {truncationBody ? (
          <div className="td-deck-ribbon__panel-zone">
            <h4 className="td-deck-ribbon__panel-zone-title">Truncamento</h4>
            {truncationBody}
          </div>
        ) : null}
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

      {tableBlock ? (
        <DeckPropertySection
          pane={pane}
          title="Truncamento"
          hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableTruncation}
          defaultOpen
        >
          {truncationBody}
        </DeckPropertySection>
      ) : null}
    </>
  );
}
