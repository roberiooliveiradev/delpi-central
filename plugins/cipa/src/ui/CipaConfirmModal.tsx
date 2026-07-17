import type { ReactNode } from "react";
import {
  ConfirmModalPanel,
  ModalShell,
  type ConfirmModalClassNames,
  type ModalShellClassNames,
} from "@delpi/plugin-ui/index";

const MODAL_CLASSES: ModalShellClassNames = {
  overlay: "delpi-ui-modal-overlay",
  dialog: "delpi-ui-modal delpi-ui-modal--sm",
  header: "delpi-ui-modal__header",
  title: "delpi-ui-modal__title",
  closeButton: "delpi-ui-modal__close",
  body: "delpi-ui-modal__body",
  footer: "delpi-ui-modal__footer",
};

const CONFIRM_CLASSES: ConfirmModalClassNames = {
  message: "cipa-confirm-modal__message",
  actions: "cipa-form-actions cipa-form-actions--end",
  cancelButton: "delpi-ui-action-btn delpi-ui-action-btn--ghost",
  confirmButton: "delpi-ui-action-btn delpi-ui-action-btn--primary",
  confirmButtonDanger: "delpi-ui-action-btn cipa-action-btn--danger",
};

type Props = {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  busy?: boolean;
  variant?: "default" | "danger";
  onConfirm: () => void;
  onCancel: () => void;
};

export function CipaConfirmModal({
  open,
  title,
  message,
  confirmLabel = "Confirmar",
  busy = false,
  variant = "default",
  onConfirm,
  onCancel,
}: Props) {
  return (
    <ModalShell
      open={open}
      title={title}
      onClose={() => {
        if (!busy) onCancel();
      }}
      classNames={MODAL_CLASSES}
      portalScopeClassName="dashboard-cipa"
    >
      <ConfirmModalPanel
        message={message}
        confirmLabel={confirmLabel}
        cancelLabel="Cancelar"
        confirmBusy={busy}
        variant={variant}
        onConfirm={onConfirm}
        onCancel={onCancel}
        classNames={CONFIRM_CLASSES}
      />
    </ModalShell>
  );
}
