import { NativeCheckboxControl, NativeTextControl } from "@delpi/plugin-ui/index";
import { normalizeCanvasTableCells } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckField } from "../deck/DeckField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/** Tabela canvas — linhas/colunas/cabeçalho. */
export function CanvasTableSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, updateSelected } = useComunicadoEditor();
  if (!selected || selected.type !== "canvas_table") return null;

  const body = (
    <>
      <DeckField id="td-canvas-table-rows" label="Linhas">
        <NativeTextControl
          id="td-canvas-table-rows"
          type="number"
          min={1}
          max={20}
          value={selected.rows}
          onChange={(value) => {
            const rows = Math.max(1, Math.min(20, Number(value) || 1));
            updateSelected({
              rows,
              cells: normalizeCanvasTableCells(selected.cells, rows, selected.cols),
            });
          }}
        />
      </DeckField>
      <DeckField id="td-canvas-table-cols" label="Colunas">
        <NativeTextControl
          id="td-canvas-table-cols"
          type="number"
          min={1}
          max={12}
          value={selected.cols}
          onChange={(value) => {
            const cols = Math.max(1, Math.min(12, Number(value) || 1));
            updateSelected({
              cols,
              cells: normalizeCanvasTableCells(selected.cells, selected.rows, cols),
            });
          }}
        />
      </DeckField>
      <NativeCheckboxControl
        id="td-canvas-table-header-row"
        className="td-deck-inspector__checkbox"
        checked={selected.headerRow ?? false}
        label="Primeira linha como cabeçalho"
        onChange={(checked) => updateSelected({ headerRow: checked })}
      />
    </>
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Tabela (canvas)" hint={H.canvasTable} defaultOpen>
        {body}
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup label="Tabela (canvas)" hint={H.canvasTable}>
      {body}
    </DeckRibbonGroup>
  );
}
