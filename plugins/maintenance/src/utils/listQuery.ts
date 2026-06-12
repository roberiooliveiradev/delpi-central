export type ListQueryParams = {
  page?: number;
  pageSize?: number;
  sortKey?: string | null;
  sortDirection?: "asc" | "desc";
};

export type ListQueryFilters = Record<string, string | number | boolean | null | undefined>;

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
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
}
