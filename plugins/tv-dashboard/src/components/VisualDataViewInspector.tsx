import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  TABLE_VIEW_MAX_COLS_CAP,
  TABLE_VIEW_MAX_ROWS_CAP,
  chartTypeLabel,
  dataSourceOptionsForInspector,
  normalizeTableViewLimit,
  tablePresetLabel,
  type ComunicadoBlock,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import type { PanelLayout } from "./SelectedDataSidePanel";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
  layout?: PanelLayout;
  /** Abre aba Dados do painel lateral (catálogo de fontes). */
  onOpenDataSources?: () => void;
};

function parseLimitInput(raw: string, cap: number): number | undefined {
  const trimmed = raw.trim();
  if (!trimmed) return undefined;
  return normalizeTableViewLimit(Number(trimmed), cap);
}

export function VisualDataViewInspector({
  pane = false,
  layout = "pane",
  onOpenDataSources,
}: Props) {
  const { selected, blocks, updateSelected, openDataPanel } = useComunicadoEditor();
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
          onChange={(value) =>
            updateSelected({
              dataSourceId: value || undefined,
            } as Partial<ComunicadoBlock>)
          }
          options={[
            {
              value: "",
              label: sourceOptions.length === 0 ? "Insira uma fonte (aba Dados)" : "Selecione…",
            },
            ...sourceOptions,
          ]}
        />
      </DeckField>
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
