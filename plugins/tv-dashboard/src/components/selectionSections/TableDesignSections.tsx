import type { ReactNode } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Bold,
  Database,
  Grid3x3,
  Italic,
  ListChecks,
  Square,
  Shapes,
} from "lucide-react";
import {
  AnchoredPanelPortal,
  ColorPickerPopoverTrigger,
  CONFIGURABLE_TABLE_BORDER_STYLE_OPTIONS,
  CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS,
  HintAction,
  NumberStepperControl,
  ShapeShadowMenu,
  TableStyleRibbonStrip,
  ToolbarSelectField,
  useRibbonSectionPopoverSurface,
  type TableStylePreset,
} from "@delpi/plugin-ui/index";
import {
  COMUNICADO_FONT_SIZE_MIN,
  COMUNICADO_FONT_SIZE_PRESETS,
  COMUNICADO_FONT_SIZE_STEP,
  TABLE_VIEW_DEFAULT_FONT_SIZE_PX,
  clampFontSize,
  ensureComunicadoGoogleFontsLoaded,
  isTableElementEnabled,
  listComunicadoFontFamilyOptions,
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
  presetDefaultTableOptions,
  resolveTableFrameStyle,
  setTableElementEnabled,
  tableElementPrimaryPartRef,
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
import { ShapeMenuHint } from "../formatRibbon/ShapeMenuHint";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { TdRibbonSelect } from "../tdRibbonUi";
import { TvRibbonColorPicker } from "../deck/TvRibbonColorPicker";
import { SelectionPaneSection } from "./SelectionPaneSection";
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
  { id: "header", label: "Linha de cabeçalho", hint: "Exibe a primeira linha como cabeçalho da tabela." },
  { id: "totalRow", label: "Linha de totais", hint: "Exibe a última linha como linha de totais." },
  { id: "firstColumn", label: "Primeira coluna", hint: "Destaca a primeira coluna da tabela." },
  { id: "lastColumn", label: "Última coluna", hint: "Destaca a última coluna da tabela." },
  { id: "zebraStripe", label: "Linhas em tiras", hint: "Alterna o fundo das linhas para facilitar a leitura." },
  { id: "bandedColumns", label: "Colunas em tiras", hint: "Alterna o fundo das colunas para facilitar a leitura." },
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
    updateSelectedStyle({ boxShadow });
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

function TableStyleOptionsChecks({
  options,
  onToggle,
  density = "ribbon",
}: {
  options: ComunicadoTableOptions;
  onToggle: (id: TableElementId, enabled: boolean) => void;
  /** `pane`: grade estreita da sidebar (ribbon usa 4 colunas largas). */
  density?: "ribbon" | "pane";
}) {
  return (
    <div
      className={[
        "td-deck-ribbon__style-checks",
        density === "pane" ? "td-deck-ribbon__style-checks--pane" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="group"
      aria-label="Opções de estilo"
    >
      {STYLE_OPTION_CHECKS.map((item) => {
        const checked = isTableElementEnabled(item.id, options);
        return (
          <label key={item.id} className="td-deck-ribbon__style-check" title={item.hint}>
            <input
              type="checkbox"
              checked={checked}
              onChange={() => onToggle(item.id, !checked)}
            />
            <span>{item.label}</span>
          </label>
        );
      })}
    </div>
  );
}

/**
 * Opções de estilo da tabela (checkboxes).
 * Ribbon: tile «Opções» + popover; painel: checkboxes embutidos.
 */
export function TableStyleOptionsSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();

  if (!ctrl) return null;

  const checks = (
    <TableStyleOptionsChecks
      options={ctrl.options}
      onToggle={ctrl.toggleElement}
      density={layout === "pane" ? "pane" : "ribbon"}
    />
  );

  if (layout === "pane") {
    return wrapPane("Opções de estilo", H.tableStyleOptions, layout, checks, false, "table-style-options");
  }

  return (
    <DeckRibbonGroup groupId="table-style-options" label="Opções de estilo" hint={H.tableStyleOptions}>
      <TableStyleOptionsBandOrInline checks={checks} />
    </DeckRibbonGroup>
  );
}

function TableStyleOptionsBandOrInline({ checks }: { checks: ReactNode }) {
  const flattenNested = useRibbonSectionPopoverSurface();
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  if (flattenNested) {
    return <>{checks}</>;
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
            {checks}
          </AnchoredPanelPortal>
        ) : null}
      </div>
  );
}

