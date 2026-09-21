/** Bounds for kit CompactPagination when the BFF only exposes has_more (no total). */
export function helpdeskListPaginationBounds(input: {
  page: number;
  pageSize: number;
  itemCount: number;
  hasMore: boolean;
}): { total: number; totalPages: number } {
  const page = Math.max(1, input.page);
  const pageSize = Math.max(1, input.pageSize);
  const totalPages = input.hasMore ? page + 1 : page;
  const total = Math.max(
    page > 1 || input.itemCount > 0 || input.hasMore ? 1 : 0,
    (page - 1) * pageSize + input.itemCount + (input.hasMore ? 1 : 0),
  );
  return { total, totalPages };
}
