import type { ReactNode } from "react";

import { ConfirmModalPanel, confirmModalTransformometroClasses } from "@delpi/plugin-ui/index";

import { Modal } from "./Modal";

export type ConfirmModalProps = {
  open: boolean;
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  secondaryLabel?: string;
  confirmBusy?: boolean;
  variant?: "default" | "danger";
  onConfirm: () => void;
  onCancel: () => void;
  onSecondary?: () => void;
};

export function ConfirmModal({
  open,
  title = "Confirmar",
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  secondaryLabel,
  confirmBusy = false,
  variant = "default",
  onConfirm,
  onCancel,
  onSecondary,
}: ConfirmModalProps) {
  return (
    <Modal open={open} title={title} onClose={onCancel} className="ds-modal--confirm">
      <ConfirmModalPanel
        message={message}
        confirmLabel={confirmLabel}
        cancelLabel={cancelLabel}
        secondaryLabel={secondaryLabel}
        confirmBusy={confirmBusy}
        variant={variant}
        onConfirm={onConfirm}
        onCancel={onCancel}
        onSecondary={onSecondary}
        classNames={confirmModalTransformometroClasses()}
      />
    </Modal>
  );
}
