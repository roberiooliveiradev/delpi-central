import {
  defaultStrokeWidthForPrimitive,
  resolveShapePrimitive,
  shapeHasAdjustments,
  shapeSupportsFill,
  shapeSupportsStroke,
} from "@delpi/tv-dashboard-presentation";
import {
  DECK_SHAPE_DEFAULTS,
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeShadowMenu,
  ShapeStyleRibbonStrip,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../../content/comunicadoVisualPresets";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckPropertySection } from "../deck/DeckPropertySection";
import { DeckRangeField } from "../deck/DeckRangeField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { ShapeAdjustmentsControl } from "../ShapeAdjustmentsControl";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

/**
 * Preenchimento / contorno / estilos / sombra de forma pura (`type === "shape"`).
 * KPI/input/chart continuam nas ribbons tipadas até migrarem.
 */
export function ShapeChromeSection({ layout }: { layout: SelectionSectionLayout }) {
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
      <ShapeStyleRibbonStrip
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
          <DeckPropertySection title="Preenchimento e linha" defaultOpen>
            {fillMenus}
            {strokeMenus}
          </DeckPropertySection>
        </div>
        <div id="td-shape-pane-effects">
          <DeckPropertySection title="Efeitos" defaultOpen={false}>
            <ShapeShadowMenu
              value={block.style?.boxShadow}
              presets={SHADOW_MENU_PRESETS}
              shadowLabel="Sombra"
              onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
            />
            <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
              <ShapeStyleRibbonStrip
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
          </DeckPropertySection>
        </div>
        {showShapeAdjustments ? (
          <DeckPropertySection title="Ajustes da forma" defaultOpen={false}>
            <ShapeAdjustmentsControl
              kind={block.shape}
              style={block.style}
              onChange={(patch) => updateSelectedStyle(patch)}
              variant="inspector"
              idPrefix="td-frame-shape-adj"
            />
          </DeckPropertySection>
        ) : null}
        {primitive === "point" ? (
          <DeckPropertySection title="Marcador" hint={H.shapeSize} defaultOpen={false}>
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
          </DeckPropertySection>
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
