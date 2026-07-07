import { useLayoutEffect, useRef, useState, type CSSProperties, type RefObject } from "react";
import { createPortal } from "react-dom";
import { BarChart3, Heading, Image as ImageIcon, Shapes, Text, Video } from "lucide-react";
import { COMUNICADO_SHAPE_KINDS } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DataRoutePickerModal } from "./DataRoutePickerModal";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

function ShapeDropdownMenu({
  anchorRef,
  onSelect,
}: {
  anchorRef: RefObject<HTMLDivElement | null>;
  onSelect: (kind: (typeof COMUNICADO_SHAPE_KINDS)[number]["kind"]) => void;
}) {
  const [style, setStyle] = useState<CSSProperties>({ visibility: "hidden" });

  useLayoutEffect(() => {
    const anchor = anchorRef.current;
    if (!anchor) return;

    const rect = anchor.getBoundingClientRect();
    setStyle({
      position: "fixed",
      top: rect.bottom + 4,
      left: rect.left,
      zIndex: 5000,
      visibility: "visible",
    });
  }, [anchorRef]);

  return createPortal(
    <div className="td-composer__dropdown-menu td-composer__dropdown-menu--portal" role="menu" style={style}>
      {COMUNICADO_SHAPE_KINDS.map((item) => (
        <button
          key={item.kind}
          type="button"
          role="menuitem"
          className="td-composer__dropdown-item"
          onClick={() => onSelect(item.kind)}
        >
          {item.label}
        </button>
      ))}
    </div>,
    document.body,
  );
}

export function ComunicadoInsertRibbon({ labels = {} }: { labels?: Labels }) {
  const { shapeMenuOpen, setShapeMenuOpen, addBlock, addShape, addDataBlock } = useComunicadoEditor();
  const shapeAnchorRef = useRef<HTMLDivElement>(null);
  const [dataPickerOpen, setDataPickerOpen] = useState(false);

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Inserir" hint={H.insert}>
        <div className="td-deck-ribbon__tiles">
          <DeckRibbonTile
            icon={BarChart3}
            label={labels.comunicadoAddIndicator ?? "Indicador"}
            hint={H.insertIndicator ?? H.insert}
            onClick={() => setDataPickerOpen(true)}
          />
          <DeckRibbonTile
            icon={Heading}
            label={labels.comunicadoAddHeading ?? "Título"}
            hint={H.insertHeading}
            onClick={() => addBlock("heading")}
          />
          <DeckRibbonTile
            icon={Text}
            label={labels.comunicadoAddText ?? "Texto"}
            hint={H.insertText}
            onClick={() => addBlock("text")}
          />
          <DeckRibbonTile
            icon={ImageIcon}
            label={labels.comunicadoAddImage ?? "Imagem"}
            hint={H.insertImage}
            onClick={() => addBlock("image")}
          />
          <DeckRibbonTile
            icon={Video}
            label={labels.comunicadoAddVideo ?? "Vídeo"}
            hint={H.insertVideo}
            onClick={() => addBlock("video")}
          />
          <div ref={shapeAnchorRef} className="td-composer__dropdown">
            <DeckRibbonTile
              icon={Shapes}
              label={labels.comunicadoAddShape ?? "Forma"}
              hint={H.insertShape}
              active={shapeMenuOpen}
              onClick={() => setShapeMenuOpen(!shapeMenuOpen)}
            />
            {shapeMenuOpen ? (
              <ShapeDropdownMenu
                anchorRef={shapeAnchorRef}
                onSelect={(kind) => {
                  addShape(kind);
                  setShapeMenuOpen(false);
                }}
              />
            ) : null}
          </div>
        </div>
      </DeckRibbonGroup>
      <DataRoutePickerModal
        open={dataPickerOpen}
        onClose={() => setDataPickerOpen(false)}
        onSelect={(block) => addDataBlock(block)}
      />
    </div>
  );
}
