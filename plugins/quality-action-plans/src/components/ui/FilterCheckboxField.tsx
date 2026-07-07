import {
  createDashboardFilterCheckboxField,
  filterCheckboxFieldPacClasses,
} from "@delpi/plugin-ui";

export const FilterCheckboxField = createDashboardFilterCheckboxField({
  classNames: filterCheckboxFieldPacClasses("pac"),
  labels: {
    defaultCheckboxLabel: "Ativar filtro",
  },
});
