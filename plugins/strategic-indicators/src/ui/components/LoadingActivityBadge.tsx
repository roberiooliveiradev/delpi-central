import {
  createDashboardLoadingActivityBadge,
  type LoadingActivityBadgeProps,
} from "@delpi/plugin-ui/index";

/** Chip compacto de status (sidebar / header) — kit `@delpi/plugin-ui`. */
export const LoadingActivityBadge = createDashboardLoadingActivityBadge({
  prefix: "si",
  defaultTone: "neutral",
});

export type { LoadingActivityBadgeProps };
