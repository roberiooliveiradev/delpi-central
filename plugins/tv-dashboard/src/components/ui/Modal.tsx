import {
  createHostContainedModalShell,
  createModalShell,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";

export const Modal = createModalShell({
  prefix: "td",
  portalScopeClassName: TV_DASHBOARD_ROOT_CLASS,
});

/** Modal que ocupa somente a área do MFE, preservando sidebar/chrome do host Minha DELPI. */
export const HostContainedModal = createHostContainedModalShell({
  prefix: "td",
  portalScopeClassName: TV_DASHBOARD_ROOT_CLASS,
});
