import {
  Columns3,
  Database,
  Grid3x3,
  Heading,
  LayoutGrid,
  ListOrdered,
  PanelLeft,
  PanelRight,
  Rows3,
  Shapes,
  Sigma,
  Table2,
} from "lucide-react";
import {
  isTableElementEnabled,
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  presetDefaultTableOptions,
  setTableElementEnabled,
  tableElementPrimaryPartRef,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTablePreset,
  type ComunicadoTableViewBlock,
  type TableElementId,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { FormatRibbonTypographySections } from "./formatRibbon";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const STYLE_OPTION_TILES: Array<{
  id: TableElementId;
  icon: typeof Heading;
  label: string;
  hint: string;
}> = [
  {
    id: "tableTitle",
    icon: Heading,
    label: "Título",
    hint: "Exibir ou ocultar o título acima da tabela.",
  },
  {
    id: "header",
    icon: ListOrdered,
    label: "Cabeçalho",
    hint: "Excel: Header Row — linha com nomes das colunas.",
  },
  {
    id: "totalRow",
    icon: Sigma,
    label: "Totais",
    hint: "Excel: Total Row — soma colunas numéricas.",
  },
  {
    id: "zebraStripe",
    icon: Rows3,
    label: "Listras (linhas)",
    hint: "Excel: Banded Rows — linhas pares destacadas.",
  },
  {
    id: "firstColumn",
    icon: PanelLeft,
    label: "1ª coluna",
    hint: "Excel: First Column — destaque na primeira coluna.",
  },
  {
    id: "lastColumn",
    icon: PanelRight,
    label: "Última col.",
    hint: "Excel: Last Column — destaque na última coluna.",
  },
  {
    id: "bandedColumns",
    icon: Columns3,
    label: "Listras (cols)",
    hint: "Excel: Banded Columns — colunas pares destacadas.",
  },
  {
    id: "borders",
    icon: Grid3x3,
    label: "Bordas",
    hint: "Linhas separadoras entre células.",
  },
];

/**
 * Faixa contextual «Tabela» — estilos, opções e tipografia.
 * Aba Forma permanece para moldura (preenchimento/contorno/cantos).
 */
export function ComunicadoTableRibbon() {
  const { selected, updateSelected, selectTablePart, openDataPanel } = useComunicadoEditor();

  if (!selected || selected.type !== "table_view") {
    return (
      <div className="td-deck-ribbon__groups">
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione uma tabela no palco para editar estilos, opções e tipografia.
        </p>
      </div>
    );
  }

  const block = selected as ComunicadoTableViewBlock;
  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);

  const applyOptions = (patch: Partial<ComunicadoTableOptions>, preset?: ComunicadoTablePreset) => {
    const nextPreset = preset ?? block.tablePreset;
    const nextOptions = {
      ...mergeComunicadoTableOptions(block.tableOptions, nextPreset),
      ...patch,
    };
    updateSelected({
      ...(preset ? { tablePreset: preset } : {}),
      tableOptions: nextOptions,
      tableParts: mergeTablePartsWithOptions(block.tableParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  const setPreset = (preset: ComunicadoTablePreset) => {
    const defaults = presetDefaultTableOptions(preset);
    updateSelected({
      tablePreset: preset,
      tableOptions: defaults,
      tableParts: mergeTablePartsWithOptions(block.tableParts, defaults),
    } as Partial<ComunicadoBlock>);
  };

  const toggleElement = (elementId: TableElementId, enabled: boolean) => {
    applyOptions(setTableElementEnabled(elementId, enabled));
    if (enabled) {
      const part = tableElementPrimaryPartRef(elementId);
      if (part) selectTablePart(block.id, part);
    }
  };

  return (
    <div className="td-deck-ribbon__groups">
      <FormatRibbonTypographySections />

      <DeckRibbonGroup label="Dados" hint={H.tableData ?? H.chartData}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Database}
            label="Selecionar dados"
            hint="Abre o painel de fontes de dados."
            onClick={() => openDataPanel()}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Estilos" hint={H.tableStyles}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Table2}
            label="Grade"
            hint="Estilo grade com bordas (preset grid)."
            active={(block.tablePreset ?? "grid") === "grid"}
            onClick={() => setPreset("grid")}
          />
          <DeckRibbonTile
            icon={LayoutGrid}
            label="Minimalista"
            hint="Sem bordas fortes (preset minimal)."
            active={block.tablePreset === "minimal"}
            onClick={() => setPreset("minimal")}
          />
          <DeckRibbonTile
            icon={Rows3}
            label="Faixas"
            hint="Listras nas linhas (preset banded)."
            active={block.tablePreset === "banded"}
            onClick={() => setPreset("banded")}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Opções de estilo" hint={H.tableStyleOptions}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          {STYLE_OPTION_TILES.map((tile) => {
            const active = isTableElementEnabled(tile.id, options);
            return (
              <DeckRibbonTile
                key={tile.id}
                icon={tile.icon}
                label={tile.label}
                hint={tile.hint}
                active={active}
                onClick={() => toggleElement(tile.id, !active)}
              />
            );
          })}
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Moldura" hint={H.tableFormat ?? H.chartFormat}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Shapes}
            label="Forma"
            hint="Seleciona a moldura e abre preenchimento/contorno (como Formatar Forma)."
            onClick={() => selectTablePart(block.id, { kind: "frame" })}
          />
        </div>
      </DeckRibbonGroup>
    </div>
  );
}
