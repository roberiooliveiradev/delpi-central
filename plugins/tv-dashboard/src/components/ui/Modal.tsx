import { createModalShell } from "@delpi/plugin-ui/index";
import type { ComponentProps } from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";

export const Modal = createModalShell({
  prefix: "td",
  portalScopeClassName: TV_DASHBOARD_ROOT_CLASS,
});

type ModalProps = ComponentProps<typeof Modal>;

/** Modal que ocupa somente a área do MFE, preservando sidebar/chrome do host Minha DELPI. */
export function HostContainedModal(props: ModalProps) {
  const portalTarget =
    typeof document !== "undefined"
      ? document.querySelector<HTMLElement>(`.${TV_DASHBOARD_ROOT_CLASS}`)
      : null;
  return (
    <Modal
      {...props}
      portalTarget={portalTarget}
      containedInPortalTarget={Boolean(portalTarget)}
    />
  );
}
