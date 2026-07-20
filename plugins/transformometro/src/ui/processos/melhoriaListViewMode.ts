import {
  fieldVisibilityForProcessoListView,
  isProcessoListViewMode,
  pageSizeForProcessoListView,
  PROCESSO_LIST_VIEW_MODES,
  type ProcessoListFieldVisibility,
  type ProcessoListViewMode,
} from "./processoListViewMode";

export type MelhoriaListViewMode = ProcessoListViewMode;
export type MelhoriaListFieldVisibility = ProcessoListFieldVisibility;

export const MELHORIA_LIST_VIEW_STORAGE_KEY = "transformometro.melhorias.viewMode";

export const MELHORIA_LIST_VIEW_MODES = PROCESSO_LIST_VIEW_MODES;

export function readMelhoriaListViewMode(): MelhoriaListViewMode {
  if (typeof window === "undefined") return "icons-lg";
  const stored = window.localStorage.getItem(MELHORIA_LIST_VIEW_STORAGE_KEY);
  return isProcessoListViewMode(stored) ? stored : "icons-lg";
}

export function writeMelhoriaListViewMode(mode: MelhoriaListViewMode): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(MELHORIA_LIST_VIEW_STORAGE_KEY, mode);
}

export const pageSizeForMelhoriaListView = pageSizeForProcessoListView;
export const fieldVisibilityForMelhoriaListView = fieldVisibilityForProcessoListView;
