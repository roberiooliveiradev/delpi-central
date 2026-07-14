import {
  defaultStrokeWidthForPrimitive,
  getInputPartState,
  getKpiPartState,
  inputPartBoxChromeLabels,
  kpiPartBoxChromeLabels,
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  resolveInputShapeChromePartRef,
  resolveKpiShapeChromePartRef,
  resolveShapePrimitive,
  shapeHasAdjustments,
  shapeSupportsFill,
  shapeSupportsStroke,
  upsertInputPartState,
  upsertKpiPartState,
  type ComunicadoBlock,
  type ComunicadoInputBlock,
  type ComunicadoKpiViewBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  DECK_COLOR_BORDER,
  DECK_COLOR_SURFACE,
  DECK_INPUT_DEFAULTS,
  DECK_SHAPE_DEFAULTS,
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeShadowMenu,
  ShapeStyleMenu,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../../content/comunicadoVisualPresets";
import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ShapeAdjustmentsControl } from "../ShapeAdjustmentsControl";
import { DeckRangeField } from "../deck/DeckRangeField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { PartSelectionNav } from "./PartSelectionNav";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

/**
 * Chrome de preenchimento/contorno — forma, KPI (parte) e input (parte/frame).
 */
export function ShapeChromeSection({ layout }: { layout: SelectionSectionLayout }) {
  const {
    selected,
    selectedKpiPart,
    selectedInputPart,
    selectedChartPart,
    selectedTablePart,
    updateSelected,
    updateSelectedStyle,
    clearKpiPartSelection,
    clearInputPartSelection,
  } = useComunicadoEditor();

  if (!selected) return null;

  if (selected.type === "shape") {
    return <ShapeBlockChrome layout={layout} />;
  }

  if (selected.type === "kpi_view") {
    return (
      <KpiShapeChrome
        layout={layout}
        block={selected as ComunicadoKpiViewBlock}
        selectedKpiPart={selectedKpiPart}
        onClearPart={clearKpiPartSelection}
        updateSelected={updateSelected}
        updateSelectedStyle={updateSelectedStyle}
      />
    );
  }

  if (selected.type === "input") {
    const chromeMode = resolveSelectionChromeMode({
      selected,
      selectedKpiPart,
      selectedChartPart,
      selectedTablePart,
      selectedInputPart,
    });
    return (
      <InputShapeChrome
        layout={layout}
        block={selected as ComunicadoInputBlock}
        selectedInputPart={selectedInputPart}
        partChrome={isPartSelectionChrome(chromeMode) ? chromeMode : null}
        onClearPart={clearInputPartSelection}
        updateSelected={updateSelected}
      />
    );
  }

  return null;
}

