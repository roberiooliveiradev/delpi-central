type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  hideWhenSinglePage?: boolean;
};

export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
  hideWhenSinglePage = false,
}: PaginationProps) {
  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1;
  const canPrev = page > 1;
  const canNext = page < totalPages;

  if (total === 0) return null;
  if (hideWhenSinglePage && totalPages <= 1) return null;

  return (
    <div className="dm-pagination" role="navigation" aria-label="Paginação da tabela">
      <button
        type="button"
        className="dm-ghost-btn dm-pagination__nav"
        disabled={!canPrev}
        onClick={() => onPageChange(page - 1)}
      >
        Anterior
      </button>

      <p className="dm-pagination__info">
        Página <span className="dm-pagination__current">{page}</span> de {totalPages}
      </p>

      <button
        type="button"
        className="dm-ghost-btn dm-pagination__nav"
        disabled={!canNext}
        onClick={() => onPageChange(page + 1)}
      >
        Próxima
      </button>
    </div>
  );
}
