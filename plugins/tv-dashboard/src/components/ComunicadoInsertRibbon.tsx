import { useEffect, useRef, useState } from "react";
import { BarChart3, Heading, Image as ImageIcon, Shapes, Sparkles, Text, Video } from "lucide-react";
import type { ComunicadoShapeKind } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { rememberComunicadoShape } from "../utils/comunicadoRecentShapes";
import { DataRoutePickerModal } from "./DataRoutePickerModal";
import { ComunicadoIconLibraryMenu } from "./ComunicadoIconLibraryMenu";
import { ComunicadoShapeLibraryMenu } from "./ComunicadoShapeLibraryMenu";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

export function ComunicadoInsertRibbon({ labels = {} }: { labels?: Labels }) {
  const {
    shapeMenuOpen,
    setShapeMenuOpen,
    addBlock,
    addShape,
    addIconBlock,
    addDataBlock,
    openMediaLibrary,
  } = useComunicadoEditor();
  const shapeAnchorRef = useRef<HTMLDivElement>(null);
  const iconAnchorRef = useRef<HTMLDivElement>(null);
  const [dataPickerOpen, setDataPickerOpen] = useState(false);
  const [iconMenuOpen, setIconMenuOpen] = useState(false);

  useEffect(() => {
    if (!shapeMenuOpen && !iconMenuOpen) return undefined;

    function handlePointerDown(event: MouseEvent) {
      const target = event.target as Node;
      if (shapeAnchorRef.current?.contains(target) || iconAnchorRef.current?.contains(target)) return;
      if ((target as HTMLElement).closest?.(".td-shape-library--portal")) return;
      setShapeMenuOpen(false);
      setIconMenuOpen(false);
    }

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [iconMenuOpen, setShapeMenuOpen, shapeMenuOpen]);

  function insertShape(kind: ComunicadoShapeKind) {
    addShape(kind);
    rememberComunicadoShape(kind);
    setShapeMenuOpen(false);
  }

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Texto" hint={H.insertTextGroup ?? H.insert}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
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
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Mídia" hint={H.insertMediaGroup ?? H.insert}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={ImageIcon}
            label={labels.comunicadoAddImage ?? "Imagem"}
            hint={H.insertImage}
            onClick={() => openMediaLibrary("insert-image")}
          />
          <DeckRibbonTile
            icon={Video}
            label={labels.comunicadoAddVideo ?? "Vídeo"}
            hint={H.insertVideo}
            onClick={() => openMediaLibrary("insert-video")}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Ilustrações" hint={H.insertIllustrationsGroup ?? H.insertShape}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <div ref={shapeAnchorRef} className="td-composer__dropdown">
            <DeckRibbonTile
              icon={Shapes}
              label={labels.comunicadoAddShape ?? "Formas"}
              hint={H.insertShape}
              active={shapeMenuOpen}
              onClick={() => {
                setIconMenuOpen(false);
                setShapeMenuOpen(!shapeMenuOpen);
              }}
            />
            {shapeMenuOpen ? (
              <ComunicadoShapeLibraryMenu anchorRef={shapeAnchorRef} onSelect={insertShape} />
            ) : null}
          </div>
          <div ref={iconAnchorRef} className="td-composer__dropdown">
            <DeckRibbonTile
              icon={Sparkles}
              label={labels.comunicadoAddIcon ?? "Ícones"}
              hint={H.insertIcon}
              active={iconMenuOpen}
              onClick={() => {
                setShapeMenuOpen(false);
                setIconMenuOpen((open) => !open);
              }}
            />
            {iconMenuOpen ? (
              <ComunicadoIconLibraryMenu
                anchorRef={iconAnchorRef}
                onSelect={(name) => {
                  addIconBlock(name);
                  setIconMenuOpen(false);
                }}
              />
            ) : null}
          </div>
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Dados" hint={H.insertDataGroup ?? H.insertIndicator}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={BarChart3}
            label={labels.comunicadoAddIndicator ?? "Indicador"}
            hint={H.insertIndicator ?? H.insert}
            onClick={() => setDataPickerOpen(true)}
          />
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
