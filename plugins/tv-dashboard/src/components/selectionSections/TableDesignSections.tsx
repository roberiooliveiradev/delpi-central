import type { ReactNode } from "react";
import { useRef, useState } from "react";
import {
  Columns3,
  Database,
  Grid3x3,
  Heading2,
  ListChecks,
  PanelLeft,
  PanelRight,
  Rows3,
  Sigma,
  Square,
  Shapes,
  Type,
  type LucideIcon,
} from "lucide-react";
import {
  AnchoredPanelPortal,
  ColorPickerPopoverTrigger,
  CONFIGURABLE_TABLE_BORDER_STYLE_OPTIONS,
  CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS,
  HintAction,
  ShapeShadowMenu,
  TableStyleMenu,
  TableStyleRibbonStrip,
  ToolbarSelectField,
  useRibbonSectionPopoverSurface,
  type TableStylePreset,
} from "@delpi/plugin-ui/index";
import {
  isTableElementEnabled,
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  presetDefaultTableOptions,
  resolveTableFrameStyle,
  resolveTableShapeChromePartRef,
  setTableElementEnabled,
  tableElementPrimaryPartRef,
  upsertTablePartState,
  type ComunicadoBlock,
  type ComunicadoTableOptions,
  type ComunicadoTableViewBlock,
  type TableElementId,
} from "@delpi/tv-dashboard-presentation";
import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";

import {
  findTableStyleRecipe,
  resolveActiveTableStyleRecipeId,
  tableStyleRecipesAsPresets,
  type TableStyleRecipe,
} from "../../content/tableStyleRecipes";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../../content/comunicadoVisualPresets";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ShapeCornerRadiusControl } from "../ShapeCornerRadiusControl";
import { FormatRibbonOpacityFields } from "../formatRibbon/FormatRibbonOrganizeSection";
import { ShapeMenuHint } from "../formatRibbon/ShapeMenuHint";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
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

