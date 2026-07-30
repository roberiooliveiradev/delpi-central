import type { ReactNode } from "react";
import { useRef, useState } from "react";
import {
  Database,
  Grid3x3,
  LayoutTemplate,
  Square,
  Shapes,
} from "lucide-react";
import {
  AnchoredPanelPortal,
  ColorPickerPopoverTrigger,
  CONFIGURABLE_TABLE_BORDER_STYLE_OPTIONS,
  CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS,
  ShapeShadowMenu,
  TableStyleMenu,
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
import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";

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
import { ShapeCornerRadiusControl } from "../ShapeCornerRadiusControl";
import { FormatRibbonOpacityFields } from "../formatRibbon/FormatRibbonOrganizeSection";
import { ShapeMenuHint } from "../formatRibbon/ShapeMenuHint";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonLargeButton } from "../deck/DeckRibbonLargeButton";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
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

  const addElementAnchorRef = useRef<HTMLDivElement>(null);
  const addElementPanelRef = useRef<HTMLDivElement>(null);
  const [addElementOpen, setAddElementOpen] = useState(false);

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
    setAddElementOpen(false);
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
    options,
    frame,
    cornerRadius,
    borderWidth,
    borderStyle,
    activeStyleId,
    shadeTarget,
    shadeValue,
    borderWidthOptions,
    addElementAnchorRef,
    addElementPanelRef,
    addElementOpen,
    setAddElementOpen,
    applyOptions,
    applyGalleryPreset,
    clearTableStyle,
    applyAddElementChoice,
    openAddElementMoreOptions,
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
 * Layout / elementos da tabela — paridade com ChartLayoutSection («Adicionar elemento»).
 * Ribbon: botão grande + menu cascata; painel: menu embutido.
 */
export function TableStyleOptionsSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();
  if (!ctrl) return null;

  return wrapPane(
    "Layout da tabela",
    H.tableStyleOptions,
    layout,
    <TableStyleOptionsBandOrInline ctrl={ctrl} />,
    true,
    "table-style-options",
  );
}

function TableStyleOptionsBandOrInline({
  ctrl,
}: {
  ctrl: NonNullable<ReturnType<typeof useTableDesignControls>>;
}) {
  const inSectionPopover = useRibbonSectionPopoverSurface();

  const addElementMenu = (
    <TableAddElementMenu
      options={ctrl.options}
      onApplyChoice={ctrl.applyAddElementChoice}
      onMoreOptions={ctrl.openAddElementMoreOptions}
    />
  );

  if (inSectionPopover) {
    return addElementMenu;
  }

  return (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <div ref={ctrl.addElementAnchorRef} className="td-composer__dropdown">
        <DeckRibbonLargeButton
          icon={LayoutTemplate}
          label={"Adicionar\nelemento"}
          hint={H.tableStyleOptions}
          onClick={() => ctrl.setAddElementOpen((open) => !open)}
        />
        {ctrl.addElementOpen ? (
          <AnchoredPanelPortal
            open={ctrl.addElementOpen}
            anchorRef={ctrl.addElementAnchorRef}
            panelRef={ctrl.addElementPanelRef}
            variant="bare"
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            className="td-chart-add-element-portal"
            role="menu"
            aria-label="Adicionar elemento de tabela"
            exclusive={!inSectionPopover}
            onDismiss={() => ctrl.setAddElementOpen(false)}
          >
            <div>{addElementMenu}</div>
          </AnchoredPanelPortal>
        ) : null}
      </div>
    </div>
  );
}

/** Galeria + sombreamento. Ribbon: estilos colapsados (só gatilho); painel: faixa de thumbs. */
export function TableStylesSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();
  if (!ctrl) return null;

  const gallery =
    layout === "pane" ? (
      <div className="td-table-style-gallery-pane">
        <TableStyleRibbonStrip
          presets={STYLE_GALLERY_PRESETS}
          selectedId={ctrl.activeStyleId}
          onSelect={ctrl.applyGalleryPreset}
          onClear={ctrl.clearTableStyle}
          maxVisible={6}
        />
      </div>
    ) : (
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
        {/* Colapsado: evita faixa larga de thumbs cortando «Ação» / legendas. */}
        <TableStyleMenu
          presets={STYLE_GALLERY_PRESETS}
          selectedId={ctrl.activeStyleId}
          onSelect={ctrl.applyGalleryPreset}
          onClear={ctrl.clearTableStyle}
          triggerLabel="Estilos"
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
        <SelectionPaneSection title="Estilos de tabela" hint={H.tableStyles} defaultOpen>
          {gallery}
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
        {gallery}
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

  const formaChrome = (
    <>
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        <DeckRibbonTile
          icon={Shapes}
          label="Forma"
          hint={H.tableOpenFrameShape}
          onClick={ctrl.openFrameShapeChrome}
        />
      </div>
      <div className="td-deck-ribbon__organize-props td-forma-opacity">
        <ShapeCornerRadiusControl
          id="td-table-design-corner-radius"
          value={ctrl.cornerRadius}
          onChange={ctrl.patchCornerRadius}
          embedded
        />
        <FormatRibbonOpacityFields className="td-forma-opacity__slot" />
      </div>
    </>
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
          <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
            <DeckRibbonTile
              icon={Database}
              label="Selecionar dados"
              hint={H.openDataPanel}
              onClick={() => ctrl.openDataPanel()}
            />
          </div>
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
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Database}
            label="Selecionar dados"
            hint={H.openDataPanel}
            onClick={() => ctrl.openDataPanel()}
          />
        </div>
      </DeckRibbonGroup>
    </>
  );
}
