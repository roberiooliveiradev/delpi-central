import {
  createDashboardPaginationKit,
  TABLE_PAGE_SIZE_OPTIONS,
  type PageJumpValidationReason,
} from "@delpi/plugin-ui/index";

import { SCRAP_HELP_TOOLTIPS } from "../content/helpTooltips";

const P = SCRAP_HELP_TOOLTIPS.pagination;

const kit = createDashboardPaginationKit({
  prefix: "sm",
  hints: {
    pageSize: P.pageSize,
    previous: P.previous,
    next: P.next,
    info: P.info,
    jump: P.jump,
  },
  tablePageSizeLabels: {
    label: "Itens por página",
    selectAriaLabel: "Quantidade de itens por página",
  },
  labels: {
    navigationAriaLabel: "Paginação da tabela de refugos",
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

export const Pagination = kit.Pagination;
export const TablePageSizeSelect = kit.TablePageSizeSelect;
export { TABLE_PAGE_SIZE_OPTIONS };
