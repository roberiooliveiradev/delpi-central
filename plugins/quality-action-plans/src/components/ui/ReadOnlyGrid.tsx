import { createDashboardFormGrid, formGridPacClasses } from "@delpi/plugin-ui";

/** Mesma grade do modo edição (`pac-form-grid`) para manter ordem e colunas alinhadas. */
export const ReadOnlyGrid = createDashboardFormGrid({
  classNames: formGridPacClasses("pac"),
});

export const FormGrid = ReadOnlyGrid;
