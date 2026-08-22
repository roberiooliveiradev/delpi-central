import { createHostContainedModalShell } from "@delpi/plugin-ui/index";

const FINANCIAL_ROOT_CLASS = "dashboard-financial";

/** Modais ficam contidos no host — não cobrem a sidebar do portal. */
export const FinDialog = createHostContainedModalShell({
  prefix: "fin",
  portalScopeClassName: FINANCIAL_ROOT_CLASS,
  containedLayout: "dialog",
});

export const FinWideDialog = createHostContainedModalShell({
  prefix: "fin",
  portalScopeClassName: FINANCIAL_ROOT_CLASS,
  containedLayout: "dialog",
  variant: "wide",
});
