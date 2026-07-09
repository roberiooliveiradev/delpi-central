import type { Processo } from "../../data/api/transformometroApi";
import { computeProcessoListCompletion } from "../../utils/processoCompletion";

export type ProcessoListSortField = "nome" | "codigo" | "status" | "preenchimento";
export type ProcessoListSortDirection = "asc" | "desc";

export type ProcessoListSort = {
  key: ProcessoListSortField;
  direction: ProcessoListSortDirection;
};

export const PROCESSO_LIST_SORT_STORAGE_KEY = "transformometro.processos.sort";

export const DEFAULT_PROCESSO_LIST_SORT: ProcessoListSort = {
  key: "nome",
  direction: "asc",
};

export const PROCESSO_LIST_SORT_OPTIONS: Array<{ value: ProcessoListSortField; label: string }> = [
  { value: "nome", label: "Título do processo" },
  { value: "codigo", label: "Código" },
  { value: "status", label: "Status" },
  { value: "preenchimento", label: "Preenchimento" },
];

const SORT_FIELDS = new Set<string>(PROCESSO_LIST_SORT_OPTIONS.map((option) => option.value));

export function isProcessoListSortField(value: string | null): value is ProcessoListSortField {
  return value != null && SORT_FIELDS.has(value);
}

export function readProcessoListSort(): ProcessoListSort {
  const storage = globalThis.localStorage;
  if (!storage) return DEFAULT_PROCESSO_LIST_SORT;
  try {
    const raw = storage.getItem(PROCESSO_LIST_SORT_STORAGE_KEY);
    if (!raw) return DEFAULT_PROCESSO_LIST_SORT;
    const parsed = JSON.parse(raw) as Partial<ProcessoListSort>;
    const key: ProcessoListSortField = isProcessoListSortField(parsed.key ?? null)
      ? parsed.key!
      : DEFAULT_PROCESSO_LIST_SORT.key;
    const direction = parsed.direction === "desc" ? "desc" : "asc";
    return { key, direction };
  } catch {
    return DEFAULT_PROCESSO_LIST_SORT;
  }
}

export function writeProcessoListSort(sort: ProcessoListSort): void {
  const storage = globalThis.localStorage;
  if (!storage) return;
  storage.setItem(PROCESSO_LIST_SORT_STORAGE_KEY, JSON.stringify(sort));
}

export function sortProcessoListItems(items: Processo[], sort: ProcessoListSort): Processo[] {
  const copy = [...items];
  const factor = sort.direction === "asc" ? 1 : -1;

  copy.sort((left, right) => {
    if (sort.key === "preenchimento") {
      return (
        (computeProcessoListCompletion(left).percent - computeProcessoListCompletion(right).percent) * factor
      );
    }

    let leftValue = "";
    let rightValue = "";
    if (sort.key === "codigo") {
      leftValue = left.codigo_processo ?? "";
      rightValue = right.codigo_processo ?? "";
    } else if (sort.key === "status") {
      leftValue = left.status_processo ?? "";
      rightValue = right.status_processo ?? "";
    } else {
      leftValue = left.nome_processo ?? "";
      rightValue = right.nome_processo ?? "";
    }

    return leftValue.localeCompare(rightValue, "pt-BR", { sensitivity: "base" }) * factor;
  });

  return copy;
}
