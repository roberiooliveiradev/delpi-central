import { GHOST_BTN } from "../ui/ghostChrome";
import { createCompactPagination } from "@delpi/plugin-ui/index";

import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";

export const Pagination = createCompactPagination({
  prefix: "lmps",
  layout: "flat",
  withHints: true,
  ghostBtn: GHOST_BTN,
  labels: {
    info: ({ page, totalPages, total }) =>
      `Página ${page} de ${totalPages} · ${total} registro(s)`,
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação",
  },
  hints: LMPS_HELP_TOOLTIPS.pagination,
});
