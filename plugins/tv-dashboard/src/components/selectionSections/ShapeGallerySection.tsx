import { useRef, useState } from "react";
import { Replace } from "lucide-react";
import {
  defaultFrame,
  defaultStrokeWidthForPrimitive,
  resolveShapePrimitive,
  type ComunicadoBlock,
  type ComunicadoShapeKind,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { rememberComunicadoShape } from "../../utils/comunicadoRecentShapes";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ComunicadoShapeLibraryMenu } from "../ComunicadoShapeLibraryMenu";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/** Tile «Alterar forma» — reutilizado dentro do grupo Forma (caixa visual). */
export function ShapeChangeControl() {
  const { selected, updateSelected } = useComunicadoEditor();
  const changeShapeAnchorRef = useRef<HTMLDivElement>(null);
  const [changeShapeOpen, setChangeShapeOpen] = useState(false);

  if (!selected || selected.type !== "shape") return null;

  const block = selected;

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
    updateSelected(patch as Partial<ComunicadoBlock>);
    rememberComunicadoShape(kind);
    setChangeShapeOpen(false);
  };

  return (
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
          onDismiss={() => setChangeShapeOpen(false)}
        />
      ) : null}
    </div>
  );
}

/**
 * @deprecated Preferir `ShapeChangeControl` dentro de `VisualBoxFormaChrome`.
 * Mantido para hosts que ainda resolvem seção `shapeGallery` isolada.
 */
export function ShapeGallerySection({ layout }: { layout: SelectionSectionLayout }) {
  const body = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <ShapeChangeControl />
    </div>
  );

  if (layout === "pane") {
    return (
      <SelectionPaneSection title="Formas" hint={H.shapeChange} defaultOpen={false}>
        {body}
      </SelectionPaneSection>
    );
  }

  return (
    <DeckRibbonGroup label="Formas" hint={H.shapeChange}>
      {body}
    </DeckRibbonGroup>
  );
}
