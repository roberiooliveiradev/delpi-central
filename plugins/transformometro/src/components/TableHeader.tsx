import {
  createDashboardTableHeaderContent,
  tableHeaderContentTransformometroClasses,
} from "@delpi/plugin-ui";

/** Cabeçalho de coluna em tabelas HTML nativas (fora do DataTable). */
export const TableHeader = createDashboardTableHeaderContent({
  classNames: tableHeaderContentTransformometroClasses("ds"),
  labels: {
    hintAriaLabel: (label) => `Ajuda: ${label}`,
  },
  hintPresentation: "icon",
});
