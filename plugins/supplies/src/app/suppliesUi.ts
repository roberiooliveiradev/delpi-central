import {
  createDashboardCommandPalette,
  createDashboardEmptyState,
  createDashboardPagePath,
  createDashboardStateBanner,
  createDashboardTopBar,
  createDashboardViewTransition,
  emptyStateCardBemClasses,
  stateBannerBemClasses,
} from "@delpi/plugin-ui/index";

export const UI_PREFIX = "sp";
export const SP_PORTAL_SCOPE = "dashboard-supplies-portal";

const spEmptyStateClassNames = emptyStateCardBemClasses(UI_PREFIX);
const spStateBannerClassNames = stateBannerBemClasses(UI_PREFIX);

export const SuppliesTopBar = createDashboardTopBar({ prefix: UI_PREFIX });
export const SuppliesCommandPalette = createDashboardCommandPalette({
  prefix: UI_PREFIX,
  portalScopeClassName: SP_PORTAL_SCOPE,
});
export const SuppliesPagePath = createDashboardPagePath({
  prefix: UI_PREFIX,
  portalScopeClassName: SP_PORTAL_SCOPE,
});
export const SuppliesEmptyState = createDashboardEmptyState({
  classNames: {
    ...spEmptyStateClassNames,
    withTitle: true,
  },
  defaultMessage: "",
});
export const SuppliesStateBanner = createDashboardStateBanner({
  classNames: spStateBannerClassNames,
});
export const SuppliesViewTransition = createDashboardViewTransition({ prefix: UI_PREFIX });
