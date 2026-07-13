import { useRef, useState, type CSSProperties } from "react";
import { Database, Grid3x3, Square, Shapes } from "lucide-react";
import { ColorPickerPopoverTrigger } from "@delpi/plugin-ui/index";
import {
  isTableElementEnabled,
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  presetDefaultTableOptions,
  setTableElementEnabled,
  tableElementPrimaryPartRef,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
  type TableElementId,
} from "@delpi/tv-dashboard-presentation";

import { TABLE_STYLE_RECIPES, type TableStyleRecipe } from "../content/tableStyleRecipes";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const STYLE_OPTION_CHECKS: Array<{
  id: TableElementId;
  label: string;
  hint: string;
}> = [
  { id: "tableTitle", label: "Título", hint: "Exibir ou ocultar o título acima da tabela." },
  { id: "header", label: "Linha de cabeçalho", hint: "Excel: Header Row." },
  { id: "totalRow", label: "Linha de totais", hint: "Excel: Total Row." },
  { id: "firstColumn", label: "Primeira coluna", hint: "Excel: First Column." },
  { id: "lastColumn", label: "Última coluna", hint: "Excel: Last Column." },
  { id: "zebraStripe", label: "Linhas em tiras", hint: "Excel: Banded Rows." },
  { id: "bandedColumns", label: "Colunas em tiras", hint: "Excel: Banded Columns." },
  { id: "borders", label: "Bordas", hint: "Linhas separadoras entre células." },
];

function recipeThumbStyle(recipe: TableStyleRecipe): CSSProperties {
  return {
    ["--td-thumb-header" as string]: recipe.options.headerBg ?? "#e2e8f0",
    ["--td-thumb-cell" as string]: recipe.options.cellBg ?? "#ffffff",
    ["--td-thumb-border" as string]: recipe.options.borderColor ?? "#cbd5e1",
  };
}

/**
 * Aba contextual «Design da Tabela» — opções de estilo, galeria, sombreamento e bordas.
 */
