import {
  createDashboardTableHeaderContent,
  tableHeaderContentTransformometroClasses,
} from "@delpi/plugin-ui/index";

/** Cabeçalho de coluna em tabelas HTML nativas (fora do DataTable). */
export const TableHeader = createDashboardTableHeaderContent({
  classNames: tableHeaderContentTransformometroClasses("ds"),
  labels: {
    hintAriaLabel: (label) => `Ajuda: ${label}`,
  },
  hintPresentation: "icon",
});
