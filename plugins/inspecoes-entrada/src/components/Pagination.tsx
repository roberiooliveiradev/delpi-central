import { createCompactPagination } from "@delpi/plugin-ui/index";

export const Pagination = createCompactPagination({
  prefix: "ie",
  labels: {
    info: ({ page, totalPages, total }) =>
      `Página ${page} de ${totalPages} · ${total.toLocaleString("pt-BR")} registro(s)`,
    pageSizeLabel: "Itens por página",
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação do histórico",
  },
});
