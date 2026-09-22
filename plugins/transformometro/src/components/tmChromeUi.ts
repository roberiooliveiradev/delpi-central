import {
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardUnderlineNav,
  createDashboardStatusBadge,
} from "@delpi/plugin-ui/index";

/** Wrappers presentation-only do kit (`ds` prefix) — espelha o padrão Commercial. */
export const TmPagePath = createDashboardPagePath({
  prefix: "ds",
  portalScopeClassName: "dashboard-transformometro",
});

export const TmPageHero = createDashboardPageHero({ prefix: "ds" });

export const TmUnderlineNav = createDashboardUnderlineNav({ prefix: "ds" });

export const TmStatusBadge = createDashboardStatusBadge({ prefix: "ds" });
