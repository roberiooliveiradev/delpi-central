import {
  createDashboardPageHero,
  createDashboardUnderlineNav,
} from "@delpi/plugin-ui/index";

/** PageHero temático SI — admin e dashboards internos. */
export const SiPageHero = createDashboardPageHero({ prefix: "si" });

/** UnderlineNav temático SI — abas admin e sub-nav catálogo. */
export const SiUnderlineNav = createDashboardUnderlineNav({ prefix: "si" });
