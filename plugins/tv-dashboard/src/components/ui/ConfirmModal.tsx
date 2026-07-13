import type { ReactNode } from "react";
import { ConfirmModalPanel, confirmModalBemClasses } from "@delpi/plugin-ui/index";

import { Modal } from "./Modal";

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
  return (
    <Modal open={open} title={title} onClose={onCancel} className="td-modal--confirm">
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
    </Modal>
  );
}
