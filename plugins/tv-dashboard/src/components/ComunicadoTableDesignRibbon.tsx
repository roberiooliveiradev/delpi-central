import { Database, Grid3x3, Square, Shapes } from "lucide-react";
import {
  ColorPickerPopoverTrigger,
  CONFIGURABLE_TABLE_BORDER_STYLE_OPTIONS,
  CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS,
  ShapeShadowMenu,
  TableStyleRibbonStrip,
  ToolbarSelectField,
  type TableStylePreset,
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

import {
  findTableStyleRecipe,
  resolveActiveTableStyleRecipeId,
  tableStyleRecipesAsPresets,
  type TableStyleRecipe,
} from "../content/tableStyleRecipes";
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

const STYLE_GALLERY_PRESETS = tableStyleRecipesAsPresets();

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

const BORDER_WIDTH_OPTIONS = CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS.map((width) => ({
  value: String(width),
  label: `${width} pt`,
}));

const BORDER_STYLE_OPTIONS = CONFIGURABLE_TABLE_BORDER_STYLE_OPTIONS.map((entry) => ({
  value: entry.value,
  label: entry.label,
}));

/**
 * Aba contextual «Design da Tabela» — opções, galeria plugin-ui, sombreamento e bordas.
 */
export function ComunicadoTableDesignRibbon() {
  const {
    selected,
    selectedTablePart,
    updateSelected,
    selectTablePart,
    openDataPanel,
  } = useComunicadoEditor();

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
  const activeStyleId = resolveActiveTableStyleRecipeId(options, block.tablePreset ?? "grid");

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
  };

  const applyGalleryPreset = (preset: TableStylePreset) => {
    const recipe = findTableStyleRecipe(preset.id);
    if (recipe) applyRecipe(recipe);
  };

  const clearTableStyle = () => {
    applyOptions(presetDefaultTableOptions("grid"), "grid");
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

  const patchFrameShadow = (boxShadow: string | undefined) => {
    const nextParts = upsertTablePartState(block.tableParts, { kind: "frame" }, {
      style: { boxShadow: boxShadow?.trim() ? boxShadow : "none" },
    });
    updateSelected({
      tableParts: mergeTablePartsWithOptions(nextParts, block.tableOptions),
      style: { ...block.style, boxShadow: boxShadow?.trim() ? boxShadow : undefined },
    } as Partial<ComunicadoBlock>);
  };

  const openFrameShapeChrome = () => {
    selectTablePart(block.id, { kind: "frame" });
  };

  const borderWidthOptions =
    BORDER_WIDTH_OPTIONS.some((entry) => entry.value === String(borderWidth))
      ? BORDER_WIDTH_OPTIONS
      : [...BORDER_WIDTH_OPTIONS, { value: String(borderWidth), label: `${borderWidth} pt` }];

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Opções de estilo" hint={H.tableStyleOptions}>
        <div className="td-deck-ribbon__style-checks">
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
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          <TableStyleRibbonStrip
            presets={STYLE_GALLERY_PRESETS}
            selectedId={activeStyleId}
            onSelect={applyGalleryPreset}
            onClear={clearTableStyle}
          />
        </div>
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
          <ToolbarSelectField
            label="Peso"
            value={String(borderWidth)}
            allowEmptyOption={false}
            options={borderWidthOptions}
            onChange={(value) => {
              const width = Number(value);
              if (!Number.isFinite(width)) return;
              applyOptions({ borderWidth: width, showBorders: true });
            }}
          />
          <ToolbarSelectField
            label="Estilo"
            value={borderStyle}
            allowEmptyOption={false}
            options={BORDER_STYLE_OPTIONS}
            onChange={(value) =>
              applyOptions({
                borderStyle: value as NonNullable<ComunicadoTableOptions["borderStyle"]>,
                showBorders: true,
              })
            }
          />
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

      <DeckRibbonGroup label="Forma" hint="Preenchimento e contorno da moldura da tabela.">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Shapes}
            label="Forma"
            hint="Seleciona a moldura e abre preenchimento/contorno (como Formatar Forma)."
            onClick={openFrameShapeChrome}
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
        </div>
      </DeckRibbonGroup>
    </div>
  );
}
