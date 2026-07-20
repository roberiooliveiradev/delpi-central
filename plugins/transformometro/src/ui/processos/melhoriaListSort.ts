import type { ProcessoInstancia } from "../../data/api/transformometroApi";
import { labelMelhoriaPrioridade } from "../../constants/melhoriaForm";
import {
  formatInstanciaSetoresDisplay,
  formatInstanciaUnidadeDisplay,
} from "./processoEscopo";

export type MelhoriaListSortField = "titulo" | "unidade" | "fase" | "prioridade" | "status";

export type MelhoriaListSort = {
  key: MelhoriaListSortField;
  direction: "asc" | "desc";
};

export const MELHORIA_LIST_SORT_STORAGE_KEY = "transformometro.melhorias.sort";

export const MELHORIA_LIST_SORT_OPTIONS: Array<{ value: MelhoriaListSortField; label: string }> = [
  { value: "titulo", label: "Título" },
  { value: "unidade", label: "Unidade" },
  { value: "fase", label: "Fase" },
  { value: "prioridade", label: "Prioridade" },
  { value: "status", label: "Status" },
];

const DEFAULT_SORT: MelhoriaListSort = { key: "titulo", direction: "asc" };

export function readMelhoriaListSort(): MelhoriaListSort {
  if (typeof window === "undefined") return DEFAULT_SORT;
  try {
    const raw = window.localStorage.getItem(MELHORIA_LIST_SORT_STORAGE_KEY);
    if (!raw) return DEFAULT_SORT;
    const parsed = JSON.parse(raw) as Partial<MelhoriaListSort>;
    if (!MELHORIA_LIST_SORT_OPTIONS.some((option) => option.value === parsed.key)) {
      return DEFAULT_SORT;
    }
    return {
      key: parsed.key as MelhoriaListSortField,
      direction: parsed.direction === "desc" ? "desc" : "asc",
    };
  } catch {
    return DEFAULT_SORT;
  }
}

export function writeMelhoriaListSort(sort: MelhoriaListSort): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(MELHORIA_LIST_SORT_STORAGE_KEY, JSON.stringify(sort));
}

export function melhoriaFolderTitle(
  row: ProcessoInstancia,
  activeFilialCount: number
): string {
  const rotulo = String(row.rotulo_instancia ?? "").trim();
  if (rotulo) return rotulo;
  return formatInstanciaUnidadeDisplay(row, activeFilialCount) || "Melhoria";
}

export function melhoriaFolderMeta(
  row: ProcessoInstancia,
  activeFilialCount: number
): string {
  const parts = [
    formatInstanciaUnidadeDisplay(row, activeFilialCount),
    formatInstanciaSetoresDisplay(row),
    row.fase_melhoria,
    labelMelhoriaPrioridade(row.prioridade),
  ].filter((part) => part && part !== "—");
  return parts.join(" · ");
}

function compareText(a: string, b: string): number {
  return a.localeCompare(b, "pt-BR", { sensitivity: "base" });
}

export function sortMelhoriaListItems(
  items: ProcessoInstancia[],
  sort: MelhoriaListSort,
  activeFilialCount: number
): ProcessoInstancia[] {
  const factor = sort.direction === "asc" ? 1 : -1;
  return [...items].sort((left, right) => {
    let cmp = 0;
    switch (sort.key) {
      case "unidade":
        cmp = compareText(
          formatInstanciaUnidadeDisplay(left, activeFilialCount),
          formatInstanciaUnidadeDisplay(right, activeFilialCount)
        );
        break;
      case "fase":
        cmp = compareText(String(left.fase_melhoria ?? ""), String(right.fase_melhoria ?? ""));
        break;
      case "prioridade":
        cmp = compareText(
          labelMelhoriaPrioridade(left.prioridade),
          labelMelhoriaPrioridade(right.prioridade)
        );
        break;
      case "status":
        cmp = compareText(
          String(left.status_instancia ?? "ativo"),
          String(right.status_instancia ?? "ativo")
        );
        break;
      case "titulo":
      default:
        cmp = compareText(
          melhoriaFolderTitle(left, activeFilialCount),
          melhoriaFolderTitle(right, activeFilialCount)
        );
        break;
    }
    return cmp * factor;
  });
}
