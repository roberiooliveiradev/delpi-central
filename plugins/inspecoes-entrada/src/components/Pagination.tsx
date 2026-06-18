type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  pageSizeOptions: readonly number[];
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
};

export function Pagination({
  page,
  pageSize,
  total,
  totalPages,
  pageSizeOptions,
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const canPrev = page > 1;
  const canNext = page < totalPages;

  if (total === 0) return null;

  return (
    <div className="ie-pagination">
      <div className="ie-pagination__left">
        <span className="ie-pagination__info">
          Página {page} de {totalPages} · {total.toLocaleString("pt-BR")} registro(s)
        </span>
        <label className="ie-pagination__size">
          <span>Itens por página</span>
          <select
            value={pageSize}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
          >
            {pageSizeOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="ie-pagination__actions">
        <button
          type="button"
          className="ie-btn ie-btn--ghost"
          disabled={!canPrev}
          onClick={() => onPageChange(page - 1)}
        >
          Anterior
        </button>
        <button
          type="button"
          className="ie-btn ie-btn--ghost"
          disabled={!canNext}
          onClick={() => onPageChange(page + 1)}
        >
          Próxima
        </button>
      </div>
    </div>
  );
}
