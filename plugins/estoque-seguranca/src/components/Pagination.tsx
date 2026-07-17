import {
  createDashboardPaginationKit,
  TABLE_PAGE_SIZE_OPTIONS,
  type PageJumpValidationReason,
} from "@delpi/plugin-ui/index";

const kit = createDashboardPaginationKit({
  prefix: "ess",
  labels: {
    navigationAriaLabel: "Paginação da tabela de estoque de segurança",
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
          return "Informe uma página.";
        case "invalid":
          return "Página inválida.";
        case "below_min":
          return "A página mínima é 1.";
        case "above_max":
          return `A página máxima é ${totalPages}.`;
        default:
          return "";
      }
    },
  },
  tablePageSizeLabels: {
    label: "Itens por página",
    selectAriaLabel: "Quantidade de itens por página",
  },
});

export const Pagination = kit.Pagination;
export const TablePageSizeSelect = kit.TablePageSizeSelect;
export { TABLE_PAGE_SIZE_OPTIONS };
