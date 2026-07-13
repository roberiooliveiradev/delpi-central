import { HintAction, ComboboxNumberControl } from "@delpi/plugin-ui/index";
import {
  Crosshair,
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
import { resolveViewportPixelSize } from "../utils/viewportPixelSize";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useKeyboardShortcutsTips } from "../context/KeyboardShortcutsTipsProvider";
import {
  STAGE_GRID_SIZE_MIN_PX,
  clampStageGridSizePx,
  stageGridSizeMaxPx,
  stageGridSizePresetsForDesign,
} from "../utils/stageGridSize";
import { clampStageZoom, STAGE_ZOOM_MAX, STAGE_ZOOM_MIN } from "../utils/stageViewport";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { ShortcutTip } from "./ShortcutTip";
import { useComunicadoEditor } from "./comunicadoEditorContext";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const V = TV_DASHBOARD_HELP_TOOLTIPS.view;

export function ComunicadoViewRibbon() {
  const {
    stageZoom,
    setStageZoom,
    fitStageToView,
    showStageRulers,
    setShowStageRulers,
    showStageGrid,
    setShowStageGrid,
    stageGridSizePx,
    setStageGridSizePx,
    showStageGuides,
    setShowStageGuides,
    snapEnabled,
    setSnapEnabled,
    viewportProfile,
  } = useComunicadoEditor();
  const { openCatalog } = useKeyboardShortcutsTips();

  const design = useMemo(
    () => resolveViewportPixelSize(viewportProfile || "1080p"),
    [viewportProfile],
  );
  const gridPresets = useMemo(() => stageGridSizePresetsForDesign(design), [design]);
  const gridSizeMax = stageGridSizeMaxPx(design);
  const gridSizeValue = clampStageGridSizePx(stageGridSizePx, design);

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Zoom" hint={V.zoom}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <ShortcutTip shortcutId="zoom-wheel" placement="bottom">
            <span className="td-shortcut-tip__cluster">
              <DeckRibbonTile
                icon={ZoomOut}
                label="−"
                hint={H.zoomOut}
                disabled={stageZoom <= STAGE_ZOOM_MIN}
                onClick={() => setStageZoom(clampStageZoom(stageZoom - 0.1))}
              />
              <span className="td-deck-ribbon__zoom-label">{Math.round(stageZoom * 100)}%</span>
              <DeckRibbonTile
                icon={ZoomIn}
                label="+"
                hint={H.zoomIn}
                disabled={stageZoom >= STAGE_ZOOM_MAX}
                onClick={() => setStageZoom(clampStageZoom(stageZoom + 0.1))}
              />
            </span>
          </ShortcutTip>
          <DeckRibbonTile
            icon={Maximize2}
            label="Ajustar"
            hint={H.zoomFit}
            onClick={() => fitStageToView()}
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
            icon={Ruler}
            label="Réguas"
            hint={V.rulers}
            active={showStageRulers}
            onClick={() => setShowStageRulers(!showStageRulers)}
          />
          <DeckRibbonTile
            icon={Grid3x3}
            label="Grade"
            hint={V.grid}
            active={showStageGrid}
            onClick={() => setShowStageGrid(!showStageGrid)}
          />
          <div className="td-deck-ribbon__grid-size" role="group" aria-label="Tamanho da grade">
            <span className="td-deck-ribbon__grid-size-label">Tamanho</span>
            <HintAction hint={V.gridSize} ariaLabel="Ajuda: Tamanho da grade">
              <ComboboxNumberControl
                className="td-deck-ribbon__grid-size-combobox"
                compact
                square
                aria-label="Tamanho da célula da grade"
                value={gridSizeValue}
                options={gridPresets}
                min={STAGE_GRID_SIZE_MIN_PX}
                max={gridSizeMax}
                clamp={(raw) => clampStageGridSizePx(raw, design)}
                portalScopeClassName="dashboard-tv-dashboard"
                onChange={(next) => {
                  setStageGridSizePx(clampStageGridSizePx(next, design));
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
            onClick={() => setShowStageGuides(!showStageGuides)}
          />
          <DeckRibbonTile
            icon={Magnet}
            label="Encaixe"
            hint={V.snap}
            active={snapEnabled}
            onClick={() => setSnapEnabled(!snapEnabled)}
          />
          <DeckRibbonTile
            icon={Keyboard}
            label="Atalhos"
            hint="Catálogo de atalhos do teclado. Segure Alt no editor para ver balões nas ações."
            onClick={openCatalog}
          />
        </div>
      </DeckRibbonGroup>
    </div>
  );
}
