import "./AuditPagination.css";

type AuditPaginationProps = {
  page: number;
  pageCount: number;
  onPrevious: () => void;
  onNext: () => void;
};

export function AuditPagination({
  page,
  pageCount,
  onPrevious,
  onNext,
}: AuditPaginationProps) {
  return (
    <div className="mdc-audit-pagination">
      <span>
        Página {page + 1} de {pageCount}
      </span>

      <div>
        <button type="button" disabled={page === 0} onClick={onPrevious}>
          Anterior
        </button>
        <button type="button" disabled={page >= pageCount - 1} onClick={onNext}>
          Próxima
        </button>
      </div>
    </div>
  );
}
