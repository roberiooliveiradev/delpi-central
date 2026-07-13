type PaginationProps = {
  page: number;
  pageSize: number;
  pageSizeOptions: readonly number[];
  hasNext: boolean;
  loading: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  ariaLabel?: string;
};

export function Pagination({
  page,
  pageSize,
  pageSizeOptions,
  hasNext,
  loading,
  onPageChange,
  onPageSizeChange,
  ariaLabel = "Paginação do histórico",
}: PaginationProps) {
  return (
    <div className="ip-pagination" aria-label={ariaLabel}>
      <p className="ip-pagination__info">
        Página {page}
        {hasNext ? " · há próxima página" : " · última página"}
      </p>

      <label className="ip-field ip-pagination__size">
        <span className="ip-field__label">Itens por página</span>
        <select
          className="ip-input"
          value={pageSize}
          disabled={loading}
          onChange={(event) => onPageSizeChange(Number(event.target.value))}
        >
          {pageSizeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <div className="ip-pagination__nav">
        <button
          type="button"
          className="ip-button"
          disabled={loading || page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Anterior
        </button>
        <button
          type="button"
          className="ip-button"
          disabled={loading || !hasNext}
          onClick={() => onPageChange(page + 1)}
        >
          Próxima
        </button>
      </div>
    </div>
  );
}
