import {
  createDashboardReadOnlyField,
  readOnlyFieldKaizenBemClasses,
} from "@delpi/plugin-ui";

const LABELS = {
  emptyDisplay: "—",
  fieldHelpAriaLabel: (label: string) => `Ajuda: ${label}`,
};

export const ReadOnlyField = createDashboardReadOnlyField({
  classNames: readOnlyFieldKaizenBemClasses("kz"),
  labels: LABELS,
  labelMode: "helpTooltip",
});
