import type { ReactNode } from "react";
import {
  Database,
  Grid3x3,
  LayoutTemplate,
  Palette,
  PenLine,
  Square,
  Shapes,
  SlidersHorizontal,
} from "lucide-react";
import {
  ColorPickerPopoverTrigger,
  CONFIGURABLE_TABLE_BORDER_STYLE_OPTIONS,
  CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS,
  ShapeShadowMenu,
  TableStyleRibbonStrip,
  ToolbarSelectField,
  useRibbonSectionPopoverSurface,
  type TableStylePreset,
} from "@delpi/plugin-ui/index";
import {
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  presetDefaultTableOptions,
  resolveTableFrameStyle,
  resolveTableShapeChromePartRef,
  tableElementPrimaryPartRef,
  upsertTablePartState,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
  type TableElementId,
} from "@delpi/tv-dashboard-presentation";

import {
  applyTableAddElementChoice,
  type TableAddElementChoiceId,
} from "../../content/tableAddElementMenuCatalog";
import {
  findTableStyleRecipe,
  resolveActiveTableStyleRecipeId,
  tableStyleRecipesAsPresets,
  type TableStyleRecipe,
} from "../../content/tableStyleRecipes";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../../content/comunicadoVisualPresets";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { TableAddElementMenu } from "../TableAddElementMenu";
import { TableDataMenu, type TableDataMenuActionId } from "../TableDataMenu";
import { TableStylesMenu } from "../TableStylesMenu";
import { ShapeCornerRadiusControl } from "../ShapeCornerRadiusControl";
import { FormatRibbonOpacityFields } from "../formatRibbon/FormatRibbonOrganizeSection";
import { ShapeMenuHint } from "../formatRibbon/ShapeMenuHint";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { DeckRibbonTilePopover } from "../deck/DeckRibbonTilePopover";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

const STYLE_GALLERY_PRESETS = tableStyleRecipesAsPresets();

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
    updateSelectedStyle,
    selectTablePart,
    openDataPanel,
    setSelectionPanelTab,
  } = useComunicadoEditor();

  if (!selected || selected.type !== "table_view") {
    return null;
  }

  const block = selected as ComunicadoTableViewBlock;
  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);
  const frame = resolveTableFrameStyle(block.tableParts);
  const chromePart = resolveTableShapeChromePartRef(selectedTablePart);
  const isFrameChrome = chromePart.kind === "frame";
  const cornerRadius =
    (isFrameChrome ? frame.borderRadius : undefined) ?? block.style?.borderRadius ?? 0;
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

  const applyAddElementChoice = (choiceId: TableAddElementChoiceId) => {
    applyOptions(applyTableAddElementChoice(choiceId, options));
  };

  const openAddElementMoreOptions = (id: TableElementId) => {
    const part = tableElementPrimaryPartRef(id);
    if (part) selectTablePart(block.id, part);
    setSelectionPanelTab("element");
  };

  const openDataFocus = (actionId: TableDataMenuActionId) => {
    openDataPanel();
    setSelectionPanelTab("data");
    const anchorId =
      actionId === "columns" ? "td-view-table-columns" : "td-view-data-source";
    requestAnimationFrame(() => {
      document.getElementById(anchorId)?.scrollIntoView({ block: "nearest" });
    });
  };

  const shadeTarget =
    selectedTablePart?.kind === "header" || selectedTablePart?.kind === "headerCell"
      ? "header"
      : "cell";
  const shadeValue = shadeTarget === "header" ? options.headerBg : options.cellBg;

  const patchFrameShadow = (boxShadow: string | undefined) => {
    updateSelectedStyle({ boxShadow });
  };

  const patchCornerRadius = (radius: number) => {
    const nextParts = upsertTablePartState(block.tableParts, chromePart, {
      style: { borderRadius: radius } as never,
    });
    updateSelected({
      tableParts: mergeTablePartsWithOptions(nextParts, block.tableOptions),
      ...(isFrameChrome ? { style: { ...block.style, borderRadius: radius } } : {}),
    } as Partial<ComunicadoBlock>);
  };

  const borderWidthOptions = BORDER_WIDTH_OPTIONS.some(
    (entry) => entry.value === String(borderWidth),
  )
    ? BORDER_WIDTH_OPTIONS
    : [...BORDER_WIDTH_OPTIONS, { value: String(borderWidth), label: `${borderWidth} pt` }];

  return {
    block,
    options,
    frame,
    cornerRadius,
    borderWidth,
    borderStyle,
    activeStyleId,
    shadeTarget,
    shadeValue,
    borderWidthOptions,
    applyOptions,
    applyRecipe,
    applyGalleryPreset,
    clearTableStyle,
    applyAddElementChoice,
    openAddElementMoreOptions,
    openDataFocus,
    patchFrameShadow,
    patchCornerRadius,
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
  groupId?: string,
) {
  if (layout === "pane") {
    return (
      <SelectionPaneSection title={title} hint={hint} defaultOpen={false}>
        {body}
      </SelectionPaneSection>
    );
  }
  return (
    <DeckRibbonGroup groupId={groupId} label={title} hint={hint} wide={wide}>
      {body}
    </DeckRibbonGroup>
  );
}

