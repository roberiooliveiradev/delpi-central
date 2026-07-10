import { createInfoStatePanel } from "@delpi/plugin-ui/index";

import "./InfoState.css";

export const InfoState = createInfoStatePanel({
  prefix: "si",
  renderIcon: () => "i",
});

export type { DashboardInfoStatePanelProps as InfoStateProps } from "@delpi/plugin-ui/index";