const STYLE_OPTION_TILES: Array<{
  id: TableElementId;
  label: string;
  hint: string;
  icon: LucideIcon;
}> = [
  { id: "tableTitle", label: "Título", hint: "Exibir ou ocultar o título acima da tabela.", icon: Type },
  {
    id: "header",
    label: "Cabeçalho",
    hint: "Exibe a primeira linha como cabeçalho da tabela.",
    icon: Heading2,
  },
  { id: "totalRow", label: "Totais", hint: "Exibe a última linha como linha de totais.", icon: Sigma },
  {
    id: "firstColumn",
    label: "1ª coluna",
    hint: "Destaca a primeira coluna da tabela.",
    icon: PanelLeft,
  },
  {
    id: "lastColumn",
    label: "Última col.",
    hint: "Destaca a última coluna da tabela.",
    icon: PanelRight,
  },
  {
    id: "zebraStripe",
    label: "Linhas alt.",
    hint: "Alterna o fundo das linhas para facilitar a leitura.",
    icon: Rows3,
  },
  {
    id: "bandedColumns",
    label: "Colunas alt.",
    hint: "Alterna o fundo das colunas para facilitar a leitura.",
    icon: Columns3,
  },
  { id: "borders", label: "Bordas", hint: "Linhas separadoras entre células.", icon: Grid3x3 },
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
    updateSelectedStyle,
    selectTablePart,
    openDataPanel,
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

  /** Só liga/desliga estilo — seleção de parte é pelo texto/palco, não pelo toggle. */
  const toggleElement = (id: TableElementId, enabled: boolean) => {
    applyOptions(setTableElementEnabled(id, enabled));
  };

  const focusElement = (id: TableElementId) => {
    const part = tableElementPrimaryPartRef(id);
    if (part) selectTablePart(block.id, part);
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
    applyOptions,
    applyGalleryPreset,
    clearTableStyle,
    toggleElement,
    focusElement,
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

function TableStyleOptionTiles({
  options,
  onToggle,
  onSelectLabel,
  density = "ribbon",
}: {
  options: ComunicadoTableOptions;
  onToggle: (id: TableElementId, enabled: boolean) => void;
  /** Clique no rótulo do tile foca a parte no palco (não no ícone sozinho — o tile inteiro só alterna). */
  onSelectLabel?: (id: TableElementId) => void;
  /** `pane`: grade estreita da sidebar. */
  density?: "ribbon" | "pane";
}) {
  return (
    <div
      className={[
        "td-deck-ribbon__tiles",
        "td-deck-ribbon__tiles--compact",
        "td-deck-ribbon__style-option-tiles",
        density === "pane" ? "td-deck-ribbon__style-option-tiles--pane" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="group"
      aria-label="Opções de estilo"
    >
      {STYLE_OPTION_TILES.map((item) => {
        const checked = isTableElementEnabled(item.id, options);
        return (
          <DeckRibbonTile
            key={item.id}
            icon={item.icon}
            label={item.label}
            hint={item.hint}
            active={checked}
            onClick={(event) => {
              /* Clique no texto do rótulo → só foca a parte; ícone/área do botão → toggle. */
              const target = event.target as HTMLElement | null;
              if (onSelectLabel && target?.closest?.(".td-ribbon-tile__label")) {
                event.preventDefault();
                onSelectLabel(item.id);
                return;
              }
              onToggle(item.id, !checked);
            }}
          />
        );
      })}
    </div>
  );
}

/**
 * Opções de estilo da tabela (ícones).
 * Ribbon: tile «Opções» + popover; painel: tiles embutidos.
 * Toggle não seleciona parte no palco — só o clique no texto do rótulo.
 */
export function TableStyleOptionsSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();

  if (!ctrl) return null;

  const tiles = (
    <TableStyleOptionTiles
      options={ctrl.options}
      onToggle={ctrl.toggleElement}
      onSelectLabel={ctrl.focusElement}
      density={layout === "pane" ? "pane" : "ribbon"}
    />
  );

  if (layout === "pane") {
    return wrapPane("Opções de estilo", H.tableStyleOptions, layout, tiles, false, "table-style-options");
  }

  return (
    <DeckRibbonGroup groupId="table-style-options" label="Opções de estilo" hint={H.tableStyleOptions}>
      <TableStyleOptionsBandOrInline tiles={tiles} />
    </DeckRibbonGroup>
  );
}

function TableStyleOptionsBandOrInline({ tiles }: { tiles: ReactNode }) {
  const flattenNested = useRibbonSectionPopoverSurface();
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  if (flattenNested) {
    return <>{tiles}</>;
  }

  return (
      <div className="td-table-style-options-entry delpi-ui-shape-menu td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
        <HintAction hint={H.tableStyleOptions} ariaLabel="Ajuda: Opções de estilo">
          <button
            ref={triggerRef}
            type="button"
            className={[
              "delpi-ui-shape-menu__trigger",
              open ? "td-table-style-options-entry__trigger--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            aria-label="Opções de estilo"
            aria-haspopup="dialog"
            aria-expanded={open}
            onClick={() => setOpen((prev) => !prev)}
          >
            <span className="delpi-ui-shape-menu__trigger-icon" aria-hidden="true">
              <ListChecks size={18} />
            </span>
            <span className="delpi-ui-shape-menu__trigger-label">Opções</span>
          </button>
        </HintAction>
        {open ? (
          <AnchoredPanelPortal
            open={open}
            anchorRef={triggerRef}
            panelRef={panelRef}
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            className="td-table-style-options-popover"
            role="dialog"
            aria-label="Opções de estilo"
            preferredPlacement="bottom"
            allowFlip={false}
            gap={10}
            density="compact"
            onDismiss={() => setOpen(false)}
          >
            {tiles}
          </AnchoredPanelPortal>
        ) : null}
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
