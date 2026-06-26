import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  TABLE_PAGE_SIZE_OPTIONS,
  buildVisiblePageItems,
} from "../utils/paginationPages";
import { HelpTooltip } from "./HelpTooltip";
import { PaginationPageJump } from "./PaginationPageJump";

type TablePageSizeSelectProps = {
  pageSize: number;
  pageSizeOptions?: readonly number[];
  onPageSizeChange: (pageSize: number) => void;
};

export function TablePageSizeSelect({
  pageSize,
  pageSizeOptions = TABLE_PAGE_SIZE_OPTIONS,
  onPageSizeChange,
}: TablePageSizeSelectProps) {
  return (
    <label className="ds-table-page-size">
      <span className="ds-table-page-size__label">Itens por página</span>
      <select
        className="ds-table-page-size__select"
        value={pageSize}
        onChange={(event) => onPageSizeChange(Number(event.target.value))}
        aria-label="Quantidade de itens por página"
      >
        {pageSizeOptions.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
      <HelpTooltip
        content={SUPPLIES_HELP_TOOLTIPS.pagination.pageSize}
        ariaLabel="Ajuda: itens por página"
        className="ds-table-page-size__help"
      />
    </label>
  );
}

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
  const pageItems = buildVisiblePageItems(page, totalPages);
  const rangeStart = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const rangeEnd = Math.min(page * pageSize, total);

  if (total === 0) return null;

  return (
    <div className="ds-pagination" role="navigation" aria-label="Paginação da tabela">
      <div className="ds-pagination__controls">
        <div className="ds-pagination__action">
          <button
            type="button"
            className="ds-ghost-btn"
            disabled={!canPrev}
            onClick={() => onPageChange(page - 1)}
            aria-disabled={!canPrev}
          >
            Anterior
          </button>
          <HelpTooltip
            content={SUPPLIES_HELP_TOOLTIPS.pagination.previous}
            ariaLabel="Ajuda: página anterior"
            className="ds-pagination__action-help"
          />
        </div>

        {totalPages > 1 ? (
          <div className="ds-pagination__pages" role="group" aria-label="Páginas">
            {pageItems.map((item, index) =>
              item === "ellipsis" ? (
                <span
                  key={`ellipsis-${index}`}
                  className="ds-pagination__ellipsis"
                  aria-hidden="true"
                >
                  …
                </span>
              ) : (
                <button
                  key={item}
                  type="button"
                  className={
                    item === page
                      ? "ds-pagination__page ds-pagination__page--active"
                      : "ds-pagination__page"
                  }
                  aria-current={item === page ? "page" : undefined}
                  onClick={() => onPageChange(item)}
                >
                  {item}
                </button>
              ),
            )}
          </div>
        ) : null}

        {totalPages > 1 ? (
          <PaginationPageJump
            page={page}
            totalPages={totalPages}
            onPageChange={onPageChange}
          />
        ) : null}

        <div className="ds-pagination__action">
          <button
            type="button"
            className="ds-ghost-btn"
            disabled={!canNext}
            onClick={() => onPageChange(page + 1)}
            aria-disabled={!canNext}
          >
            Próxima
          </button>
          <HelpTooltip
            content={SUPPLIES_HELP_TOOLTIPS.pagination.next}
            ariaLabel="Ajuda: próxima página"
            className="ds-pagination__action-help"
          />
        </div>
      </div>

      <span className="ds-pagination__info">
        Exibindo {rangeStart}–{rangeEnd} de {total} · Página {page} de {totalPages}
        <HelpTooltip
          content={SUPPLIES_HELP_TOOLTIPS.pagination.info}
          ariaLabel="Ajuda: paginação"
          className="ds-pagination__help"
        />
      </span>
    </div>
  );
}
