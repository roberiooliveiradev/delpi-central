import { createDashboardStateBox } from "@delpi/plugin-ui/index";

/** Re-export canônico — chrome em `@delpi/plugin-ui` (`.delpi-ui-state-box*`). */
export const StateBox = createDashboardStateBox({ prefix: "dm" });
