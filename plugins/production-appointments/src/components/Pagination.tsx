import {
  createDashboardPaginationKit,
  TABLE_PAGE_SIZE_OPTIONS,
  type PageJumpValidationReason,
} from "@delpi/plugin-ui/index";

const kit = createDashboardPaginationKit({
  prefix: "pa",
  hints: {
    pageSize: "Define quantos registros a tabela solicita por página.",
    previous: "Volta para a página anterior.",
    next: "Avança para a próxima página.",
    info: "Intervalo de registros exibidos nesta página.",
    jump: "Digite o número da página e pressione Enter.",
  },
  tablePageSizeLabels: {
    label: "Itens por página",
    selectAriaLabel: "Quantidade de itens por página",
  },
  labels: {
    navigationAriaLabel: "Paginação da tabela",
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
          return "Informe o número da página.";
        case "invalid":
          return "Número de página inválido.";
        case "below_min":
          return "A página mínima é 1.";
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
