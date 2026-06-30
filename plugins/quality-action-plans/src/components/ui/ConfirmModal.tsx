import type { ReactNode } from "react";

import { FormActions } from "./FormActions";
import { Modal } from "./Modal";

export type ConfirmModalProps = {
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

export function ConfirmModal({
  open,
  title = "Confirmar",
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  confirmBusy = false,
  variant = "default",
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  return (
    <Modal open={open} title={title} onClose={onCancel} className="pac-modal--confirm">
      <p className="pac-confirm-modal__message">{message}</p>
      <FormActions align="end">
        <button
          type="button"
          className="pac-ghost-btn"
          disabled={confirmBusy}
          onClick={onCancel}
        >
          {cancelLabel}
        </button>
        <button
          type="button"
          className={variant === "danger" ? "pac-danger-btn" : "pac-primary-btn"}
          disabled={confirmBusy}
          onClick={onConfirm}
        >
          {confirmBusy ? "Aguarde…" : confirmLabel}
        </button>
      </FormActions>
    </Modal>
  );
}
