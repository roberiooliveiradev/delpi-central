import { useRef, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  Copy,
  Replace,
  Trash2,
} from "lucide-react";
import {
  defaultFrame,
  defaultStrokeWidthForPrimitive,
  resolveShapePrimitive,
  shapeSupportsFill,
  shapeSupportsStroke,
  type ComunicadoShapeKind,
} from "@delpi/tv-dashboard-presentation";
import { ShapeEffectsMenu, ShapeFillMenu, ShapeOutlineMenu, ShapeStyleMenu } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { rememberComunicadoShape } from "../utils/comunicadoRecentShapes";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoShapeLibraryMenu } from "./ComunicadoShapeLibraryMenu";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

/**
 * Faixa contextual «Forma» — espelha a aba Forma do PowerPoint Online:
 * Alterar forma · Estilos · Preenchimento · Contorno · Organizar · Tamanho.
 */
export function ComunicadoShapeRibbon() {
  const {
    selected,
    updateSelected,
    updateSelectedStyle,
    removeSelected,
    duplicateSelected,
    moveLayer,
  } = useComunicadoEditor();
  const changeShapeAnchorRef = useRef<HTMLDivElement>(null);
  const [changeShapeOpen, setChangeShapeOpen] = useState(false);

  if (!selected || selected.type !== "shape") {
    return (
      <div className="td-deck-ribbon__groups">
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione uma forma no palco para editar estilo, preenchimento, contorno e tamanho (como no
          PowerPoint).
        </p>
      </div>
    );
  }

  const block = selected;
  const primitive = resolveShapePrimitive(block.shape);
  const showFill = shapeSupportsFill(primitive);
  const showStroke = shapeSupportsStroke(primitive);
  const defaultStrokeWidth = block.style?.strokeWidth ?? defaultStrokeWidthForPrimitive(primitive);

  const applyShapeKind = (kind: ComunicadoShapeKind) => {
    const prevPrimitive = resolveShapePrimitive(block.shape);
    const nextPrimitive = resolveShapePrimitive(kind);
    const patch: Record<string, unknown> = { shape: kind };
    if (prevPrimitive !== nextPrimitive) {
      const nextFrame = defaultFrame("shape", kind);
      patch.frame = {
        ...nextFrame,
        x: Math.max(0, Math.min(100 - nextFrame.w, block.frame.x)),
        y: Math.max(0, Math.min(100 - nextFrame.h, block.frame.y)),
      };
      patch.style = {
        ...block.style,
        strokeWidth: defaultStrokeWidthForPrimitive(nextPrimitive),
        ...(nextPrimitive === "point"
          ? { markerRadius: block.style?.markerRadius ?? 8 }
          : {}),
      };
    }
    updateSelected(patch as Partial<typeof selected>);
    rememberComunicadoShape(kind);
    setChangeShapeOpen(false);
  };

  const setFrameSize = (axis: "w" | "h", raw: number) => {
    const value = Math.max(0.5, Math.min(100, Number.isFinite(raw) ? raw : block.frame[axis]));
    const next = { ...block.frame, [axis]: value };
    if (axis === "w") {
      next.x = Math.max(0, Math.min(100 - value, block.frame.x));
    } else {
      next.y = Math.max(0, Math.min(100 - value, block.frame.y));
    }
    updateSelected({ frame: next } as Partial<typeof selected>);
  };

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Formas" hint={H.shapeChange}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <div ref={changeShapeAnchorRef} className="td-composer__dropdown">
            <DeckRibbonTile
              icon={Replace}
              label="Alterar forma"
              hint={H.shapeChange}
              active={changeShapeOpen}
              onClick={() => setChangeShapeOpen((open) => !open)}
            />
            {changeShapeOpen ? (
              <ComunicadoShapeLibraryMenu
                open={changeShapeOpen}
                anchorRef={changeShapeAnchorRef}
                onSelect={applyShapeKind}
              />
            ) : null}
          </div>
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Estilos de forma" hint={H.shape}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          <ShapeStyleMenu
            onSelect={(preset) =>
              updateSelectedStyle({
                fill: preset.fill,
                stroke: preset.stroke,
                strokeWidth: preset.strokeWidth,
                boxShadow: preset.boxShadow,
              })
            }
          />
          <ShapeEffectsMenu
            onSelect={(effectId, optionId) => {
              if (effectId === "shadow" && !optionId) {
                updateSelectedStyle({ boxShadow: "0 4px 14px rgba(0, 0, 0, 0.28)" });
              }
            }}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Preenchimento" hint={H.shape}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          {showFill ? (
            <ShapeFillMenu
              value={block.style?.fill ?? "#089bdb"}
              fillLabel={primitive === "point" ? "Cor" : "Preench."}
              onChange={(color) => updateSelectedStyle({ fill: color })}
              onNoFill={() => updateSelectedStyle({ fill: "transparent" })}
            />
          ) : (
            <p className="td-subtitle td-deck-ribbon__hint">Sem preenchimento nesta forma.</p>
          )}
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Contorno" hint={H.strokeWidth}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          {showStroke ? (
            <ShapeOutlineMenu
              color={block.style?.stroke ?? "#ffffff"}
              strokeWidth={defaultStrokeWidth}
              minWidth={primitive === "point" ? 0 : 0}
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
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Organizar" hint={H.organize}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile icon={Copy} label="Duplicar" hint={H.duplicateBlock} onClick={duplicateSelected} />
          <DeckRibbonTile icon={ArrowUp} label="Frente" hint={E.layerUp} onClick={() => moveLayer("up")} />
          <DeckRibbonTile icon={ArrowDown} label="Fundo" hint={E.layerDown} onClick={() => moveLayer("down")} />
          <DeckRibbonTile icon={Trash2} label="Remover" hint={E.remove} onClick={removeSelected} />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Tamanho" hint={H.shapeSize}>
        <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--inline">
          <label className="td-deck-ribbon__field-label" htmlFor="td-shape-width">
            Largura %
          </label>
          <input
            id="td-shape-width"
            type="number"
            className="td-deck-ribbon__number td-deck-ribbon__number--compact"
            min={0.5}
            max={100}
            step={0.5}
            aria-label="Largura da forma em percentual do slide"
            value={Number(block.frame.w.toFixed(1))}
            onChange={(e) => setFrameSize("w", Number(e.target.value))}
          />
          <label className="td-deck-ribbon__field-label" htmlFor="td-shape-height">
            Altura %
          </label>
          <input
            id="td-shape-height"
            type="number"
            className="td-deck-ribbon__number td-deck-ribbon__number--compact"
            min={0.5}
            max={100}
            step={0.5}
            aria-label="Altura da forma em percentual do slide"
            value={Number(block.frame.h.toFixed(1))}
            onChange={(e) => setFrameSize("h", Number(e.target.value))}
          />
        </div>
      </DeckRibbonGroup>
    </div>
  );
}
