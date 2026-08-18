import type { ReactNode } from "react";

import {
  ConfirmModalPanel,
  confirmModalBemClasses,
  createHostContainedModalShell,
} from "@delpi/plugin-ui/index";

const SI_HOST_CLASS = "si-settings-page";
const SI_PREFIX = "si";

const SiHostDialog = createHostContainedModalShell({
  prefix: SI_PREFIX,
  portalScopeClassName: SI_HOST_CLASS,
  containedLayout: "dialog",
});

const siConfirmModalClassNames = confirmModalBemClasses(SI_PREFIX);

export type SiConfirmModalProps = {
  open: boolean;
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmBusy?: boolean;
  variant?: "default" | "danger";
  onConfirm: () => void;
  onCancel: () => void;
};

/** Confirmação host-contained (não cobre a sidebar do portal). */
export function SiConfirmModal({
  open,
  title = "Confirmar",
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  confirmBusy = false,
  variant = "default",
  onConfirm,
  onCancel,
}: SiConfirmModalProps) {
  return (
    <SiHostDialog
      open={open}
      title={title}
      onClose={onCancel}
      className="si-modal--confirm"
    >
      <ConfirmModalPanel
        message={message}
        confirmLabel={confirmLabel}
        cancelLabel={cancelLabel}
        confirmBusy={confirmBusy}
        variant={variant}
        onConfirm={onConfirm}
        onCancel={onCancel}
        classNames={siConfirmModalClassNames}
      />
    </SiHostDialog>
  );
}