/** Galeria + sombreamento. */
export function TableStylesSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();
  if (!ctrl) return null;

  const gallery = (
    <div
      className={
        layout === "pane"
          ? "td-table-style-gallery-pane"
          : "td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus"
      }
    >
      <TableStyleRibbonStrip
        presets={STYLE_GALLERY_PRESETS}
        selectedId={ctrl.activeStyleId}
        onSelect={ctrl.applyGalleryPreset}
        onClear={ctrl.clearTableStyle}
        /* Sidebar: menos thumbs visíveis + wrap CSS; ribbon: faixa horizontal. */
        maxVisible={layout === "pane" ? 6 : 7}
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
      <DeckRibbonGroup groupId="table-styles" label="Estilos de tabela" hint={H.tableStyles} wide>
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

/** Tipografia global da grade (família, tamanho, B/I, cor, alinhamento). */
export function TableTypographySection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useTableDesignControls();
  const { config } = useComunicadoEditor();
  const fontFamilyOptions = useMemo(
    () =>
      listComunicadoFontFamilyOptions(config.customFonts).map((font) => ({
        value: font.value,
        label:
          font.source === "google"
            ? `${font.label} · Google`
            : font.source === "custom"
              ? `${font.label} · Personalizada`
              : font.label,
      })),
    [config.customFonts],
  );

  useEffect(() => {
    ensureComunicadoGoogleFontsLoaded(fontFamilyOptions.map((option) => option.value));
  }, [fontFamilyOptions]);

  if (!ctrl) return null;

  const fontSize = ctrl.options.fontSize ?? TABLE_VIEW_DEFAULT_FONT_SIZE_PX;
  const fontFamily = ctrl.options.fontFamily?.trim() || fontFamilyOptions[0]?.value || "";
  const bold =
    ctrl.options.fontWeight === "bold" ||
    ctrl.options.fontWeight === "700" ||
    ctrl.options.fontWeight === 700;
  const italic = ctrl.options.fontStyle === "italic";
  const textAlign = ctrl.options.textAlign ?? "left";
  const textColor = ctrl.options.cellTextColor ?? "#334155";

  const body = (
    <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--text-stack td-deck-ribbon__toolbar--font">
      <div className="td-deck-ribbon__toolbar-row td-deck-ribbon__toolbar-row--inputs">
        <HintAction hint={H.fontFamily} ariaLabel="Ajuda: Família da fonte">
          <TdRibbonSelect
            aria-label="Família da fonte da tabela"
            className="td-deck-ribbon__select--font-family"
            value={fontFamily}
            onChange={(value) => {
              if (!value) return;
              ensureComunicadoGoogleFontsLoaded([value]);
              ctrl.applyOptions({ fontFamily: value });
            }}
            options={fontFamilyOptions}
          />
        </HintAction>
        <NumberStepperControl
          className="td-deck-ribbon__font-size"
          groupAriaLabel="Tamanho da fonte da tabela"
          compact
          aria-label="Tamanho da fonte da tabela"
          value={fontSize}
          options={COMUNICADO_FONT_SIZE_PRESETS}
          min={COMUNICADO_FONT_SIZE_MIN}
          clamp={clampFontSize}
          portalScopeClassName="dashboard-tv-dashboard"
          onChange={(next) => ctrl.applyOptions({ fontSize: clampFontSize(next) })}
          onStepDown={() =>
            ctrl.applyOptions({
              fontSize: clampFontSize(fontSize - COMUNICADO_FONT_SIZE_STEP),
            })
          }
          onStepUp={() =>
            ctrl.applyOptions({
              fontSize: clampFontSize(fontSize + COMUNICADO_FONT_SIZE_STEP),
            })
          }
          stepDownDisabled={fontSize <= COMUNICADO_FONT_SIZE_MIN}
          stepDownAriaLabel="Diminuir fonte"
          stepUpAriaLabel="Aumentar fonte"
          renderStepDown={(button) => (
            <HintAction hint={H.fontSizeDown} ariaLabel="Diminuir fonte">
              {button}
            </HintAction>
          )}
          renderStepUp={(button) => (
            <HintAction hint={H.fontSizeUp} ariaLabel="Aumentar fonte">
              {button}
            </HintAction>
          )}
          renderValue={(control) => (
            <HintAction hint={H.fontSize} ariaLabel="Ajuda: Tamanho da fonte">
              {control}
            </HintAction>
          )}
        />
      </div>
      <div className="td-deck-ribbon__toolbar-row" role="group" aria-label="Estilo tipográfico da tabela">
        <button
          type="button"
          className={`td-btn td-btn--sm${bold ? " td-btn--active" : ""}`}
          aria-pressed={bold}
          aria-label="Negrito"
          title="Negrito"
          onClick={() => ctrl.applyOptions({ fontWeight: bold ? "normal" : "bold" })}
        >
          <Bold size={14} aria-hidden />
        </button>
        <button
          type="button"
          className={`td-btn td-btn--sm${italic ? " td-btn--active" : ""}`}
          aria-pressed={italic}
          aria-label="Itálico"
          title="Itálico"
          onClick={() => ctrl.applyOptions({ fontStyle: italic ? "normal" : "italic" })}
        >
          <Italic size={14} aria-hidden />
        </button>
        <TvRibbonColorPicker
          inline
          variant="text"
          contrastBackground={ctrl.options.cellBg ?? "#ffffff"}
          label="Cor do texto"
          value={textColor}
          onChange={(color) =>
            ctrl.applyOptions({
              cellTextColor: color,
              headerTextColor: color,
            })
          }
        />
        {(
          [
            ["left", AlignLeft, "Alinhar à esquerda"],
            ["center", AlignCenter, "Centralizar"],
            ["right", AlignRight, "Alinhar à direita"],
          ] as const
        ).map(([align, Icon, label]) => (
          <button
            key={align}
            type="button"
            className={`td-btn td-btn--sm${textAlign === align ? " td-btn--active" : ""}`}
            aria-pressed={textAlign === align}
            aria-label={label}
            title={label}
            onClick={() => ctrl.applyOptions({ textAlign: align })}
          >
            <Icon size={14} aria-hidden />
          </button>
        ))}
      </div>
    </div>
  );

  return wrapPane("Fonte", H.tableTypography ?? H.font, layout, body, true, "table-typography");
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

  const shortcuts = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTile
        icon={Shapes}
        label="Forma"
        hint={H.tableOpenFrameShape}
        onClick={ctrl.openFrameShapeChrome}
      />
      <DeckRibbonTile
        icon={Database}
        label="Selecionar dados"
        hint={H.openDataPanel}
        onClick={() => ctrl.openDataPanel()}
      />
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
        <SelectionPaneSection title="Forma e dados" hint={H.tableFormat} defaultOpen={false}>
          {shortcuts}
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
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Shapes}
            label="Forma"
            hint={H.tableOpenFrameShape}
            onClick={ctrl.openFrameShapeChrome}
          />
        </div>
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
