import { createHostContainedModalShell } from "@delpi/plugin-ui/index";

const TM_ROOT_CLASS = "dashboard-transformometro";

/**
 * Aviso / confirm — overlay só na área do MFE (não cobre `#portal-sidebar`).
 * Canônico: `mfe-modal-host-contained.mdc` + `createHostContainedModalShell`.
 */
export const HostContainedDialog = createHostContainedModalShell({
  prefix: "ds",
  portalScopeClassName: TM_ROOT_CLASS,
  containedLayout: "dialog",
});

/** Formulários densos (ex.: criar tarefa a partir da mensagem). */
export const HostContainedWideDialog = createHostContainedModalShell({
  prefix: "ds",
  portalScopeClassName: TM_ROOT_CLASS,
  containedLayout: "dialog",
  variant: "wide",
});

/** Alias estável — sempre host-contained. */
export const Modal = HostContainedDialog;

/** Alias estável para jornadas wide. */
export const WideModal = HostContainedWideDialog;