function ShapeBlockChrome({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, updateSelectedStyle } = useComunicadoEditor();
  if (!selected || selected.type !== "shape") return null;

  const block = selected;
  const primitive = resolveShapePrimitive(block.shape);
  const showFill = shapeSupportsFill(primitive);
  const showStroke = shapeSupportsStroke(primitive);
  const defaultStrokeWidth = block.style?.strokeWidth ?? defaultStrokeWidthForPrimitive(primitive);
  const showShapeAdjustments = shapeHasAdjustments(block.shape);

  const stylesMenus = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      <ShapeStyleMenu
        triggerLabel="Estilos"
        onSelect={(preset) =>
          updateSelectedStyle({
            fill: preset.fill,
            stroke: preset.stroke,
            strokeWidth: preset.strokeWidth,
            boxShadow: preset.boxShadow,
          })
        }
      />
      <ShapeShadowMenu
        value={block.style?.boxShadow}
        presets={SHADOW_MENU_PRESETS}
        shadowLabel="Sombra"
        onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
      />
    </div>
  );

  const fillMenus = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      {showFill ? (
        <ShapeFillMenu
          value={block.style?.fill ?? DECK_SHAPE_DEFAULTS.fill}
          fillLabel={primitive === "point" ? "Cor" : "Preench."}
          onChange={(color) => updateSelectedStyle({ fill: color })}
          onNoFill={() => updateSelectedStyle({ fill: "transparent" })}
        />
      ) : (
        <p className="td-subtitle td-deck-ribbon__hint">Sem preenchimento nesta forma.</p>
      )}
    </div>
  );

  const strokeMenus = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      {showStroke ? (
        <ShapeOutlineMenu
          color={
            block.style?.stroke ??
            (primitive === "line" ? DECK_SHAPE_DEFAULTS.lineStroke : DECK_SHAPE_DEFAULTS.stroke)
          }
          strokeWidth={defaultStrokeWidth}
          minWidth={0}
          maxWidth={primitive === "point" ? 8 : 20}
          outlineLabel="Contorno"
          onColorChange={(color) => updateSelectedStyle({ stroke: color })}
          onNoOutline={() => updateSelectedStyle({ stroke: "transparent" })}
          onStrokeWidthChange={(width) => updateSelectedStyle({ strokeWidth: width })}
        />
      ) : (
        <p className="td-subtitle td-deck-ribbon__hint">Sem contorno nesta forma.</p>
      )}
    </div>
  );

  if (layout === "pane") {
    return (
      <>
        <div id="td-shape-pane-fill-line">
          <SelectionPaneSection title="Preenchimento e linha" defaultOpen>
            {fillMenus}
            {strokeMenus}
          </SelectionPaneSection>
        </div>
        <div id="td-shape-pane-effects">
          <SelectionPaneSection title="Efeitos" defaultOpen={false}>
            <ShapeShadowMenu
              value={block.style?.boxShadow}
              presets={SHADOW_MENU_PRESETS}
              shadowLabel="Sombra"
              onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
            />
            <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
              <ShapeStyleMenu
                triggerLabel="Estilos"
                onSelect={(preset) =>
                  updateSelectedStyle({
                    fill: preset.fill,
                    stroke: preset.stroke,
                    strokeWidth: preset.strokeWidth,
                    boxShadow: preset.boxShadow,
                  })
                }
              />
            </div>
          </SelectionPaneSection>
        </div>
        {showShapeAdjustments ? (
          <SelectionPaneSection title="Ajustes da forma" defaultOpen={false}>
            <ShapeAdjustmentsControl
              kind={block.shape}
              style={block.style}
              onChange={(patch) => updateSelectedStyle(patch)}
              variant="inspector"
              idPrefix="td-frame-shape-adj"
            />
          </SelectionPaneSection>
        ) : null}
        {primitive === "point" ? (
          <SelectionPaneSection title="Marcador" hint={H.shapeSize} defaultOpen={false}>
            <DeckRangeField
              id="td-shape-marker-radius"
              label="Raio px"
              hint={H.shapeSize}
              min={2}
              max={48}
              step={1}
              value={block.style?.markerRadius ?? 8}
              aria-label="Raio do ponto em pixels"
              onChange={(value) =>
                updateSelectedStyle({ markerRadius: Math.max(2, Math.min(48, value || 8)) })
              }
            />
          </SelectionPaneSection>
        ) : null}
      </>
    );
  }

  return (
    <>
      <DeckRibbonGroup label="Estilos de forma" hint={H.shape}>
        {stylesMenus}
      </DeckRibbonGroup>
      <DeckRibbonGroup label="Preenchimento" hint={H.shape}>
        {fillMenus}
      </DeckRibbonGroup>
      <DeckRibbonGroup label="Contorno" hint={H.strokeWidth}>
        {strokeMenus}
      </DeckRibbonGroup>
      {showShapeAdjustments ? (
        <ShapeAdjustmentsControl
          kind={block.shape}
          style={block.style}
          onChange={(patch) => updateSelectedStyle(patch)}
          variant="ribbon"
        />
      ) : null}
      {primitive === "point" ? (
        <DeckRibbonGroup label="Marcador" hint={H.shapeSize}>
          <DeckRangeField
            id="td-shape-marker-radius"
            label="Raio px"
            hint={H.shapeSize}
            min={2}
            max={48}
            step={1}
            value={block.style?.markerRadius ?? 8}
            aria-label="Raio do ponto em pixels"
            onChange={(value) =>
              updateSelectedStyle({ markerRadius: Math.max(2, Math.min(48, value || 8)) })
            }
          />
        </DeckRibbonGroup>
      ) : null}
    </>
  );
}

