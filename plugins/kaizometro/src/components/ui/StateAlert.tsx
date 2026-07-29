import { createDashboardStateBanner, stateBannerKaizenClasses } from "@delpi/plugin-ui/index";

export const StateAlert = createDashboardStateBanner({
  classNames: stateBannerKaizenClasses("kz"),
});