/**
 * Layout / elementos da tabela — molde Tela/Programação (tile + popover).
 */
export function TableStyleOptionsSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();
  if (!ctrl) return null;

  return wrapPane(
    "Layout da tabela",
    H.tableStyleOptions,
    layout,
    <TableStyleOptionsBandOrInline ctrl={ctrl} />,
    false,
    "table-style-options",
  );
}

function TableStyleOptionsBandOrInline({
  ctrl,
}: {
  ctrl: NonNullable<ReturnType<typeof useTableDesignControls>>;
}) {
  const inSectionPopover = useRibbonSectionPopoverSurface();

  const addElementMenu = (close?: () => void) => (
    <TableAddElementMenu
      options={ctrl.options}
      onApplyChoice={ctrl.applyAddElementChoice}
      onMoreOptions={(elementId) => {
        ctrl.openAddElementMoreOptions(elementId);
        close?.();
      }}
    />
  );

  if (inSectionPopover) {
    return addElementMenu();
  }

  return (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTilePopover
        icon={LayoutTemplate}
        label="Adicionar elemento"
        hint={H.tableStyleOptions}
        panelLabel="Adicionar elemento de tabela"
        panelVariant="menu"
        panelClassName="td-chart-add-element-portal"
      >
        {(close) => addElementMenu(close)}
      </DeckRibbonTilePopover>
    </div>
  );
}

/** Galeria + sombreamento. Ribbon: tile «Alterar estilos» + popover. */
export function TableStylesSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();
  if (!ctrl) return null;

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
        <SelectionPaneSection title="Estilos de tabela" hint={H.tableStyles} defaultOpen>
          <TableStyleRibbonStrip
            presets={STYLE_GALLERY_PRESETS}
            selectedId={ctrl.activeStyleId}
            onSelect={ctrl.applyGalleryPreset}
            onClear={ctrl.clearTableStyle}
            maxVisible={6}
          />
        </SelectionPaneSection>
        <SelectionPaneSection
          title="Sombreamento"
          hint="Cor de fundo do cabeçalho ou das células."
          defaultOpen={false}
        >
          {shade}
        </SelectionPaneSection>
      </>
    );
  }

  return (
    <>
      <DeckRibbonGroup groupId="table-styles" label="Estilos de tabela" hint={H.tableStyles}>
        <TableStylesBandOrInline ctrl={ctrl} />
      </DeckRibbonGroup>
      <DeckRibbonGroup
        groupId="table-shading"
        label="Sombreamento"
        hint="Cor de fundo do cabeçalho ou das células."
      >
        {shade}
      </DeckRibbonGroup>
    </>
  );
}

function TableStylesBandOrInline({
  ctrl,
}: {
  ctrl: NonNullable<ReturnType<typeof useTableDesignControls>>;
}) {
  const inSectionPopover = useRibbonSectionPopoverSurface();

  const stylesMenu = (close?: () => void) => (
    <TableStylesMenu
      options={ctrl.options}
      preset={ctrl.block.tablePreset}
      onApplyRecipe={(recipe) => {
        ctrl.applyRecipe(recipe);
        close?.();
      }}
      onClear={() => {
        ctrl.clearTableStyle();
        close?.();
      }}
    />
  );

  if (inSectionPopover) {
    return stylesMenu();
  }

  return (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTilePopover
        icon={Palette}
        label="Alterar estilos"
        hint={H.tableStyles}
        panelLabel="Alterar estilos da tabela"
        panelVariant="menu"
        panelClassName="td-chart-float__popover--style"
      >
        {(close) => stylesMenu(close)}
      </DeckRibbonTilePopover>
    </div>
  );
}

