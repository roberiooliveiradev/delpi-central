import { createCompactPagination } from "@delpi/plugin-ui/index";

export const Pagination = createCompactPagination({
  prefix: "fcc",
  layout: "flat",
  ghostBtn: "fcc-btn fcc-btn--secondary",
  labels: {
    info: ({ page, totalPages }) => `Página ${page} de ${totalPages}`,
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação dos lançamentos",
  },
});
