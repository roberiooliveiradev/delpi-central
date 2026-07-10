import { NativeSelectControl } from "@delpi/plugin-ui/index";
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

export function VisualDataViewInspector() {
  const { selected, blocks, updateSelected } = useComunicadoEditor();

  if (!selected || !isDataViewBlockType(selected.type)) return null;

  const sourceOptions = dataSourceOptionsForInspector(blocks, selected.id);

  return (
    <DeckPropertySection title="Conexão de dados" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.viewBinding}>
      {selected.type === "chart_view" ? (
        <p className="td-deck-inspector__meta">Gráfico: {chartTypeLabel(selected.chartType)}</p>
      ) : (
        <p className="td-deck-inspector__meta">Tabela: {tablePresetLabel(selected.tablePreset)}</p>
      )}
      <DeckField id="td-view-data-source" label="Fonte de dados">
        <NativeSelectControl
          id="td-view-data-source"
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
          <input
            id="td-view-max-rows"
            type="number"
            min={1}
            max={50}
            value={selected.maxRows ?? ""}
            onChange={(event) => {
              const raw = event.target.value.trim();
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
