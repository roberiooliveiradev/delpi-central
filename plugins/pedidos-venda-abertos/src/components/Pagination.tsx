import { createCompactPagination } from "@delpi/plugin-ui";

export const Pagination = createCompactPagination({
  prefix: "pva",
  layout: "flat",
  labels: {
    info: ({ page, totalPages, total }) =>
      `Página ${page} de ${totalPages} · ${total.toLocaleString("pt-BR")} registro(s)`,
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação de pedidos",
  },
});
