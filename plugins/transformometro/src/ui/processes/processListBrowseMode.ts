export type ProcessoListBrowseMode = "processo" | "departamento";

export const PROCESSO_LIST_BROWSE_STORAGE_KEY = "transformometro.processos.browseMode";

export const PROCESSO_LIST_BROWSE_MODES: Array<{
  id: ProcessoListBrowseMode;
  label: string;
}> = [
  { id: "processo", label: "Processos" },
  { id: "departamento", label: "Departamentos" },
];

export function isProcessoListBrowseMode(value: string | null): value is ProcessoListBrowseMode {
  return value === "processo" || value === "departamento";
}

export function readProcessoListBrowseMode(): ProcessoListBrowseMode {
  if (typeof window === "undefined") return "processo";
  const stored = window.localStorage.getItem(PROCESSO_LIST_BROWSE_STORAGE_KEY);
  return isProcessoListBrowseMode(stored) ? stored : "processo";
}

export function writeProcessoListBrowseMode(mode: ProcessoListBrowseMode): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(PROCESSO_LIST_BROWSE_STORAGE_KEY, mode);
}
