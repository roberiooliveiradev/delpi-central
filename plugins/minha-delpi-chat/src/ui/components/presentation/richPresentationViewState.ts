/** Estado de filtro/busca — preservado ao expandir (espelha ChartViewState). */

export type RichTableViewState = {
  searchQuery: string;
  categoryFilterKey: string | null;
  categoryFilterValue: string | null;
};

export type RichTreeViewState = {
  searchQuery: string;
};

export function createDefaultRichTableViewState(): RichTableViewState {
  return {
    searchQuery: "",
    categoryFilterKey: null,
    categoryFilterValue: null,
  };
}

export function createDefaultRichTreeViewState(): RichTreeViewState {
  return {
    searchQuery: "",
  };
}
