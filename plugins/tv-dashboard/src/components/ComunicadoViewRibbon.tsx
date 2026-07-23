import { Focus, Maximize2, ZoomIn, ZoomOut } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DECK_VIEW_ACTION_KEYTIPS } from "../utils/deckKeyTips";
import { clampStageZoom, STAGE_ZOOM_MAX, STAGE_ZOOM_MIN } from "../utils/stageViewport";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonGroups } from "./deck/DeckRibbonGroups";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { ShortcutTip } from "./ShortcutTip";
import { useComunicadoEditor } from "./comunicadoEditorContext";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const V = TV_DASHBOARD_HELP_TOOLTIPS.view;
const K = DECK_VIEW_ACTION_KEYTIPS;

/**
 * Aba Exibir — zoom do palco.
 * Controles «Mostrar» (réguas, grade, guias…) ficam na barra inferior.
 */
export function ComunicadoViewRibbon() {
  const { stageZoom, setStageZoom, fitStageToView } = useComunicadoEditor();

  return (
    <DeckRibbonGroups>
      <DeckRibbonGroup
        groupId="view-zoom"
        label="Zoom"
        hint={V.zoom}
        order={0}
        collapseIcon={Maximize2}
      >
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <ShortcutTip shortcutId="zoom-wheel" placement="bottom">
            <span className="td-shortcut-tip__cluster">
              <DeckRibbonTile
                icon={ZoomOut}
                label="−"
                hint={H.zoomOut}
                disabled={stageZoom <= STAGE_ZOOM_MIN}
                keyTip={K.zoomOut}
                onClick={() => setStageZoom(clampStageZoom(stageZoom - 0.1))}
              />
              <span className="td-deck-ribbon__zoom-label">{Math.round(stageZoom * 100)}%</span>
              <DeckRibbonTile
                icon={ZoomIn}
                label="+"
                hint={H.zoomIn}
                disabled={stageZoom >= STAGE_ZOOM_MAX}
                keyTip={K.zoomIn}
                onClick={() => setStageZoom(clampStageZoom(stageZoom + 0.1))}
              />
            </span>
          </ShortcutTip>
          <DeckRibbonTile
            icon={Maximize2}
            label="Ajustar"
            hint={H.zoomFit}
            keyTip={K.zoomFit}
            onClick={() => fitStageToView()}
          />
          <DeckRibbonTile
            icon={Focus}
            label="100%"
            hint={H.zoomReset}
            active={stageZoom === 1}
            keyTip={K.zoom100}
            onClick={() => setStageZoom(1)}
          />
        </div>
      </DeckRibbonGroup>
    </DeckRibbonGroups>
  );
}
