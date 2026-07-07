import { Heading, Image as ImageIcon, Shapes, Text, Video } from "lucide-react";
import { COMUNICADO_SHAPE_KINDS } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

export function ComunicadoInsertRibbon({ labels = {} }: { labels?: Labels }) {
  const { shapeMenuOpen, setShapeMenuOpen, addBlock, addShape } = useComunicadoEditor();

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Inserir" hint={H.insert}>
        <div className="td-deck-ribbon__tiles">
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
          <div className="td-composer__dropdown">
            <DeckRibbonTile
              icon={Shapes}
              label={labels.comunicadoAddShape ?? "Forma"}
              hint={H.insertShape}
              active={shapeMenuOpen}
              onClick={() => setShapeMenuOpen(!shapeMenuOpen)}
            />
            {shapeMenuOpen ? (
              <div className="td-composer__dropdown-menu" role="menu">
                {COMUNICADO_SHAPE_KINDS.map((item) => (
                  <button
                    key={item.kind}
                    type="button"
                    role="menuitem"
                    className="td-composer__dropdown-item"
                    onClick={() => addShape(item.kind)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </DeckRibbonGroup>
    </div>
  );
}
