type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1;
  const canPrev = page > 1;
  const canNext = page < totalPages;

  if (total === 0) return null;

  return (
    <div className="pva-pagination">
      <span className="pva-pagination__info">
        Página {page} de {totalPages} · {total.toLocaleString("pt-BR")} registro(s)
      </span>
      <div className="pva-pagination__actions">
        <button
          type="button"
          className="pva-btn pva-btn--ghost"
          disabled={!canPrev}
          onClick={() => onPageChange(page - 1)}
        >
          Anterior
        </button>
        <button
          type="button"
          className="pva-btn pva-btn--ghost"
          disabled={!canNext}
          onClick={() => onPageChange(page + 1)}
        >
          Próxima
        </button>
      </div>
    </div>
  );
}
