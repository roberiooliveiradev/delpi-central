import { createModalShell } from "@delpi/plugin-ui/index";

export const Modal = createModalShell({
  prefix: "ds",
  overlayClassName: "dashboard-transformometro",
});

/** Formulários com grid de campos (ex.: criar tarefa a partir da mensagem). */
export const WideModal = createModalShell({
  prefix: "ds",
  overlayClassName: "dashboard-transformometro",
  variant: "wide",
});
