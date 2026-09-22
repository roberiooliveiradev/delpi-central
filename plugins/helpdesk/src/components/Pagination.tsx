import {
  createDashboardPaginationKit,
  HintAction,
  type PageJumpValidationReason,
} from "@delpi/plugin-ui/index";

import { helpTooltips } from "../content/helpTooltips";

const P = helpTooltips.pagination;

/** Tamanhos aceitos pela lista (BFF has_more; sem 100). */
export const HELPDESK_PAGE_SIZE_OPTIONS = [10, 20, 50] as const;

const kit = createDashboardPaginationKit({
  prefix: "helpdesk",
  tablePageSizeLabels: {
    label: "Por página",
    selectAriaLabel: "Quantidade de chamados por página",
  },
  labels: {
    navigationAriaLabel: "Paginação da lista de chamados",
    pagesAriaLabel: "Páginas",
    previous: "Anterior",
    next: "Próxima",
    info: ({ rangeStart, rangeEnd, total, page, totalPages }) =>
      `Exibindo ${rangeStart}–${rangeEnd} de ${total} · Página ${page} de ${totalPages}`,
    jumpLabel: "Ir para",
    jumpInputAriaLabel: "Ir para página",
    jumpError: (reason: PageJumpValidationReason, totalPages: number) => {
      switch (reason) {
        case "empty":
          return P.jumpEmpty;
        case "invalid":
          return P.jumpInvalid;
        case "below_min":
          return P.jumpBelowMin;
        case "above_max":
          return `A página máxima é ${totalPages}.`;
        default:
          return "";
      }
    },
  },
});

export const HelpdeskPagination = kit.Pagination;
export const HelpdeskTablePageSizeSelect = kit.TablePageSizeSelect;

export type HelpdeskListPaginationFooterProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
};

/** Rodapé da lista: Por página + paginação do kit, ajuda via HintAction (sem ícones ?). */
export function HelpdeskListPaginationFooter({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}: HelpdeskListPaginationFooterProps) {
  return (
    <div className="helpdesk-list-pagination">
      <HintAction hint={helpTooltips.listUi.pageSize} ariaLabel="Ajuda: Por página">
        <div className="helpdesk-list-pagination__page-size" role="group" aria-label="Por página">
          <HelpdeskTablePageSizeSelect
            pageSize={pageSize}
            pageSizeOptions={[...HELPDESK_PAGE_SIZE_OPTIONS]}
            onPageSizeChange={onPageSizeChange}
          />
        </div>
      </HintAction>
      <HintAction hint={P.nav} ariaLabel="Ajuda: Paginação">
        <div className="helpdesk-list-pagination__nav">
          <HelpdeskPagination
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={onPageChange}
          />
        </div>
      </HintAction>
    </div>
  );
}