function KpiShapeChrome({
  layout,
  block,
  selectedKpiPart,
  onClearPart,
  updateSelected,
  updateSelectedStyle,
}: {
  layout: SelectionSectionLayout;
  block: ComunicadoKpiViewBlock;
  selectedKpiPart: ReturnType<typeof useComunicadoEditor>["selectedKpiPart"];
  onClearPart: () => void;
  updateSelected: ReturnType<typeof useComunicadoEditor>["updateSelected"];
  updateSelectedStyle: ReturnType<typeof useComunicadoEditor>["updateSelectedStyle"];
}) {
  const chromePart = resolveKpiShapeChromePartRef(selectedKpiPart);
  if (!chromePart) {
    if (layout === "ribbon") {
      return (
        <p className="td-subtitle td-deck-ribbon__hint">
          Seleção global do KPI — posição, tamanho e organizar. Clique no fundo ou numa parte
          para formatar preenchimento e contorno.
        </p>
      );
    }
    return null;
  }

  const partState = getKpiPartState(block.kpiParts, chromePart);
  const isCardChrome = chromePart.kind === "card";
  const boxLabels = kpiPartBoxChromeLabels(chromePart.kind);
  const cardState = getKpiPartState(block.kpiParts, { kind: "card" });
  const fillValue = isCardChrome
    ? (cardState?.style?.fill ?? block.kpiOptions?.backgroundColor ?? DECK_COLOR_SURFACE)
    : (partState?.style?.fill ?? "transparent");
  const strokeValue = isCardChrome
    ? (cardState?.style?.stroke ?? DECK_COLOR_BORDER)
    : (partState?.style?.stroke ?? "transparent");
  const strokeWidth = isCardChrome
    ? (cardState?.style?.strokeWidth ?? 1)
    : (partState?.style?.strokeWidth ?? 0);

  const patchChromeStyle = (style: Record<string, unknown>) => {
    const nextParts = upsertKpiPartState(block.kpiParts, chromePart, {
      style: style as never,
    });
    const fromParts = partsToKpiOptions(nextParts);
    const nextOptions = mergeComunicadoKpiOptions({
      ...block.kpiOptions,
      ...fromParts,
      ...(isCardChrome && typeof style.fill === "string"
        ? { backgroundColor: style.fill }
        : {}),
    });
    updateSelected({
      kpiParts: mergeKpiPartsWithOptions(nextParts, nextOptions),
      kpiOptions: nextOptions,
    } as Partial<ComunicadoBlock>);
  };

  const chromeMode = resolveSelectionChromeMode({
    selected: block,
    selectedKpiPart,
  });
  const nav =
    isPartSelectionChrome(chromeMode) && chromeMode.source === "kpi" ? (
      <PartSelectionNav chrome={chromeMode} onBack={onClearPart} />
    ) : null;

  const menus = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      <ShapeStyleMenu
        triggerLabel="Estilos"
        onSelect={(preset) =>
          patchChromeStyle({
            fill: preset.fill,
            stroke: preset.stroke,
            strokeWidth: preset.strokeWidth,
          })
        }
      />
      <ShapeFillMenu
        value={fillValue}
        fillLabel={boxLabels.fillShort}
        onChange={(color) => patchChromeStyle({ fill: color })}
        onNoFill={() => patchChromeStyle({ fill: "transparent" })}
      />
      <ShapeOutlineMenu
        color={strokeValue}
        strokeWidth={strokeWidth}
        minWidth={0}
        maxWidth={20}
        outlineLabel={boxLabels.strokeShort}
        onColorChange={(color) => patchChromeStyle({ stroke: color })}
        onNoOutline={() => patchChromeStyle({ stroke: "transparent", strokeWidth: 0 })}
        onStrokeWidthChange={(width) => patchChromeStyle({ strokeWidth: width })}
      />
      {isCardChrome ? (
        <ShapeShadowMenu
          value={block.style?.boxShadow}
          presets={SHADOW_MENU_PRESETS}
          shadowLabel="Sombra"
          onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
        />
      ) : null}
    </div>
  );

  const hint = isCardChrome
    ? H.shape
    : "Fundo e borda da caixa desta parte — não alteram o fundo do card.";

  if (layout === "pane") {
    return (
      <>
        {nav}
        <SelectionPaneSection title="Aparência" hint={hint} defaultOpen>
          {menus}
        </SelectionPaneSection>
      </>
    );
  }

  return (
    <>
      {nav}
      <DeckRibbonGroup label="Aparência" hint={hint}>
        {menus}
      </DeckRibbonGroup>
    </>
  );
}

