import { createDashboardTableHeaderCell, tableHeaderCellPacClasses } from "@delpi/plugin-ui/index";

export const TableHeaderCell = createDashboardTableHeaderCell({
  classNames: tableHeaderCellPacClasses("pac"),
  labels: {
    hintAriaLabel: (label) => `Ajuda: ${label}`,
  },
});
