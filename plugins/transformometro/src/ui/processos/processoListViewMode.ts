export type ProcessoListViewMode = "icons-lg" | "icons-md" | "list" | "details";

export type ProcessoListFieldVisibility = {
  showCode: boolean;
  showMeta: boolean;
  showStatus: boolean;
  showProgress: boolean;
};

export const PROCESSO_LIST_VIEW_STORAGE_KEY = "transformometro.processos.viewMode";

export const PROCESSO_LIST_VIEW_MODES: Array<{
  id: ProcessoListViewMode;
  label: string;
  shortLabel: string;
  pageSize: number;
}> = [
  { id: "icons-lg", label: "Ícones grandes", shortLabel: "Grandes", pageSize: 24 },
  { id: "icons-md", label: "Ícones médios", shortLabel: "Médios", pageSize: 40 },
  { id: "list", label: "Lista", shortLabel: "Lista", pageSize: 20 },
  { id: "details", label: "Detalhes", shortLabel: "Detalhes", pageSize: 15 },
];

export function isProcessoListViewMode(value: string | null): value is ProcessoListViewMode {
  return PROCESSO_LIST_VIEW_MODES.some((mode) => mode.id === value);
}

export function readProcessoListViewMode(): ProcessoListViewMode {
  if (typeof window === "undefined") return "icons-lg";
  const stored = window.localStorage.getItem(PROCESSO_LIST_VIEW_STORAGE_KEY);
  return isProcessoListViewMode(stored) ? stored : "icons-lg";
}

export function writeProcessoListViewMode(mode: ProcessoListViewMode): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(PROCESSO_LIST_VIEW_STORAGE_KEY, mode);
}

export function pageSizeForProcessoListView(mode: ProcessoListViewMode): number {
  return PROCESSO_LIST_VIEW_MODES.find((item) => item.id === mode)?.pageSize ?? 24;
}

export function fieldVisibilityForProcessoListView(mode: ProcessoListViewMode): ProcessoListFieldVisibility {
  switch (mode) {
    case "icons-lg":
      return { showCode: false, showMeta: false, showStatus: false, showProgress: false };
    case "icons-md":
      return { showCode: true, showMeta: true, showStatus: false, showProgress: false };
    case "list":
      return { showCode: true, showMeta: true, showStatus: true, showProgress: true };
    default:
      return { showCode: true, showMeta: true, showStatus: true, showProgress: true };
  }
}