/** Bordas, efeitos da moldura, atalhos Forma/Dados. */
export function TableBordersSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();
  if (!ctrl) return null;

  const borderPenFields = (
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
  );

  const borders =
    layout === "pane" ? (
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
        {borderPenFields}
      </>
    ) : (
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
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
        <DeckRibbonTilePopover
          icon={PenLine}
          label="Caneta"
          hint="Peso e estilo do traço das bordas."
          panelLabel="Caneta de borda"
          panelClassName="td-deck-ribbon-tile-popover--narrow"
        >
          {borderPenFields}
        </DeckRibbonTilePopover>
      </div>
    );

  const effects = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      <ShapeMenuHint hint={H.tableFrameShadow} ariaLabel="Ajuda: Sombra da moldura">
        <ShapeShadowMenu
          value={ctrl.frame.boxShadow === "none" ? undefined : ctrl.frame.boxShadow}
          presets={SHADOW_MENU_PRESETS}
          shadowLabel="Sombra"
          onChange={ctrl.patchFrameShadow}
        />
      </ShapeMenuHint>
    </div>
  );

  const formaAdjustFields = (
    <div className="td-deck-ribbon__organize-props td-forma-opacity">
      <ShapeCornerRadiusControl
        id="td-table-design-corner-radius"
        value={ctrl.cornerRadius}
        onChange={ctrl.patchCornerRadius}
        embedded
      />
      <FormatRibbonOpacityFields className="td-forma-opacity__slot" />
    </div>
  );

  const formaChrome =
    layout === "pane" ? (
      <>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Shapes}
            label="Forma"
            hint={H.tableOpenFrameShape}
            onClick={ctrl.openFrameShapeChrome}
          />
        </div>
        {formaAdjustFields}
      </>
    ) : (
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        <DeckRibbonTile
          icon={Shapes}
          label="Forma"
          hint={H.tableOpenFrameShape}
          onClick={ctrl.openFrameShapeChrome}
        />
        <DeckRibbonTilePopover
          icon={SlidersHorizontal}
          label="Ajuste"
          hint={H.tableFrameChrome}
          panelLabel="Raio e opacidade da moldura"
          panelClassName="td-deck-ribbon-tile-popover--narrow"
        >
          {formaAdjustFields}
        </DeckRibbonTilePopover>
      </div>
    );

  if (layout === "pane") {
    return (
      <>
        <SelectionPaneSection title="Bordas" hint={H.tableBorders} defaultOpen={false}>
          {borders}
        </SelectionPaneSection>
        <SelectionPaneSection title="Efeitos" hint={H.tableFrameShadow} defaultOpen={false}>
          {effects}
        </SelectionPaneSection>
        <SelectionPaneSection title="Forma" hint={H.tableFrameChrome} defaultOpen={false}>
          {formaChrome}
        </SelectionPaneSection>
        <SelectionPaneSection title="Dados" hint={H.tableData ?? H.chartData} defaultOpen={false}>
          <TableDataBandOrInline ctrl={ctrl} />
        </SelectionPaneSection>
      </>
    );
  }

  return (
    <>
      <DeckRibbonGroup groupId="table-borders" label="Bordas" hint={H.tableBorders}>
        {borders}
      </DeckRibbonGroup>
      <DeckRibbonGroup groupId="table-effects" label="Efeitos" hint={H.tableFrameShadow}>
        {effects}
      </DeckRibbonGroup>
      <DeckRibbonGroup groupId="table-forma" label="Forma" hint={H.tableFrameChrome}>
        {formaChrome}
      </DeckRibbonGroup>
      <DeckRibbonGroup groupId="table-data" label="Dados" hint={H.tableData ?? H.chartData}>
        <TableDataBandOrInline ctrl={ctrl} />
      </DeckRibbonGroup>
    </>
  );
}

function TableDataBandOrInline({
  ctrl,
}: {
  ctrl: NonNullable<ReturnType<typeof useTableDesignControls>>;
}) {
  const inSectionPopover = useRibbonSectionPopoverSurface();

  const dataMenu = (close?: () => void) => (
    <TableDataMenu
      onSelect={(actionId) => {
        ctrl.openDataFocus(actionId);
        close?.();
      }}
    />
  );

  if (inSectionPopover) {
    return dataMenu();
  }

  return (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTilePopover
        icon={Database}
        label="Selecionar dados"
        hint={H.openDataPanel}
        panelLabel="Dados da tabela"
        panelVariant="menu"
        panelClassName="td-chart-float__popover--actions"
      >
        {(close) => dataMenu(close)}
      </DeckRibbonTilePopover>
    </div>
  );
}
