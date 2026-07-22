import { HintAction, ComboboxNumberControl } from "@delpi/plugin-ui/index";
import {
  AlignHorizontalSpaceAround,
  Crosshair,
  Eye,
  Focus,
  Grid3x3,
  Keyboard,
  Magnet,
  Maximize2,
  Ruler,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { useMemo } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useKeyboardShortcutsTips } from "../context/KeyboardShortcutsTipsProvider";
import {
  STAGE_GRID_SIZE_MAX_PERCENT,
  STAGE_GRID_SIZE_MIN_PERCENT,
  clampStageGridSizePercent,
  stageGridSizePercentPresets,
} from "../utils/stageGridSize";
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

export function ComunicadoViewRibbon() {
  const {
    stageZoom,
    setStageZoom,
    fitStageToView,
    showStageRulers,
    setShowStageRulers,
    showStageGrid,
    setShowStageGrid,
    stageGridSizePercent,
    setStageGridSizePercent,
    showStageGuides,
    setShowStageGuides,
    snapToGrid,
    setSnapToGrid,
    snapToObjects,
    setSnapToObjects,
  } = useComunicadoEditor();
  const { openCatalog } = useKeyboardShortcutsTips();

  const gridPresets = useMemo(() => stageGridSizePercentPresets(), []);
  const gridSizeValue = clampStageGridSizePercent(stageGridSizePercent);

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

      <DeckRibbonGroup
        groupId="view-show"
        label="Mostrar"
        hint={V.showGroup}
        order={1}
        collapseIcon={Eye}
      >
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Ruler}
            label="Réguas"
            hint={V.rulers}
            active={showStageRulers}
            keyTip={K.rulers}
            onClick={() => setShowStageRulers(!showStageRulers)}
          />
          <DeckRibbonTile
            icon={Grid3x3}
            label="Grade"
            hint={V.grid}
            active={showStageGrid}
            keyTip={K.grid}
            onClick={() => setShowStageGrid(!showStageGrid)}
          />
          <div className="td-deck-ribbon__grid-size" role="group" aria-label="Tamanho da grade">
            <span className="td-deck-ribbon__grid-size-label">Tamanho %</span>
            <HintAction hint={V.gridSize} ariaLabel="Ajuda: Tamanho da grade">
              <ComboboxNumberControl
                className="td-deck-ribbon__grid-size-combobox"
                compact
                square
                aria-label="Tamanho da célula da grade em percentual do slide"
                value={gridSizeValue}
                options={gridPresets}
                min={STAGE_GRID_SIZE_MIN_PERCENT}
                max={STAGE_GRID_SIZE_MAX_PERCENT}
                clamp={clampStageGridSizePercent}
                portalScopeClassName="dashboard-tv-dashboard"
                onChange={(next) => {
                  setStageGridSizePercent(clampStageGridSizePercent(next));
                  if (!showStageGrid) setShowStageGrid(true);
                }}
              />
            </HintAction>
          </div>
          <DeckRibbonTile
            icon={Crosshair}
            label="Guias"
            hint={V.guides}
            active={showStageGuides}
            keyTip={K.guides}
            onClick={() => setShowStageGuides(!showStageGuides)}
          />
          <DeckRibbonTile
            icon={Magnet}
            label="Na grade"
            hint={V.snapToGrid}
            active={snapToGrid}
            keyTip={K.snapToGrid}
            onClick={() => setSnapToGrid(!snapToGrid)}
          />
          <DeckRibbonTile
            icon={AlignHorizontalSpaceAround}
            label="Objetos"
            hint={V.snapToObjects}
            active={snapToObjects}
            keyTip={K.snapToObjects}
            onClick={() => setSnapToObjects(!snapToObjects)}
          />
          <DeckRibbonTile
            icon={Keyboard}
            label="Atalhos"
            hint="Catálogo de atalhos. Alt revela balões (Ctrl e F1–F8 nas abas)."
            keyTip={K.shortcuts}
            onClick={openCatalog}
          />
        </div>
      </DeckRibbonGroup>
    </DeckRibbonGroups>
  );
}
