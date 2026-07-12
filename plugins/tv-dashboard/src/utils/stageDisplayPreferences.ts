import { clampStageZoom } from "./stageViewport";

const STORAGE_KEY = "td-stage-display-preferences";

export type StageDisplayPreferences = {
  stageZoom: number;
  showStageRulers: boolean;
  showStageGrid: boolean;
  showStageGuides: boolean;
  snapEnabled: boolean;
};

export const DEFAULT_STAGE_DISPLAY_PREFERENCES: StageDisplayPreferences = {
  stageZoom: 1,
  showStageRulers: true,
  showStageGrid: false,
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
