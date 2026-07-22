import type { ReactNode } from "react";
import { ConfirmModalPanel, confirmModalBemClasses } from "@delpi/plugin-ui/index";

import { HostContainedDialog } from "./Modal";

export type ConfirmModalProps = {
  open: boolean;
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmBusy?: boolean;
  variant?: "default" | "danger";
  showCancel?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function confirmModalTvClasses() {
  return confirmModalBemClasses("td", { actionsBlock: "modal-actions", actionsAlign: "end" });
}

export function ConfirmModal({
  open,
  title = "Confirmar",
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  confirmBusy = false,
  variant = "default",
  showCancel = true,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  const shellClass = [
    "td-modal--confirm",
    variant === "danger" ? "td-modal--confirm-danger" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <HostContainedDialog open={open} title={title} onClose={onCancel} className={shellClass}>
      <ConfirmModalPanel
        message={message}
        confirmLabel={confirmLabel}
        cancelLabel={cancelLabel}
        confirmBusy={confirmBusy}
        variant={variant}
        showCancel={showCancel}
        onConfirm={onConfirm}
        onCancel={onCancel}
        classNames={confirmModalTvClasses()}
      />
    </HostContainedDialog>
  );
}
