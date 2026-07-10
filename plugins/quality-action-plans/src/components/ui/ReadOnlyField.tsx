import {
  createDashboardReadOnlyField,
  readOnlyFieldPacBemClasses,
} from "@delpi/plugin-ui/index";

const LABELS = {
  emptyDisplay: "—",
  fieldHelpAriaLabel: (label: string) => `Ajuda: ${label}`,
};

export const ReadOnlyField = createDashboardReadOnlyField({
  classNames: readOnlyFieldPacBemClasses("pac"),
  labels: LABELS,
  labelMode: "fieldLabel",
  defaultAppearance: "ficha",
});