export function ComunicadoTableDesignRibbon() {
  const {
    selected,
    selectedTablePart,
    updateSelected,
    selectTablePart,
    openDataPanel,
    requestRibbonTab,
  } = useComunicadoEditor();
  const [galleryOpen, setGalleryOpen] = useState(false);
  const galleryAnchorRef = useRef<HTMLDivElement>(null);

  if (!selected || selected.type !== "table_view") {
    return (
      <div className="td-deck-ribbon__groups">
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione uma tabela no palco para editar o design.
        </p>
      </div>
    );
  }

  const block = selected as ComunicadoTableViewBlock;
  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);

  const applyOptions = (patch: Partial<ComunicadoTableOptions>, preset = block.tablePreset) => {
    const nextOptions = {
      ...mergeComunicadoTableOptions(block.tableOptions, preset),
      ...patch,
    };
    updateSelected({
      tablePreset: preset,
      tableOptions: nextOptions,
      tableParts: mergeTablePartsWithOptions(block.tableParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  const applyRecipe = (recipe: TableStyleRecipe) => {
    const nextOptions = {
      ...presetDefaultTableOptions(recipe.preset),
      ...recipe.options,
    };
    updateSelected({
      tablePreset: recipe.preset,
      tableOptions: nextOptions,
      tableParts: mergeTablePartsWithOptions(block.tableParts, nextOptions),
    } as Partial<ComunicadoBlock>);
    setGalleryOpen(false);
  };

  const clearTableStyle = () => {
    const defaults = presetDefaultTableOptions("grid");
    updateSelected({
      tablePreset: "grid",
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

  const shadeTarget =
    selectedTablePart?.kind === "header" || selectedTablePart?.kind === "headerCell"
      ? "header"
      : "cell";
  const shadeValue = shadeTarget === "header" ? options.headerBg : options.cellBg;

  const ribbonRecipes = TABLE_STYLE_RECIPES.filter((r) =>
    ["medium-banded", "medium-teal", "medium-navy", "light-grid", "dark-ink", "light-minimal"].includes(
      r.id,
    ),
  );

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Opções de estilo" hint={H.tableStyleOptions}>
        <div className="td-deck-ribbon__style-checks" role="group" aria-label="Opções de estilo de tabela">
          {STYLE_OPTION_CHECKS.map((item) => {
            const checked = isTableElementEnabled(item.id, options);
            return (
              <label key={item.id} className="td-deck-ribbon__style-check" title={item.hint}>
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleElement(item.id, !checked)}
                />
                <span>{item.label}</span>
              </label>
            );
          })}
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Estilos de tabela" hint={H.tableStyles} wide>
        <div className="td-deck-ribbon__table-gallery" ref={galleryAnchorRef}>
          {ribbonRecipes.map((recipe) => (
            <button
              key={recipe.id}
              type="button"
              className="td-deck-ribbon__table-thumb"
              title={recipe.label}
              aria-label={recipe.label}
              onClick={() => applyRecipe(recipe)}
              style={recipeThumbStyle(recipe)}
            >
              <span className="td-deck-ribbon__table-thumb-grid" aria-hidden="true" />
            </button>
          ))}
          <button
            type="button"
            className="td-deck-ribbon__table-gallery-more"
            aria-expanded={galleryOpen}
            onClick={() => setGalleryOpen((open) => !open)}
          >
            Mais
          </button>
        </div>
        {galleryOpen ? (
          <div className="td-deck-ribbon__table-gallery-panel" role="menu">
            {(["light", "medium", "dark"] as const).map((category) => (
              <section key={category} className="td-deck-ribbon__table-gallery-section">
                <h4>
                  {category === "light" ? "Claros" : category === "medium" ? "Médios" : "Escuros"}
                </h4>
                <div className="td-deck-ribbon__table-gallery-grid">
                  {TABLE_STYLE_RECIPES.filter((r) => r.category === category).map((recipe) => (
                    <button
                      key={recipe.id}
                      type="button"
                      className="td-deck-ribbon__table-thumb"
                      title={recipe.label}
                      onClick={() => applyRecipe(recipe)}
                      style={recipeThumbStyle(recipe)}
                    >
                      <span className="td-deck-ribbon__table-thumb-grid" aria-hidden="true" />
                    </button>
                  ))}
                </div>
              </section>
            ))}
            <button type="button" className="td-btn td-btn--ghost td-btn--sm" onClick={clearTableStyle}>
              Limpar tabela
            </button>
          </div>
        ) : null}
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Sombreamento" hint="Cor de fundo do cabeçalho ou das células.">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--color-pickers">
          <ColorPickerPopoverTrigger
            value={shadeValue ?? "#ffffff"}
            triggerLabel={shadeTarget === "header" ? "Cabeçalho" : "Célula"}
            onChange={(color) =>
              applyOptions(
                shadeTarget === "header" ? { headerBg: color } : { cellBg: color },
              )
            }
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Bordas" hint="Visibilidade e cor das linhas da grade.">
        <div className="td-deck-ribbon__border-controls">
          <DeckRibbonTile
            icon={Square}
            label="Sem borda"
            hint="Remove as linhas separadoras das células."
            active={options.showBorders === false}
            onClick={() => applyOptions({ showBorders: false })}
          />
          <DeckRibbonTile
            icon={Grid3x3}
            label="Todas"
            hint="Mostra todas as bordas da grade."
            active={options.showBorders !== false}
            onClick={() => applyOptions({ showBorders: true })}
          />
          <ColorPickerPopoverTrigger
            value={options.borderColor ?? "#e2e8f0"}
            triggerLabel="Cor"
            onChange={(color) => applyOptions({ borderColor: color, showBorders: true })}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Dados" hint={H.tableData ?? H.chartData}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Database}
            label="Selecionar dados"
            hint="Abre o painel de fontes de dados."
            onClick={() => openDataPanel()}
          />
          <DeckRibbonTile
            icon={Shapes}
            label="Forma"
            hint="Abre a aba Forma para preenchimento e contorno da moldura."
            onClick={() => requestRibbonTab("shape")}
          />
        </div>
      </DeckRibbonGroup>
    </div>
  );
}
