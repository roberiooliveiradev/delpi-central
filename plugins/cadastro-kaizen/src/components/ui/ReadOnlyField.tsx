import {
  createDashboardReadOnlyField,
  readOnlyFieldKaizenBemClasses,
} from "@delpi/plugin-ui/index";

const LABELS = {
  emptyDisplay: "—",
  fieldHelpAriaLabel: (label: string) => `Ajuda: ${label}`,
};

export const ReadOnlyField = createDashboardReadOnlyField({
  classNames: readOnlyFieldKaizenBemClasses("kz"),
  labels: LABELS,
  labelMode: "helpTooltip",
});
