import { copy } from "../content/copy";
import type { Pagination } from "../types";

type FinPaginationProps = {
  pagination: Pagination;
  onPageChange: (page: number) => void;
};

export function FinPagination({ pagination, onPageChange }: FinPaginationProps) {
  const rangeStart =
    pagination.totalItems === 0 ? 0 : (pagination.page - 1) * pagination.pageSize + 1;
  const rangeEnd = Math.min(pagination.page * pagination.pageSize, pagination.totalItems);
  return (
    <nav className="fin-pagination" aria-label={copy.pagination.navigationAriaLabel}>
      <p>
        {copy.pagination.info({
          rangeStart,
          rangeEnd,
          total: pagination.totalItems,
          page: pagination.page,
          totalPages: pagination.totalPages,
        })}
      </p>
      <div className="fin-pagination__actions">
        <button
          type="button"
          className="fin-link-btn"
          disabled={!pagination.hasPrevious}
          onClick={() => onPageChange(pagination.page - 1)}
        >
          {copy.pagination.previous}
        </button>
        <button
          type="button"
          className="fin-link-btn"
          disabled={!pagination.hasNext}
          onClick={() => onPageChange(pagination.page + 1)}
        >
          {copy.pagination.next}
        </button>
      </div>
    </nav>
  );
}
