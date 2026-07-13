import { useRef, useState, type CSSProperties } from "react";
import { Database, Grid3x3, Square, Shapes } from "lucide-react";
import {
  ColorPickerPopoverTrigger,
  CONFIGURABLE_TABLE_BORDER_STYLE_OPTIONS,
  CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS,
  ShapeShadowMenu,
} from "@delpi/plugin-ui/index";
import {
  isTableElementEnabled,
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  presetDefaultTableOptions,
  resolveTableFrameStyle,
  setTableElementEnabled,
  tableElementPrimaryPartRef,
  upsertTablePartState,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
  type TableElementId,
} from "@delpi/tv-dashboard-presentation";

import { TABLE_STYLE_RECIPES, type TableStyleRecipe } from "../content/tableStyleRecipes";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../content/comunicadoVisualPresets";
import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoPartFormatRibbon } from "./ComunicadoPartFormatRibbon";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

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
          Selecione uma tabela no palco para editar o design.
        </p>
      </div>
    );
  }

  const block = selected as ComunicadoTableViewBlock;
  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);
  const frame = resolveTableFrameStyle(block.tableParts);
  const borderWidth = options.borderWidth ?? 1;
  const borderStyle = options.borderStyle ?? "solid";

  const applyOptions = (patch: Partial<ComunicadoTableOptions>, preset = block.tablePreset) => {
    const nextOptions = {
      ...mergeComunicadoTableOptions(block.tableOptions, preset),
      ...patch,
    };
    updateSelected({
      tableOptions: nextOptions,
      tableParts: mergeTablePartsWithOptions(block.tableParts, nextOptions),
      ...(preset !== block.tablePreset ? { tablePreset: preset } : {}),
    } as Partial<ComunicadoBlock>);
  };

  const applyRecipe = (recipe: TableStyleRecipe) => {
    applyOptions(recipe.options, recipe.preset);
    setGalleryOpen(false);
  };

  const clearTableStyle = () => {
    applyOptions(presetDefaultTableOptions("grid"), "grid");
    setGalleryOpen(false);
  };

  const toggleElement = (id: TableElementId, enabled: boolean) => {
    applyOptions(setTableElementEnabled(id, enabled));
    if (enabled) {
      const part = tableElementPrimaryPartRef(id);
      if (part) selectTablePart(block.id, part);
    }
  };

  const shadeTarget =
    selectedTablePart?.kind === "header" || selectedTablePart?.kind === "headerCell"
      ? "header"
      : "cell";
  const shadeValue = shadeTarget === "header" ? options.headerBg : options.cellBg;
  const ribbonRecipes = TABLE_STYLE_RECIPES.slice(0, 7);

  const patchFrameShadow = (boxShadow: string | undefined) => {
    const nextParts = upsertTablePartState(block.tableParts, { kind: "frame" }, {
      style: { boxShadow: boxShadow?.trim() ? boxShadow : "none" },
    });
    updateSelected({
      tableParts: mergeTablePartsWithOptions(nextParts, block.tableOptions),
      style: { ...block.style, boxShadow: boxShadow?.trim() ? boxShadow : undefined },
    } as Partial<ComunicadoBlock>);
  };

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Opções de estilo" hint={H.tableStyleOptions}>
        <div className="td-deck-ribbon__style-checks">
          {STYLE_OPTION_CHECKS.map((item) => {
            const checked = isTableElementEnabled(item.id, options);
            return (
              <label key={item.id} className="td-deck-ribbon__check" title={item.hint}>
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

      <DeckRibbonGroup label="Bordas" hint="Visibilidade, cor, peso e estilo da grade (caneta).">
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
        <div className="td-deck-ribbon__border-pen td-deck-ribbon__toolbar-row--dense">
          <label className="td-deck-ribbon__frame-field">
            <span className="td-deck-ribbon__field-label">Peso</span>
            <select
              className="td-deck-ribbon__select td-deck-ribbon__select--compact"
              aria-label="Peso da borda"
              value={String(borderWidth)}
              onChange={(event) => {
                const width = Number(event.target.value);
                applyOptions({ borderWidth: width, showBorders: true });
              }}
            >
              {CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS.map((width) => (
                <option key={width} value={width}>
                  {width} pt
                </option>
              ))}
              {!CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS.includes(
                borderWidth as (typeof CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS)[number],
              ) ? (
                <option value={borderWidth}>{borderWidth} pt</option>
              ) : null}
            </select>
          </label>
          <label className="td-deck-ribbon__frame-field">
            <span className="td-deck-ribbon__field-label">Estilo</span>
            <select
              className="td-deck-ribbon__select td-deck-ribbon__select--compact"
              aria-label="Estilo da borda"
              value={borderStyle}
              onChange={(event) =>
                applyOptions({
                  borderStyle: event.target.value as NonNullable<
                    ComunicadoTableOptions["borderStyle"]
                  >,
                  showBorders: true,
                })
              }
            >
              {CONFIGURABLE_TABLE_BORDER_STYLE_OPTIONS.map((entry) => (
                <option key={entry.value} value={entry.value}>
                  {entry.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Efeitos" hint="Sombra da moldura da tabela.">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          <ShapeShadowMenu
            value={frame.boxShadow === "none" ? undefined : frame.boxShadow}
            presets={SHADOW_MENU_PRESETS}
            shadowLabel="Sombra"
            onChange={patchFrameShadow}
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
