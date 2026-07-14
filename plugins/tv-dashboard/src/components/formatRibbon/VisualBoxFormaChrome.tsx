import {
  defaultStrokeWidthForPrimitive,
  isComunicadoVisualBoxBlock,
  resolveShapePrimitive,
  resolveVisualBoxProfile,
  shapeSupportsFill,
  shapeSupportsStroke,
  type ComunicadoBlockStyle,
  type ComunicadoVisualBoxBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  DECK_SHAPE_DEFAULTS,
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeShadowMenu,
  ShapeStyleMenu,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../../content/comunicadoVisualPresets";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ShapeAdjustmentsControl } from "../ShapeAdjustmentsControl";
import { ShapeCornerRadiusControl } from "../ShapeCornerRadiusControl";
import { DeckRangeField } from "../deck/DeckRangeField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { SelectionPaneSection } from "../selectionSections/SelectionPaneSection";
import { ShapeChangeControl } from "../selectionSections/ShapeGallerySection";
import type { SelectionSectionLayout } from "../selectionSections/types";
import { resolveVisualBoxElementCapabilities } from "../selectionSections/visualBoxElementCapabilities";
import { FormatRibbonOpacityFields } from "./FormatRibbonOrganizeSection";
import { ShapeMenuHint } from "./ShapeMenuHint";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const FORMA_HINT = H.shapeForma;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

const TEXT_BOX_CHROME_DEFAULTS = {
  fill: "transparent",
  stroke: "transparent",
  strokeWidth: 0,
} as const;

function resolveFormaFill(block: ComunicadoVisualBoxBlock, isTextMode: boolean): string {
  if (isTextMode) {
    return (
      block.style?.fill ??
      block.style?.backgroundColor ??
      TEXT_BOX_CHROME_DEFAULTS.fill
    );
  }
  return block.style?.fill ?? DECK_SHAPE_DEFAULTS.fill;
}

function resolveFormaStroke(
  block: ComunicadoVisualBoxBlock,
  isTextMode: boolean,
  primitive: ReturnType<typeof resolveShapePrimitive> | undefined,
): string {
  if (isTextMode) {
    return (
      block.style?.stroke ??
      block.style?.borderColor ??
      TEXT_BOX_CHROME_DEFAULTS.stroke
    );
  }
  return (
    block.style?.stroke ??
    (primitive === "line" ? DECK_SHAPE_DEFAULTS.lineStroke : DECK_SHAPE_DEFAULTS.stroke)
  );
}

function resolveFormaStrokeWidth(
  block: ComunicadoVisualBoxBlock,
  isTextMode: boolean,
  primitive: ReturnType<typeof resolveShapePrimitive> | undefined,
): number {
  if (isTextMode) {
    return (
      block.style?.strokeWidth ??
      block.style?.borderWidth ??
      TEXT_BOX_CHROME_DEFAULTS.strokeWidth
    );
  }
  if (primitive === "point") return 0;
  return block.style?.strokeWidth ?? defaultStrokeWidthForPrimitive(primitive!);
}

/**
 * Patch de estilo da caixa visual — texto espelha fill/stroke em backgroundColor/border*
 * (legado do paint); forma usa as chaves canônicas.
 */
function patchVisualBoxStyle(
  isTextMode: boolean,
  updateSelectedStyle: (patch: Partial<ComunicadoBlockStyle>) => void,
  patch: Partial<ComunicadoBlockStyle>,
): void {
  if (!isTextMode) {
    updateSelectedStyle(patch);
    return;
  }
  const next: Partial<ComunicadoBlockStyle> = { ...patch };
  if (typeof patch.fill === "string") {
    next.fill = patch.fill;
    next.backgroundColor = patch.fill;
  }
  if (typeof patch.stroke === "string") {
    next.stroke = patch.stroke;
    next.borderColor = patch.stroke;
  }
  if (typeof patch.strokeWidth === "number") {
    next.strokeWidth = patch.strokeWidth;
    next.borderWidth = patch.strokeWidth;
  }
  updateSelectedStyle(next);
}

type VisualBoxFormaChromeProps = {
  layout: SelectionSectionLayout;
  /** Painel/accordion: omite DeckRibbonGroup. */
  bare?: boolean;
};

/**
 * Forma unificada (texto/título e shape) — mesmas opções; flags via
 * `resolveVisualBoxElementCapabilities` (ex.: Alterar forma só em shape).
 */
export function VisualBoxFormaChrome({ layout, bare = false }: VisualBoxFormaChromeProps) {
  const { selected, updateSelectedStyle } = useComunicadoEditor();
  if (!selected || !isComunicadoVisualBoxBlock(selected)) return null;

  const caps = resolveVisualBoxElementCapabilities(selected);
  if (!caps?.shapeChrome) return null;

  const block = selected;
  const profile = resolveVisualBoxProfile(block);
  const isTextMode = profile.mode === "text";
  const primitive =
    profile.mode === "shape" && block.type === "shape"
      ? resolveShapePrimitive(block.shape)
      : undefined;

  const showFill = isTextMode || (primitive != null && shapeSupportsFill(primitive));
  const showStroke = isTextMode || (primitive != null && shapeSupportsStroke(primitive));
  const showCornerRadius = isTextMode || primitive !== "point";
  const showShapeAdjustments = caps.shapeAdjustments && block.type === "shape";
  const showMarker = caps.shapeMarker && block.type === "shape";

  const fillValue = resolveFormaFill(block, isTextMode);
  const strokeValue = resolveFormaStroke(block, isTextMode, primitive);
  const strokeWidth = resolveFormaStrokeWidth(block, isTextMode, primitive);
  const borderRadius = block.style?.borderRadius ?? 0;

  const patchStyle = (patch: Partial<ComunicadoBlockStyle>) =>
    patchVisualBoxStyle(isTextMode, updateSelectedStyle, patch);

  const stylesMenus = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      {caps.shapeGallery ? <ShapeChangeControl /> : null}
      <ShapeMenuHint hint={H.shapeStyles} ariaLabel="Ajuda: Estilos de forma">
        <ShapeStyleMenu
          triggerLabel="Estilos"
          onSelect={(preset) =>
            patchStyle({
              fill: preset.fill,
              stroke: preset.stroke,
              strokeWidth: preset.strokeWidth,
              boxShadow: preset.boxShadow,
            })
          }
        />
      </ShapeMenuHint>
      <ShapeMenuHint hint={H.boxShadow} ariaLabel="Ajuda: Sombra da forma">
        <ShapeShadowMenu
          value={block.style?.boxShadow}
          presets={SHADOW_MENU_PRESETS}
          shadowLabel="Sombra"
          onChange={(boxShadow) => patchStyle({ boxShadow })}
        />
      </ShapeMenuHint>
      {showFill ? (
        <ShapeMenuHint hint={H.shapeFill} ariaLabel="Ajuda: Preenchimento da forma">
          <ShapeFillMenu
            value={
              fillValue === "transparent" && isTextMode ? undefined : fillValue
            }
            fillLabel={primitive === "point" ? "Cor" : "Preench."}
            onChange={(color) => patchStyle({ fill: color })}
            onNoFill={() => patchStyle({ fill: "transparent" })}
          />
        </ShapeMenuHint>
      ) : null}
      {showStroke ? (
        <ShapeMenuHint hint={H.shapeOutline} ariaLabel="Ajuda: Contorno da forma">
          <ShapeOutlineMenu
            color={
              strokeValue === "transparent" && isTextMode ? undefined : strokeValue
            }
            strokeWidth={strokeWidth}
            minWidth={0}
            maxWidth={primitive === "point" ? 8 : 20}
            outlineLabel="Contorno"
            onColorChange={(color) =>
              patchStyle({
                stroke: color,
                strokeWidth: Math.max(1, strokeWidth || 1),
              })
            }
            onNoOutline={() =>
              patchStyle({
                stroke: "transparent",
                strokeWidth: 0,
              })
            }
            onStrokeWidthChange={(width) => patchStyle({ strokeWidth: width })}
          />
        </ShapeMenuHint>
      ) : null}
    </div>
  );

  const formaBody = (
    <>
      {stylesMenus}
      {!showFill && !showStroke ? (
        <p className="td-subtitle td-deck-ribbon__hint">Sem preenchimento nem contorno nesta forma.</p>
      ) : null}
      <div className="td-deck-ribbon__organize-props td-forma-opacity">
        {showCornerRadius ? (
          <ShapeCornerRadiusControl
            id={isTextMode ? "td-textbox-forma-corner-radius" : "td-shape-forma-corner-radius"}
            value={borderRadius}
            onChange={(radius) => patchStyle({ borderRadius: radius })}
            embedded
          />
        ) : null}
        <FormatRibbonOpacityFields className="td-forma-opacity__slot" />
      </div>
    </>
  );

  const extrasPane =
    showShapeAdjustments || showMarker ? (
      <>
        {showShapeAdjustments && block.type === "shape" ? (
          <SelectionPaneSection title="Ajustes da forma" hint={H.shapeAdjustment} defaultOpen={false}>
            <ShapeAdjustmentsControl
              kind={block.shape}
              style={block.style}
              onChange={(patch) => updateSelectedStyle(patch)}
              variant="inspector"
              idPrefix="td-frame-shape-adj"
            />
          </SelectionPaneSection>
        ) : null}
        {showMarker && block.type === "shape" ? (
          <SelectionPaneSection title="Marcador" hint={H.markerRadius} defaultOpen={false}>
            <DeckRangeField
              id="td-shape-marker-radius"
              label="Raio px"
              hint={H.markerRadius}
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
    ) : null;

  const extrasRibbon =
    showShapeAdjustments || showMarker ? (
      <>
        {showShapeAdjustments && block.type === "shape" ? (
          <ShapeAdjustmentsControl
            kind={block.shape}
            style={block.style}
            onChange={(patch) => updateSelectedStyle(patch)}
            variant="ribbon"
          />
        ) : null}
        {showMarker && block.type === "shape" ? (
          <DeckRibbonGroup label="Marcador" hint={H.markerRadius}>
            <DeckRangeField
              id="td-shape-marker-radius"
              label="Raio px"
              hint={H.markerRadius}
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
    ) : null;

  if (layout === "pane") {
    return (
      <>
        <div id="td-shape-pane-forma">
          {bare ? (
            formaBody
          ) : (
            <SelectionPaneSection title="Forma" hint={FORMA_HINT} defaultOpen>
              {formaBody}
            </SelectionPaneSection>
          )}
        </div>
        {extrasPane}
      </>
    );
  }

  if (bare) {
    return (
      <>
        {formaBody}
        {extrasRibbon}
      </>
    );
  }

  return (
    <>
      <DeckRibbonGroup label="Forma" hint={FORMA_HINT}>
        {formaBody}
      </DeckRibbonGroup>
      {extrasRibbon}
    </>
  );
}
