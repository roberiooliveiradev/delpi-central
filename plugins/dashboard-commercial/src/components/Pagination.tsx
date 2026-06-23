import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { HelpTooltip } from "./HelpTooltip";

type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: PaginationProps) {
  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1;
  const canPrev = page > 1;
  const canNext = page < totalPages;

  if (total === 0) return null;

  return (
    <div className="dc-pagination">
      <span className="dc-pagination__info">
        Página {page} de {totalPages} · {total} registro(s)
        <HelpTooltip
          content={COMMERCIAL_HELP_TOOLTIPS.pagination.info}
          ariaLabel="Ajuda: paginação"
          className="dc-pagination__help"
        />
      </span>
      <div className="dc-pagination__actions">
        <div className="dc-pagination__action">
          <button
            type="button"
            className="dc-ghost-btn"
            disabled={!canPrev}
            onClick={() => onPageChange(page - 1)}
          >
            Anterior
          </button>
          <HelpTooltip
            content={COMMERCIAL_HELP_TOOLTIPS.pagination.previous}
            ariaLabel="Ajuda: página anterior"
            className="dc-pagination__action-help"
          />
        </div>
        <div className="dc-pagination__action">
          <button
            type="button"
            className="dc-ghost-btn"
            disabled={!canNext}
            onClick={() => onPageChange(page + 1)}
          >
            Próxima
          </button>
          <HelpTooltip
            content={COMMERCIAL_HELP_TOOLTIPS.pagination.next}
            ariaLabel="Ajuda: próxima página"
            className="dc-pagination__action-help"
          />
        </div>
      </div>
    </div>
  );
}
