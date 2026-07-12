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
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
  /** Abre aba Dados do painel lateral (catálogo de fontes). */
  onOpenDataSources?: () => void;
};

function parseLimitInput(raw: string, cap: number): number | undefined {
  const trimmed = raw.trim();
  if (!trimmed) return undefined;
  return normalizeTableViewLimit(Number(trimmed), cap);
}

export function VisualDataViewInspector({ pane = false, onOpenDataSources }: Props) {
  const { selected, blocks, updateSelected, openDataPanel } = useComunicadoEditor();

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

  return (
    <>
      <DeckPropertySection
        pane={pane}
        title="Conexão de dados"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.data.viewBinding}
        defaultOpen={!hasSource}
      >
        {selected.type === "chart_view" ? (
          <p className="td-deck-inspector__meta">Gráfico: {chartTypeLabel(selected.chartType)}</p>
        ) : selected.type === "kpi_view" ? (
          <p className="td-deck-inspector__meta">Card KPI</p>
        ) : (
          <p className="td-deck-inspector__meta">Tabela: {tablePresetLabel(selected.tablePreset)}</p>
        )}
        {!hasSource ? (
          <div className="td-deck-inspector__onboarding">
            <p className="td-deck-inspector__hint">{TV_DASHBOARD_HELP_TOOLTIPS.data.connectFlow}</p>
            <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={() => openSources()}>
              Abrir fontes de dados
            </button>
          </div>
        ) : null}
        <DeckField id="td-view-data-source" label="Fonte de dados">
          <FormSelectControl
            id="td-view-data-source"
            ariaLabel="Fonte de dados"
            value={selected.dataSourceId ?? ""}
            onChange={(value) =>
              updateSelected({
                dataSourceId: value || undefined,
              } as Partial<ComunicadoBlock>)
            }
            options={[
              { value: "", label: sourceOptions.length === 0 ? "Insira uma fonte (aba Dados)" : "Selecione…" },
              ...sourceOptions,
            ]}
          />
        </DeckField>
      </DeckPropertySection>

      {tableBlock ? (
        <DeckPropertySection
          pane={pane}
          title="Truncamento"
          hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableTruncation}
          defaultOpen
        >
          <DeckField
            id="td-view-max-rows"
            label="Máximo de linhas"
            hint={TV_DASHBOARD_HELP_TOOLTIPS.data.tableMaxRows}
          >
            <NativeTextControl
              id="td-view-max-rows"
              type="number"
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
        </DeckPropertySection>
      ) : null}
    </>
  );
}
