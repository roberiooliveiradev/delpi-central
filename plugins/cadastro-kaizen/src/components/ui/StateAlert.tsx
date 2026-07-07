import { createDashboardStateBanner, stateBannerKaizenClasses } from "@delpi/plugin-ui";

export const StateAlert = createDashboardStateBanner({
  classNames: stateBannerKaizenClasses("kz"),
});
