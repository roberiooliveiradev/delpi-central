import { createDashboardTableHeaderCell, tableHeaderCellPacClasses } from "@delpi/plugin-ui";

export const TableHeaderCell = createDashboardTableHeaderCell({
  classNames: tableHeaderCellPacClasses("pac"),
  labels: {
    hintAriaLabel: (label) => `Ajuda: ${label}`,
  },
});
