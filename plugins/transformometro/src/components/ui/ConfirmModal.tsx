import type { ReactNode } from "react";

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
    <Modal open={open} title={title} onClose={onCancel} className="ds-modal--confirm">
      <p className="ds-confirm-modal__message">{message}</p>
      <div className="ds-cadastro-form__actions ds-form-actions--end">
        <button type="button" className="ds-ghost-btn" disabled={confirmBusy} onClick={onCancel}>
          {cancelLabel}
        </button>
        <button
          type="button"
          className={variant === "danger" ? "ds-danger-btn" : "ds-primary-btn"}
          disabled={confirmBusy}
          onClick={onConfirm}
        >
          {confirmBusy ? "Aguarde…" : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
