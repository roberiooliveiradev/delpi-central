import {
  createHostContainedModalShell,
  confirmModalBemClasses,
  createDashboardFormActions,
  createDashboardNativeFormFields,
  createDashboardSectionCard,
  createDashboardStatusBadge,
  formActionsBemClasses,
  formFieldShellBemClasses,
  sectionCardKaizenBemClasses,
} from "@delpi/plugin-ui/index";

export const LMPS_ROOT_CLASS = "dashboard-lmps";

export const HostContainedDialog = createHostContainedModalShell({
  prefix: "lmps",
  portalScopeClassName: LMPS_ROOT_CLASS,
  containedLayout: "dialog",
});

export const HostContainedFill = createHostContainedModalShell({
  prefix: "lmps",
  portalScopeClassName: LMPS_ROOT_CLASS,
  containedLayout: "fill",
});

export const SectionCard = createDashboardSectionCard({
  classNames: sectionCardKaizenBemClasses("lmps"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const FormActions = createDashboardFormActions({
  classNames: formActionsBemClasses("lmps"),
});

export const { FormFieldShell, TextField, SelectField, TextAreaField } =
  createDashboardNativeFormFields({
    classNames: formFieldShellBemClasses("lmps"),
  });

export const StatusBadge = createDashboardStatusBadge({
  prefix: "lmps",
});

export const LMPS_CONFIRM_CLASSES = confirmModalBemClasses("lmps");
