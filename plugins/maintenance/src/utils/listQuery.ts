export type ListQueryParams = {
  page?: number;
  pageSize?: number;
  sortKey?: string | null;
  sortDirection?: "asc" | "desc";
};

/** Limite máximo aceito pela maintenance-api (`list_query_params.page_size`). */
export const MAX_LIST_PAGE_SIZE = 200;

export type ListQueryFilters = Record<
  string,
  string | number | boolean | string[] | number[] | null | undefined
>;

function appendFilterValue(search: URLSearchParams, key: string, value: string | number | boolean) {
  if (value === "") return;
  search.append(key, String(value));
}

export function appendListQuery(
  search: URLSearchParams,
  query: ListQueryParams,
  filters: ListQueryFilters = {},
) {
  if (query.page) search.set("page", String(query.page));
  if (query.pageSize) search.set("page_size", String(query.pageSize));
  if (query.sortKey) search.set("sort_by", query.sortKey);
  if (query.sortDirection) search.set("sort_dir", query.sortDirection);

  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      for (const item of value) {
        if (item === "" || item === null || item === undefined) continue;
        appendFilterValue(search, key, item);
      }
      continue;
    }
    if (value === "") continue;
    search.set(key, String(value));
  }
}
