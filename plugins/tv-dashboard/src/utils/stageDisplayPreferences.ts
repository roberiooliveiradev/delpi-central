import { clampStageZoom } from "./stageViewport";
import {
  STAGE_GRID_SIZE_DEFAULT_PX,
  clampStageGridSizePx,
} from "./stageGridSize";

const STORAGE_KEY = "td-stage-display-preferences";

/** Design de referência para clamp persistido (Full HD). O modal reclampa no viewport real. */
const PREFS_CLAMP_DESIGN = { width: 1920, height: 1080 };

export type StageDisplayPreferences = {
  stageZoom: number;
  showStageRulers: boolean;
  showStageGrid: boolean;
  /** Tamanho da célula da grade em px de design. */
  stageGridSizePx: number;
  showStageGuides: boolean;
  snapEnabled: boolean;
};

export const DEFAULT_STAGE_DISPLAY_PREFERENCES: StageDisplayPreferences = {
  stageZoom: 1,
  showStageRulers: true,
  showStageGrid: false,
  stageGridSizePx: STAGE_GRID_SIZE_DEFAULT_PX,
  showStageGuides: true,
  snapEnabled: true,
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

export function normalizeStageDisplayPreferences(
  raw: unknown,
): StageDisplayPreferences {
  if (!isRecord(raw)) return { ...DEFAULT_STAGE_DISPLAY_PREFERENCES };

  return {
    stageZoom:
      typeof raw.stageZoom === "number" && Number.isFinite(raw.stageZoom)
        ? clampStageZoom(raw.stageZoom)
        : DEFAULT_STAGE_DISPLAY_PREFERENCES.stageZoom,
    showStageRulers:
      typeof raw.showStageRulers === "boolean"
        ? raw.showStageRulers
        : DEFAULT_STAGE_DISPLAY_PREFERENCES.showStageRulers,
    showStageGrid:
      typeof raw.showStageGrid === "boolean"
        ? raw.showStageGrid
        : DEFAULT_STAGE_DISPLAY_PREFERENCES.showStageGrid,
    stageGridSizePx:
      typeof raw.stageGridSizePx === "number" && Number.isFinite(raw.stageGridSizePx)
        ? clampStageGridSizePx(raw.stageGridSizePx, PREFS_CLAMP_DESIGN)
        : DEFAULT_STAGE_DISPLAY_PREFERENCES.stageGridSizePx,
    showStageGuides:
      typeof raw.showStageGuides === "boolean"
        ? raw.showStageGuides
        : DEFAULT_STAGE_DISPLAY_PREFERENCES.showStageGuides,
    snapEnabled:
      typeof raw.snapEnabled === "boolean"
        ? raw.snapEnabled
        : DEFAULT_STAGE_DISPLAY_PREFERENCES.snapEnabled,
  };
}

/** Preferências de Exibir (zoom, réguas, grade, guias, encaixe) — sobrevivem ao refresh. */
export function readStageDisplayPreferences(): StageDisplayPreferences {
  if (typeof window === "undefined") return { ...DEFAULT_STAGE_DISPLAY_PREFERENCES };

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_STAGE_DISPLAY_PREFERENCES };
    return normalizeStageDisplayPreferences(JSON.parse(raw));
  } catch {
    return { ...DEFAULT_STAGE_DISPLAY_PREFERENCES };
  }
}

export function writeStageDisplayPreferences(prefs: StageDisplayPreferences): void {
  if (typeof window === "undefined") return;

  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(normalizeStageDisplayPreferences(prefs)),
    );
  } catch {
    // quota / private mode
  }
}
