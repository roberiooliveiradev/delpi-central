/** Labels e opções de filtro das listas Minhas / Fila (E10–E11). */

export const REQUEST_LIST_PAGE_SIZE = 20;

/** Debounce da busca textual antes de chamar a API (ms). */
export const REQUEST_LIST_SEARCH_DEBOUNCE_MS = 300;

export const REQUEST_STATUS_FILTER_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "submitted", label: "Enviada" },
  { value: "in_progress", label: "Em andamento" },
  { value: "needs_information", label: "Aguardando informação" },
  { value: "completed", label: "Concluída" },
  { value: "cancelled", label: "Cancelada" },
  { value: "rejected", label: "Rejeitada" },
] as const;

export type RequestListFiltersState = {
  q: string;
  typeCode: string;
  status: string;
  branch: string;
  page: number;
};
