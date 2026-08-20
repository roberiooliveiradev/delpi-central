import {
  ConfirmModalPanel,
  confirmModalBemClasses,
  createHostContainedModalShell,
} from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";

const PPC_ROOT_CLASS = "dashboard-production-control";

export const HostContainedDialog = createHostContainedModalShell({
  prefix: "ppc",
  portalScopeClassName: PPC_ROOT_CLASS,
  containedLayout: "dialog",
});

const confirmClasses = confirmModalBemClasses("ppc", {
  actionsBlock: "form-actions",
  actionsAlign: "end",
});

export type PpcConfirmModalProps = {
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

export function PpcConfirmModal({
  open,
  title = "Confirmar",
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  confirmBusy = false,
  variant = "default",
  onConfirm,
  onCancel,
}: PpcConfirmModalProps) {
  return (
    <HostContainedDialog open={open} title={title} onClose={onCancel}>
      <ConfirmModalPanel
        message={message}
        confirmLabel={confirmLabel}
        cancelLabel={cancelLabel}
        confirmBusy={confirmBusy}
        variant={variant}
        onConfirm={onConfirm}
        onCancel={onCancel}
        classNames={confirmClasses}
      />
    </HostContainedDialog>
  );
}
