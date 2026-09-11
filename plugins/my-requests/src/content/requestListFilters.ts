/** Labels e opções de filtro das listas Minhas / Fila (E10–E11). */

export { REQUEST_STATUS_FILTER_OPTIONS } from "./presentationLabels";

export const REQUEST_LIST_PAGE_SIZE = 20;

/** Debounce da busca textual antes de chamar a API (ms). */
export const REQUEST_LIST_SEARCH_DEBOUNCE_MS = 300;

export type RequestListFiltersState = {
  q: string;
  typeCode: string;
  status: string;
  branch: string;
  mineScope: "" | "completed_by_me" | "assigned_to_me";
  page: number;
};

export const WORK_QUEUE_MINE_SCOPE_OPTIONS: Array<{
  value: RequestListFiltersState["mineScope"];
  label: string;
}> = [
  { value: "", label: "Todas" },
  { value: "completed_by_me", label: "Concluídas por mim" },
  { value: "assigned_to_me", label: "Atribuídas a mim" },
];
