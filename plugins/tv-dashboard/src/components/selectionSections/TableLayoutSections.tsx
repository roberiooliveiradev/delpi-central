import { AlignCenter, AlignLeft, AlignRight, Database, Grid3x3 } from "lucide-react";
import {
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

function useTableLayoutControls() {
  const { selected, updateSelected, openDataPanel } = useComunicadoEditor();
  if (!selected || selected.type !== "table_view") return null;

  const block = selected as ComunicadoTableViewBlock;
  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);

  const applyOptions = (patch: Partial<ComunicadoTableOptions>) => {
    const nextOptions = {
      ...mergeComunicadoTableOptions(block.tableOptions, block.tablePreset),
      ...patch,
    };
    updateSelected({
      tableOptions: nextOptions,
      tableParts: mergeTablePartsWithOptions(block.tableParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  return { block, options, applyOptions, updateSelected, openDataPanel };
}

/** Dados + toggle de grade (aba Layout). */
export function TableLayoutDataSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableLayoutControls();
  if (!ctrl) return null;
  const { options, applyOptions, openDataPanel } = ctrl;

  const tiles = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTile
        icon={Database}
        label="Selecionar dados"
        hint="Abre o painel de fontes de dados."
        onClick={() => openDataPanel()}
      />
      <DeckRibbonTile
        icon={Grid3x3}
        label="Grade"
        hint="Exibe ou oculta as linhas de grade (bordas)."
        active={options.showBorders !== false}
        onClick={() => applyOptions({ showBorders: options.showBorders === false })}
      />
    </div>
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Tabela" hint={H.tableData ?? H.chartData} defaultOpen>
        {tiles}
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup label="Tabela" hint={H.tableData ?? H.chartData}>
      {tiles}
    </DeckRibbonGroup>
  );
}

/** Truncamento visual maxRows / maxCols. */
export function TableLayoutDisplaySection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableLayoutControls();
  if (!ctrl) return null;
  const { block, updateSelected } = ctrl;

  const hint =
    "Truncamento visual das linhas e colunas resolvidas da fonte (não altera o ERP).";

  const fields = (
    <div className="td-deck-ribbon__frame-grid td-deck-ribbon__toolbar-row--dense">
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">Máx. linhas</span>
        <input
          type="number"
          className="td-deck-ribbon__number td-deck-ribbon__number--compact"
          min={1}
          placeholder="Todas"
          value={block.maxRows ?? ""}
          onChange={(event) => {
            const raw = event.target.value;
            updateSelected({
              maxRows: raw === "" ? undefined : Math.max(1, Number(raw) || 1),
            } as Partial<ComunicadoBlock>);
          }}
        />
      </label>
      <label className="td-deck-ribbon__frame-field">
        <span className="td-deck-ribbon__field-label">Máx. cols</span>
        <input
          type="number"
          className="td-deck-ribbon__number td-deck-ribbon__number--compact"
          min={1}
          placeholder="Todas"
          value={block.maxCols ?? ""}
          onChange={(event) => {
            const raw = event.target.value;
            updateSelected({
              maxCols: raw === "" ? undefined : Math.max(1, Number(raw) || 1),
            } as Partial<ComunicadoBlock>);
          }}
        />
      </label>
    </div>
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Exibição" hint={hint} defaultOpen={false}>
        {fields}
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup label="Exibição" hint={hint}>
      {fields}
    </DeckRibbonGroup>
  );
}

/** Alinhamento horizontal do texto nas células. */
export function TableLayoutAlignSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableLayoutControls();
  if (!ctrl) return null;
  const { options, applyOptions } = ctrl;
  const align = options.textAlign ?? "left";

  const tiles = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTile
        icon={AlignLeft}
        label="Esquerda"
        active={align === "left"}
        onClick={() => applyOptions({ textAlign: "left" })}
      />
      <DeckRibbonTile
        icon={AlignCenter}
        label="Centro"
        active={align === "center"}
        onClick={() => applyOptions({ textAlign: "center" })}
      />
      <DeckRibbonTile
        icon={AlignRight}
        label="Direita"
        active={align === "right"}
        onClick={() => applyOptions({ textAlign: "right" })}
      />
    </div>
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection
        title="Alinhamento"
        hint="Alinhamento horizontal do texto nas células."
        defaultOpen={false}
      >
        {tiles}
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup label="Alinhamento" hint="Alinhamento horizontal do texto nas células.">
      {tiles}
    </DeckRibbonGroup>
  );
}
