import type { ReactNode } from "react";
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
} from "../../content/tableStyleRecipes";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../../content/comunicadoVisualPresets";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckPropertySection } from "../deck/DeckPropertySection";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import type { SelectionSectionLayout } from "./types";

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

function useTableDesignControls() {
  const {
    selected,
    selectedTablePart,
    updateSelected,
    selectTablePart,
    openDataPanel,
  } = useComunicadoEditor();

  if (!selected || selected.type !== "table_view") {
    return null;
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
    const nextParts = upsertTablePartState(
      block.tableParts,
      { kind: "frame" },
      {
        style: { boxShadow: boxShadow?.trim() ? boxShadow : "none" },
      },
    );
    updateSelected({
      tableParts: mergeTablePartsWithOptions(nextParts, block.tableOptions),
      style: { ...block.style, boxShadow: boxShadow?.trim() ? boxShadow : undefined },
    } as Partial<ComunicadoBlock>);
  };

  const borderWidthOptions = BORDER_WIDTH_OPTIONS.some(
    (entry) => entry.value === String(borderWidth),
  )
    ? BORDER_WIDTH_OPTIONS
    : [...BORDER_WIDTH_OPTIONS, { value: String(borderWidth), label: `${borderWidth} pt` }];

  return {
    options,
    frame,
    borderWidth,
    borderStyle,
    activeStyleId,
    shadeTarget,
    shadeValue,
    borderWidthOptions,
    applyOptions,
    applyGalleryPreset,
    clearTableStyle,
    toggleElement,
    patchFrameShadow,
    openFrameShapeChrome: () => selectTablePart(block.id, { kind: "frame" }),
    openDataPanel,
  };
}

function wrapPane(
  title: string,
  hint: string | undefined,
  layout: SelectionSectionLayout,
  body: ReactNode,
  wide?: boolean,
) {
  if (layout === "pane") {
    return (
      <DeckPropertySection title={title} hint={hint} defaultOpen={false}>
        {body}
      </DeckPropertySection>
    );
  }
  return (
    <DeckRibbonGroup label={title} hint={hint} wide={wide}>
      {body}
    </DeckRibbonGroup>
  );
}

/** Opções de estilo (checkbox Excel). */
export function TableStyleOptionsSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();
  if (!ctrl) return null;

  const body = (
    <div className="td-deck-ribbon__style-checks">
      {STYLE_OPTION_CHECKS.map((item) => {
        const checked = isTableElementEnabled(item.id, ctrl.options);
        return (
          <label key={item.id} className="td-deck-ribbon__style-check" title={item.hint}>
            <input
              type="checkbox"
              checked={checked}
              onChange={() => ctrl.toggleElement(item.id, !checked)}
            />
            <span>{item.label}</span>
          </label>
        );
      })}
    </div>
  );

  return wrapPane("Opções de estilo", H.tableStyleOptions, layout, body);
}

/** Galeria + sombreamento. */
export function TableStylesSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();
  if (!ctrl) return null;

  const gallery = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      <TableStyleRibbonStrip
        presets={STYLE_GALLERY_PRESETS}
        selectedId={ctrl.activeStyleId}
        onSelect={ctrl.applyGalleryPreset}
        onClear={ctrl.clearTableStyle}
      />
    </div>
  );

  const shade = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--color-pickers">
      <ColorPickerPopoverTrigger
        value={ctrl.shadeValue ?? "#ffffff"}
        triggerLabel={ctrl.shadeTarget === "header" ? "Cabeçalho" : "Célula"}
        onChange={(color) =>
          ctrl.applyOptions(
            ctrl.shadeTarget === "header" ? { headerBg: color } : { cellBg: color },
          )
        }
      />
    </div>
  );

  if (layout === "pane") {
    return (
      <>
        <DeckPropertySection title="Estilos de tabela" hint={H.tableStyles} defaultOpen>
          {gallery}
        </DeckPropertySection>
        <DeckPropertySection title="Sombreamento" hint="Cor de fundo do cabeçalho ou das células." defaultOpen={false}>
          {shade}
        </DeckPropertySection>
      </>
    );
  }

  return (
    <>
      <DeckRibbonGroup label="Estilos de tabela" hint={H.tableStyles} wide>
        {gallery}
      </DeckRibbonGroup>
      <DeckRibbonGroup label="Sombreamento" hint="Cor de fundo do cabeçalho ou das células.">
        {shade}
      </DeckRibbonGroup>
    </>
  );
}

