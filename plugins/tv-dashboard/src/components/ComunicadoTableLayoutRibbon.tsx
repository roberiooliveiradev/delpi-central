import { AlignCenter, AlignLeft, AlignRight, Database } from "lucide-react";
import {
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoPartFormatRibbon } from "./ComunicadoPartFormatRibbon";
import { SelectionSectionsHost } from "./selectionSections";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/**
 * Aba contextual «Tabela Layout» — alinhamento, moldura, truncamento e organizar.
 * Sem merge/insert estrutural (tabela data-bound).
 */
export function ComunicadoTableLayoutRibbon() {
  const { selected, selectedTablePart, updateSelected, openDataPanel } = useComunicadoEditor();

  const selectionChrome = resolveSelectionChromeMode({
    selected,
    selectedTablePart,
  });
  if (isPartSelectionChrome(selectionChrome)) {
    return <ComunicadoPartFormatRibbon chrome={selectionChrome} />;
  }

  if (!selected || selected.type !== "table_view") {
    return (
      <div className="td-deck-ribbon__groups">
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione uma tabela no palco para editar o layout.
        </p>
      </div>
    );
  }

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

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Tabela" hint={H.tableData ?? H.chartData}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Database}
            label="Selecionar dados"
            hint="Abre o painel de fontes de dados."
            onClick={() => openDataPanel()}
          />
          <DeckRibbonTile
            icon={AlignCenter}
            label="Grade"
            hint="Exibe ou oculta as linhas de grade (bordas)."
            active={options.showBorders !== false}
            onClick={() => applyOptions({ showBorders: options.showBorders === false })}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup
        label="Exibição"
        hint="Truncamento visual das linhas e colunas resolvidas da fonte (não altera o ERP)."
      >
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
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Alinhamento" hint="Alinhamento horizontal do texto nas células.">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={AlignLeft}
            label="Esquerda"
            active={(options.textAlign ?? "left") === "left"}
            onClick={() => applyOptions({ textAlign: "left" })}
          />
          <DeckRibbonTile
            icon={AlignCenter}
            label="Centro"
            active={options.textAlign === "center"}
            onClick={() => applyOptions({ textAlign: "center" })}
          />
          <DeckRibbonTile
            icon={AlignRight}
            label="Direita"
            active={options.textAlign === "right"}
            onClick={() => applyOptions({ textAlign: "right" })}
          />
        </div>
      </DeckRibbonGroup>

      <div className="td-deck-ribbon__group-cluster td-deck-ribbon__group-cluster--frame-organize">
        <SelectionSectionsHost layout="ribbon" only={["frame", "organize"]} />
      </div>
    </div>
  );
}