type PartChrome = Extract<
  ReturnType<typeof resolveSelectionChromeMode>,
  { mode: "part" }
>;

function InputShapeChrome({
  layout,
  block,
  selectedInputPart,
  partChrome,
  onClearPart,
  updateSelected,
}: {
  layout: SelectionSectionLayout;
  block: ComunicadoInputBlock;
  selectedInputPart: ReturnType<typeof useComunicadoEditor>["selectedInputPart"];
  partChrome: PartChrome | null;
  onClearPart: () => void;
  updateSelected: ReturnType<typeof useComunicadoEditor>["updateSelected"];
}) {
  const chromePart = resolveInputShapeChromePartRef(selectedInputPart) ?? {
    kind: "frame" as const,
  };
  const partState = getInputPartState(block.inputParts, chromePart);
  const isFrameChrome = chromePart.kind === "frame";
  const boxLabels = inputPartBoxChromeLabels(chromePart.kind);
  const fillValue =
    partState?.style?.fill ??
    (isFrameChrome ? DECK_INPUT_DEFAULTS.backgroundColor : "transparent");
  const strokeValue =
    partState?.style?.stroke ??
    (isFrameChrome ? DECK_INPUT_DEFAULTS.borderColor : "transparent");
  const strokeWidth =
    partState?.style?.strokeWidth ??
    (isFrameChrome ? DECK_INPUT_DEFAULTS.borderWidth : 0);

  const patchChromeStyle = (style: Record<string, unknown>) => {
    updateSelected({
      inputParts: upsertInputPartState(block.inputParts, chromePart, {
        style: style as never,
      }),
    } as Partial<ComunicadoBlock>);
  };

  const frameShadow =
    getInputPartState(block.inputParts, { kind: "frame" })?.style?.boxShadow ??
    block.style?.boxShadow;

  const nav =
    partChrome && partChrome.source === "input" ? (
      <PartSelectionNav chrome={partChrome} onBack={onClearPart} />
    ) : null;

  const menus = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      <ShapeFillMenu
        value={fillValue}
        fillLabel={boxLabels.fillShort}
        onChange={(color) => patchChromeStyle({ fill: color })}
        onNoFill={() => patchChromeStyle({ fill: "transparent" })}
      />
      <ShapeOutlineMenu
        color={strokeValue}
        strokeWidth={strokeWidth}
        minWidth={0}
        maxWidth={20}
        outlineLabel={boxLabels.strokeShort}
        onColorChange={(color) => patchChromeStyle({ stroke: color })}
        onNoOutline={() => patchChromeStyle({ stroke: "transparent", strokeWidth: 0 })}
        onStrokeWidthChange={(width) => patchChromeStyle({ strokeWidth: width })}
      />
      {isFrameChrome ? (
        <ShapeShadowMenu
          value={typeof frameShadow === "string" ? frameShadow : undefined}
          presets={SHADOW_MENU_PRESETS}
          shadowLabel="Sombra"
          onChange={(boxShadow) => {
            const nextShadow = boxShadow?.trim() ? boxShadow : undefined;
            updateSelected({
              inputParts: upsertInputPartState(block.inputParts, { kind: "frame" }, {
                style: { boxShadow: nextShadow },
              }),
              style: { ...block.style, boxShadow: nextShadow },
            } as Partial<ComunicadoBlock>);
          }}
        />
      ) : null}
    </div>
  );

  if (layout === "pane") {
    return (
      <>
        {nav}
        <SelectionPaneSection title="Aparência" hint={H.shape} defaultOpen>
          {menus}
        </SelectionPaneSection>
      </>
    );
  }

  return (
    <>
      {nav}
      <DeckRibbonGroup label="Aparência" hint={H.shape}>
        {menus}
      </DeckRibbonGroup>
    </>
  );
}
