import {
  mergeTablePartsWithOptions,
  resolveTableFrameStyle,
  resolveTablePartPaintStyle,
  resolveTableShapeChromePartRef,
  tablePartAllowsStroke,
  upsertTablePartState,
  type ComunicadoBlock,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeShadowMenu,
  ShapeStyleMenu,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../../content/comunicadoVisualPresets";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { ShapeMenuHint } from "./ShapeMenuHint";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

/**
 * Chrome de forma da tabela (moldura / parte) — preenchimento, contorno e estilos.
 * Usado na ribbon de parte e pelo botão Forma do Design da Tabela.
 */
export function TableRibbonShapeChrome({ block }: { block: ComunicadoTableViewBlock }) {
  const { selectedTablePart, updateSelected, updateSelectedStyle } = useComunicadoEditor();
  const chromePart = resolveTableShapeChromePartRef(selectedTablePart);
  const isFrameChrome = chromePart.kind === "frame";
  const frame = resolveTableFrameStyle(block.tableParts);
  const partPaint = resolveTablePartPaintStyle(block.tableParts, chromePart);
  const fillValue = isFrameChrome ? frame.fill : (partPaint.backgroundColor ?? "transparent");
  const strokeValue = frame.stroke;
  const strokeWidth = frame.strokeWidth;
  const showStroke = tablePartAllowsStroke(chromePart);

  const patchChromeStyle = (style: Record<string, unknown>) => {
    const nextParts = upsertTablePartState(block.tableParts, chromePart, {
      style: style as never,
    });
    updateSelected({
      tableParts: mergeTablePartsWithOptions(nextParts, block.tableOptions),
      ...(isFrameChrome && typeof style.borderRadius === "number"
        ? { style: { ...block.style, borderRadius: style.borderRadius } }
        : {}),
    } as Partial<ComunicadoBlock>);
  };

  return (
    <>
      <DeckRibbonGroup label="Estilos de forma" hint={H.shapeStyles}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          <ShapeMenuHint hint={H.shapeStyles} ariaLabel="Ajuda: Estilos de forma">
            <ShapeStyleMenu
              triggerLabel="Estilos"
              onSelect={(preset) =>
                patchChromeStyle(
                  showStroke
                    ? {
                        fill: preset.fill,
                        stroke: preset.stroke,
                        strokeWidth: preset.strokeWidth,
                      }
                    : { fill: preset.fill },
                )
              }
            />
          </ShapeMenuHint>
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Preenchimento e linha" hint={H.shapeFillOutline}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          <ShapeMenuHint hint={H.shapeFill} ariaLabel="Ajuda: Preenchimento">
            <ShapeFillMenu
              value={fillValue}
              fillLabel="Preench."
              onChange={(color) => patchChromeStyle({ fill: color })}
              onNoFill={() => patchChromeStyle({ fill: "transparent" })}
            />
          </ShapeMenuHint>
          {showStroke ? (
            <ShapeMenuHint hint={H.shapeOutline} ariaLabel="Ajuda: Contorno">
              <ShapeOutlineMenu
                color={strokeValue}
                strokeWidth={strokeWidth}
                minWidth={0}
                maxWidth={20}
                outlineLabel="Contorno"
                onColorChange={(color) => patchChromeStyle({ stroke: color })}
                onNoOutline={() => patchChromeStyle({ stroke: "transparent", strokeWidth: 0 })}
                onStrokeWidthChange={(width) => patchChromeStyle({ strokeWidth: width })}
              />
            </ShapeMenuHint>
          ) : (
            <p className="td-subtitle td-deck-ribbon__hint">Contorno só na moldura da tabela.</p>
          )}
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Efeitos" hint={H.tableFrameShadow}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          <ShapeMenuHint hint={H.tableFrameShadow} ariaLabel="Ajuda: Sombra da moldura">
            <ShapeShadowMenu
              value={block.style?.boxShadow}
              presets={SHADOW_MENU_PRESETS}
              shadowLabel="Sombra"
              onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
            />
          </ShapeMenuHint>
        </div>
      </DeckRibbonGroup>
    </>
  );
}
