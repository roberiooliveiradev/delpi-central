import { HintAction, ShapeFillMenu, ShapeOutlineMenu } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { useComunicadoEditor } from "../comunicadoEditorContext";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/**
 * Caixa de texto = forma sem fundo: preenchimento e contorno opcionais
 * (padrão transparente / sem contorno).
 * `bare` — sem DeckRibbonGroup (painel/accordion do host).
 */
export function FormatRibbonTextBoxChrome({ bare = false }: { bare?: boolean } = {}) {
  const { selected, updateSelectedStyle } = useComunicadoEditor();
  if (!selected || (selected.type !== "heading" && selected.type !== "text")) return null;

  const fill = selected.style?.fill ?? selected.style?.backgroundColor ?? "transparent";
  const stroke = selected.style?.stroke ?? selected.style?.borderColor ?? "transparent";
  const strokeWidth = selected.style?.strokeWidth ?? selected.style?.borderWidth ?? 0;

  const menus = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      <HintAction hint={H.boxFill} ariaLabel="Ajuda: Preenchimento da caixa">
        <div className="td-deck-ribbon__shape-menu-hint">
          <ShapeFillMenu
            value={fill === "transparent" ? undefined : fill}
            fillLabel="Preench."
            onChange={(color) =>
              updateSelectedStyle({ fill: color, backgroundColor: color })
            }
            onNoFill={() =>
              updateSelectedStyle({ fill: "transparent", backgroundColor: "transparent" })
            }
          />
        </div>
      </HintAction>
      <HintAction hint={H.boxOutline} ariaLabel="Ajuda: Contorno da caixa">
        <div className="td-deck-ribbon__shape-menu-hint">
          <ShapeOutlineMenu
            color={stroke === "transparent" ? undefined : stroke}
            strokeWidth={strokeWidth}
            minWidth={0}
            maxWidth={12}
            outlineLabel="Contorno"
            onColorChange={(color) =>
              updateSelectedStyle({
                stroke: color,
                borderColor: color,
                strokeWidth: Math.max(1, strokeWidth || 1),
                borderWidth: Math.max(1, strokeWidth || 1),
              })
            }
            onNoOutline={() =>
              updateSelectedStyle({
                stroke: "transparent",
                borderColor: "transparent",
                strokeWidth: 0,
                borderWidth: 0,
              })
            }
            onStrokeWidthChange={(width) =>
              updateSelectedStyle({ strokeWidth: width, borderWidth: width })
            }
          />
        </div>
      </HintAction>
    </div>
  );

  if (bare) return menus;

  return (
    <DeckRibbonGroup label="Caixa" hint={H.box}>
      {menus}
    </DeckRibbonGroup>
  );
}
