import { createTablePaginationNav } from "@delpi/plugin-ui/index";

export const Pagination = createTablePaginationNav({
  prefix: "dm",
  labels: {
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação da tabela",
    infoBeforeCurrent: "Página ",
    infoAfterCurrent: (totalPages) => ` de ${totalPages}`,
  },
});
