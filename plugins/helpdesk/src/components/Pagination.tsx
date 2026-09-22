import {
  createDashboardPaginationKit,
  type PageJumpValidationReason,
} from "@delpi/plugin-ui/index";

import { helpTooltips } from "../content/helpTooltips";

const P = helpTooltips.pagination;

/** Tamanhos aceitos pela lista (BFF has_more; sem 100). */
export const HELPDESK_PAGE_SIZE_OPTIONS = [10, 20, 50] as const;

const kit = createDashboardPaginationKit({
  prefix: "helpdesk",
  hints: {
    pageSize: P.pageSize,
    previous: P.previous,
    next: P.next,
    info: P.info,
    jump: P.jump,
  },
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

/** Paginação completa do kit (setas + páginas + Ir para + helps) — mesmo padrão do dashboard-commercial. */
export const HelpdeskPagination = kit.Pagination;
export const HelpdeskTablePageSizeSelect = kit.TablePageSizeSelect;
