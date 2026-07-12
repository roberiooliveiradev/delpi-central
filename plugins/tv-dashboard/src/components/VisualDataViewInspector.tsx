import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  chartTypeLabel,
  dataSourceOptionsForInspector,
  isDataViewBlockType,
  tablePresetLabel,
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

export function VisualDataViewInspector({ pane = false, onOpenDataSources }: Props) {
  const { selected, blocks, updateSelected, openDataPanel } = useComunicadoEditor();

  if (!selected || !isDataViewBlockType(selected.type)) return null;

  const sourceOptions = dataSourceOptionsForInspector(blocks, selected.id);
  const hasSource = Boolean(selected.dataSourceId?.trim());
  const openSources = onOpenDataSources ?? openDataPanel;

  return (
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
            } as Partial<typeof selected>)
          }
          options={[
            { value: "", label: sourceOptions.length === 0 ? "Insira uma fonte (aba Dados)" : "Selecione…" },
            ...sourceOptions,
          ]}
        />
      </DeckField>
      {selected.type === "table_view" ? (
        <DeckField id="td-view-max-rows" label="Máximo de linhas">
          <NativeTextControl
            id="td-view-max-rows"
            type="number"
            min={1}
            max={50}
            value={selected.maxRows ?? ""}
            onChange={(value) => {
              const raw = value.trim();
              updateSelected({
                maxRows: raw ? Number(raw) : undefined,
              } as Partial<typeof selected>);
            }}
          />
        </DeckField>
      ) : null}
    </DeckPropertySection>
  );
}