/** Bordas, efeitos da moldura, atalhos Forma/Dados. */
export function TableBordersSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();
  if (!ctrl) return null;

  const borders = (
    <>
      <div className="td-deck-ribbon__border-controls">
        <DeckRibbonTile
          icon={Square}
          label="Sem borda"
          hint="Remove as linhas separadoras das células."
          active={ctrl.options.showBorders === false}
          onClick={() => ctrl.applyOptions({ showBorders: false })}
        />
        <DeckRibbonTile
          icon={Grid3x3}
          label="Todas"
          hint="Mostra todas as bordas da grade."
          active={ctrl.options.showBorders !== false}
          onClick={() => ctrl.applyOptions({ showBorders: true })}
        />
        <ColorPickerPopoverTrigger
          value={ctrl.options.borderColor ?? "#e2e8f0"}
          triggerLabel="Cor"
          onChange={(color) => ctrl.applyOptions({ borderColor: color, showBorders: true })}
        />
      </div>
      <div className="td-deck-ribbon__border-pen td-deck-ribbon__toolbar-row--dense">
        <ToolbarSelectField
          label="Peso"
          value={String(ctrl.borderWidth)}
          allowEmptyOption={false}
          options={ctrl.borderWidthOptions}
          onChange={(value) => {
            const width = Number(value);
            if (!Number.isFinite(width)) return;
            ctrl.applyOptions({ borderWidth: width, showBorders: true });
          }}
        />
        <ToolbarSelectField
          label="Estilo"
          value={ctrl.borderStyle}
          allowEmptyOption={false}
          options={BORDER_STYLE_OPTIONS}
          onChange={(value) =>
            ctrl.applyOptions({
              borderStyle: value as NonNullable<ComunicadoTableOptions["borderStyle"]>,
              showBorders: true,
            })
          }
        />
      </div>
    </>
  );

  const effects = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      <ShapeShadowMenu
        value={ctrl.frame.boxShadow === "none" ? undefined : ctrl.frame.boxShadow}
        presets={SHADOW_MENU_PRESETS}
        shadowLabel="Sombra"
        onChange={ctrl.patchFrameShadow}
      />
    </div>
  );

  const shortcuts = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTile
        icon={Shapes}
        label="Forma"
        hint="Seleciona a moldura e abre preenchimento/contorno (como Formatar Forma)."
        onClick={ctrl.openFrameShapeChrome}
      />
      <DeckRibbonTile
        icon={Database}
        label="Selecionar dados"
        hint="Abre o painel de fontes de dados."
        onClick={() => ctrl.openDataPanel()}
      />
    </div>
  );

  if (layout === "pane") {
    return (
      <>
        <DeckPropertySection
          title="Bordas"
          hint="Visibilidade, cor, peso e estilo da grade (caneta)."
          defaultOpen={false}
        >
          {borders}
        </DeckPropertySection>
        <DeckPropertySection title="Efeitos" hint="Sombra da moldura da tabela." defaultOpen={false}>
          {effects}
        </DeckPropertySection>
        <DeckPropertySection title="Forma e dados" defaultOpen={false}>
          {shortcuts}
        </DeckPropertySection>
      </>
    );
  }

  return (
    <>
      <DeckRibbonGroup label="Bordas" hint="Visibilidade, cor, peso e estilo da grade (caneta).">
        {borders}
      </DeckRibbonGroup>
      <DeckRibbonGroup label="Efeitos" hint="Sombra da moldura da tabela.">
        {effects}
      </DeckRibbonGroup>
      <DeckRibbonGroup label="Forma" hint="Preenchimento e contorno da moldura da tabela.">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Shapes}
            label="Forma"
            hint="Seleciona a moldura e abre preenchimento/contorno (como Formatar Forma)."
            onClick={ctrl.openFrameShapeChrome}
          />
        </div>
      </DeckRibbonGroup>
      <DeckRibbonGroup label="Dados" hint={H.tableData ?? H.chartData}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Database}
            label="Selecionar dados"
            hint="Abre o painel de fontes de dados."
            onClick={() => ctrl.openDataPanel()}
          />
        </div>
      </DeckRibbonGroup>
    </>
  );
}
