import {
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardUnderlineNav,
  createDashboardStatusBadge,
  createDashboardSectionCard,
  createDashboardDetailFieldGrid,
  createDashboardFormFieldShell,
  detailFieldGridBemClasses,
  formFieldShellBemClasses,
  sectionCardPacBemClasses,
} from "@delpi/plugin-ui/index";

/** Wrappers presentation-only do kit (`ds` prefix) — espelha o padrão Commercial. */
export const TmPagePath = createDashboardPagePath({
  prefix: "ds",
  portalScopeClassName: "dashboard-transformometro",
});

export const TmPageHero = createDashboardPageHero({ prefix: "ds" });

export const TmUnderlineNav = createDashboardUnderlineNav({ prefix: "ds" });

export const TmStatusBadge = createDashboardStatusBadge({ prefix: "ds" });

export const TmSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses("ds"),
  labels: {
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
});

export const TmDetailFieldGrid = createDashboardDetailFieldGrid({
  classNames: detailFieldGridBemClasses("ds"),
  labels: {
    fieldHelpAriaLabel: (label: string) => `Ajuda: ${label}`,
  },
});

export const TmFormFieldShell = createDashboardFormFieldShell({
  classNames: formFieldShellBemClasses("ds"),
});
