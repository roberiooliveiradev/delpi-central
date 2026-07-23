import { ComboboxNumberControl, HintAction } from "@delpi/plugin-ui/index";
import {
  AlignHorizontalSpaceAround,
  Crosshair,
  Grid3x3,
  Hand,
  Keyboard,
  Magnet,
  Ruler,
} from "lucide-react";
import { useMemo, type ReactNode } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useKeyboardShortcutsTips } from "../context/KeyboardShortcutsTipsProvider";
import {
  STAGE_GRID_SIZE_MAX_PERCENT,
  STAGE_GRID_SIZE_MIN_PERCENT,
  clampStageGridSizePercent,
  stageGridSizePercentPresets,
} from "../utils/stageGridSize";
import { ShortcutTip } from "./ShortcutTip";
import { useComunicadoEditor } from "./comunicadoEditorContext";

const V = TV_DASHBOARD_HELP_TOOLTIPS.view;

type ToggleProps = {
  label: string;
  hint: string;
  active?: boolean;
  pressed?: boolean;
  onClick: () => void;
  children: ReactNode;
};

function StatusToggle({ label, hint, active = false, pressed, onClick, children }: ToggleProps) {
  return (
    <button
      type="button"
      className={[
        "td-stage-statusbar__toggle",
        active ? "td-stage-statusbar__toggle--active" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      title={hint}
      aria-label={label}
      aria-pressed={pressed}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

/**
 * Controles «Mostrar» + Pan na barra inferior do palco
 * (réguas, grade, guias, encaixe, atalhos).
 */
export function StageStatusShowToggles() {
  const {
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
    stagePanMode,
    setStagePanMode,
  } = useComunicadoEditor();
  const { openCatalog } = useKeyboardShortcutsTips();
  const gridPresets = useMemo(() => stageGridSizePercentPresets(), []);
  const gridSizeValue = clampStageGridSizePercent(stageGridSizePercent);
  const panActive = Boolean(stagePanMode);

  return (
    <div className="td-stage-statusbar__toggles" role="group" aria-label="Mostrar">
      <StatusToggle
        label="Réguas"
        hint={V.rulers}
        active={showStageRulers}
        pressed={showStageRulers}
        onClick={() => setShowStageRulers(!showStageRulers)}
      >
        <Ruler size={14} aria-hidden="true" />
      </StatusToggle>
      <StatusToggle
        label="Grade"
        hint={V.grid}
        active={showStageGrid}
        pressed={showStageGrid}
        onClick={() => setShowStageGrid(!showStageGrid)}
      >
        <Grid3x3 size={14} aria-hidden="true" />
      </StatusToggle>
      <div className="td-stage-statusbar__grid-size" role="group" aria-label="Tamanho da grade">
        <HintAction hint={V.gridSize} ariaLabel="Ajuda: Tamanho da grade">
          <ComboboxNumberControl
            className="td-stage-statusbar__grid-size-combobox"
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
      <StatusToggle
        label="Guias"
        hint={V.guides}
        active={showStageGuides}
        pressed={showStageGuides}
        onClick={() => setShowStageGuides(!showStageGuides)}
      >
        <Crosshair size={14} aria-hidden="true" />
      </StatusToggle>
      <StatusToggle
        label="Na grade"
        hint={V.snapToGrid}
        active={snapToGrid}
        pressed={snapToGrid}
        onClick={() => setSnapToGrid(!snapToGrid)}
      >
        <Magnet size={14} aria-hidden="true" />
      </StatusToggle>
      <StatusToggle
        label="Objetos"
        hint={V.snapToObjects}
        active={snapToObjects}
        pressed={snapToObjects}
        onClick={() => setSnapToObjects(!snapToObjects)}
      >
        <AlignHorizontalSpaceAround size={14} aria-hidden="true" />
      </StatusToggle>
      <StatusToggle
        label="Atalhos"
        hint="Catálogo de atalhos. Alt revela balões (Ctrl e F1–F8 nas abas)."
        onClick={openCatalog}
      >
        <Keyboard size={14} aria-hidden="true" />
      </StatusToggle>
      <ShortcutTip shortcutId="pan">
        <StatusToggle
          label="Pan"
          hint={V.pan}
          active={panActive}
          pressed={panActive}
          onClick={() => setStagePanMode(!stagePanMode)}
        >
          <Hand size={14} aria-hidden="true" />
        </StatusToggle>
      </ShortcutTip>
    </div>
  );
}
