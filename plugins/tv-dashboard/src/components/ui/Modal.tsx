import {
  createHostContainedModalShell,
  createModalShell,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";

export const Modal = createModalShell({
  prefix: "td",
  portalScopeClassName: TV_DASHBOARD_ROOT_CLASS,
});

/** Workbench / página — preenche a área do MFE (não cobre sidebar do portal). */
export const HostContainedModal = createHostContainedModalShell({
  prefix: "td",
  portalScopeClassName: TV_DASHBOARD_ROOT_CLASS,
  containedLayout: "fill",
});

/**
 * Aviso / confirm — overlay só na área do MFE, card centralizado.
 * Anti-padrão: `Modal` (body + fixed inset:0) sobre a sidebar do portal.
 */
export const HostContainedDialog = createHostContainedModalShell({
  prefix: "td",
  portalScopeClassName: TV_DASHBOARD_ROOT_CLASS,
  containedLayout: "dialog",
});
