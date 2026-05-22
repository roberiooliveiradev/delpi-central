type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  /** Oculta controles quando há uma única página (padrão: true). */
  hideWhenSinglePage?: boolean;
};

export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
  hideWhenSinglePage = true,
}: PaginationProps) {
  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1;
  const canPrev = page > 1;
  const canNext = page < totalPages;

  if (total === 0) return null;
  if (hideWhenSinglePage && totalPages <= 1) return null;

  const rangeStart = (page - 1) * pageSize + 1;
  const rangeEnd = Math.min(page * pageSize, total);

  return (
    <div className="ds-pagination" role="navigation" aria-label="Paginação da tabela">
      <span className="ds-pagination__info">
        Exibindo {rangeStart}–{rangeEnd} de {total} · Página {page} de {totalPages}
      </span>
      <div className="ds-pagination__actions">
        <button
          type="button"
          className="ds-ghost-btn"
          disabled={!canPrev}
          onClick={() => onPageChange(page - 1)}
        >
          Anterior
        </button>
        <button
          type="button"
          className="ds-ghost-btn"
          disabled={!canNext}
          onClick={() => onPageChange(page + 1)}
        >
          Próxima
        </button>
      </div>
    </div>
  );
}
