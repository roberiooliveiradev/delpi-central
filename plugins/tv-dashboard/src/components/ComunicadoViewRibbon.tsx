import {
  Focus,
  Grid3x3,
  Magnet,
  Maximize2,
  Ruler,
  ZoomIn,
  ZoomOut,
} from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { useComunicadoEditor } from "./comunicadoEditorContext";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const V = TV_DASHBOARD_HELP_TOOLTIPS.view;

export function ComunicadoViewRibbon() {
  const {
    stageZoom,
    setStageZoom,
    showStageGrid,
    setShowStageGrid,
    showStageGuides,
    setShowStageGuides,
    snapEnabled,
    setSnapEnabled,
  } = useComunicadoEditor();

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Zoom" hint={V.zoom}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={ZoomOut}
            label="−"
            hint={H.zoomOut}
            disabled={stageZoom <= 0.5}
            onClick={() => setStageZoom(Math.max(0.5, Math.round((stageZoom - 0.1) * 10) / 10))}
          />
          <span className="td-deck-ribbon__zoom-label">{Math.round(stageZoom * 100)}%</span>
          <DeckRibbonTile
            icon={ZoomIn}
            label="+"
            hint={H.zoomIn}
            disabled={stageZoom >= 2}
            onClick={() => setStageZoom(Math.min(2, Math.round((stageZoom + 0.1) * 10) / 10))}
          />
          <DeckRibbonTile
            icon={Maximize2}
            label="Ajustar"
            hint={H.zoomFit}
            onClick={() => setStageZoom(1)}
          />
          <DeckRibbonTile
            icon={Focus}
            label="100%"
            hint={H.zoomReset}
            active={stageZoom === 1}
            onClick={() => setStageZoom(1)}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Mostrar" hint={V.showGroup}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Grid3x3}
            label="Grade"
            hint={V.grid}
            active={showStageGrid}
            onClick={() => setShowStageGrid(!showStageGrid)}
          />
          <DeckRibbonTile
            icon={Ruler}
            label="Guias"
            hint={V.guides}
            active={showStageGuides}
            onClick={() => setShowStageGuides(!showStageGuides)}
          />
          <DeckRibbonTile
            icon={Magnet}
            label="Encaixe"
            hint={V.snap}
            active={snapEnabled}
            onClick={() => setSnapEnabled(!snapEnabled)}
          />
        </div>
      </DeckRibbonGroup>
    </div>
  );
}
