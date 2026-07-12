import { createModalShell } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";

export const Modal = createModalShell({
  prefix: "td",
  portalScopeClassName: TV_DASHBOARD_ROOT_CLASS,
});
