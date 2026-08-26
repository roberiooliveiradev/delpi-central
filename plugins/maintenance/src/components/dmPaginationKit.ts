import {
  createDashboardPaginationKit,
  TABLE_PAGE_SIZE_OPTIONS,
  type PageJumpValidationReason,
} from "@delpi/plugin-ui/index";

const paginationKit = createDashboardPaginationKit({
  prefix: "dm",
  hints: {
    pageSize: "Quantidade de linhas solicitadas por página na API.",
    previous: "Volta para a página anterior.",
    next: "Avança para a próxima página.",
    info: "Página atual e total de páginas.",
    jump: "Digite o número da página e pressione Enter.",
  },
  tablePageSizeLabels: {
    label: "Por página",
    selectAriaLabel: "Registros por página",
  },
  labels: {
    navigationAriaLabel: "Paginação da tabela",
    pagesAriaLabel: "Páginas",
    previous: "Anterior",
    next: "Próxima",
    info: ({ page, totalPages, total }) =>
      totalPages > 0 ? `Página ${page} de ${totalPages} (${total} registro(s))` : "Sem registros",
    jumpLabel: "Ir para",
    jumpInputAriaLabel: "Número da página",
    jumpError: (reason: PageJumpValidationReason, totalPages: number) => {
      if (reason === "empty") return "Informe um número de página.";
      if (reason === "invalid") return "Página inválida.";
      return `Informe um número entre 1 e ${totalPages}.`;
    },
  },
});

export const DmTablePagination = paginationKit.Pagination;
export const DmTablePageSizeSelect = paginationKit.TablePageSizeSelect;
export { TABLE_PAGE_SIZE_OPTIONS };
