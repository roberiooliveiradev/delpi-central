import { createCompactPagination } from "@delpi/plugin-ui/index";

export const Pagination = createCompactPagination({
  prefix: "fi",
  layout: "flat",
  ghostBtn: "fi-btn fi-btn--secondary",
  labels: {
    info: ({ page, totalPages }) => `Página ${page} de ${totalPages}`,
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação",
  },
});
