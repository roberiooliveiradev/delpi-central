import type { ReactNode } from "react";

export type ConfirmModalClassNames = {
  message: string;
  actions: string;
  cancelButton: string;
  confirmButton: string;
  confirmButtonDanger: string;
};

export type ConfirmModalPanelProps = {
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmBusy?: boolean;
  confirmBusyLabel?: string;
  variant?: "default" | "danger";
  /** Quando false, só o botão de confirmar (alerta/aviso, sem Cancelar). */
  showCancel?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  classNames: ConfirmModalClassNames;
};

export function confirmModalBemClasses(
  prefix: string,
  options?: { actionsBlock?: string; actionsAlign?: "start" | "end" },
): ConfirmModalClassNames {
  const actionsBlock = options?.actionsBlock ?? "form-actions";
  const actionsAlign = options?.actionsAlign ?? "end";

  return {
    message: `${prefix}-confirm-modal__message`,
    actions: `${prefix}-${actionsBlock} ${prefix}-${actionsBlock}--${actionsAlign}`,
    cancelButton: `${prefix}-ghost-btn`,
    confirmButton: `${prefix}-primary-btn`,
    confirmButtonDanger: `${prefix}-danger-btn`,
  };
}

export function confirmModalPacClasses(): ConfirmModalClassNames {
  return confirmModalBemClasses("pac");
}

export function confirmModalTransformometroClasses(): ConfirmModalClassNames {
  return {
    message: "ds-confirm-modal__message",
    actions: "ds-cadastro-form__actions ds-form-actions--end",
    cancelButton: "ds-ghost-btn",
    confirmButton: "ds-primary-btn",
    confirmButtonDanger: "ds-danger-btn",
  };
}

export function ConfirmModalPanel({
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  confirmBusy = false,
  confirmBusyLabel = "Aguarde…",
  variant = "default",
  showCancel = true,
  onConfirm,
  onCancel,
  classNames,
}: ConfirmModalPanelProps) {
  const confirmButtonClass =
    variant === "danger" ? classNames.confirmButtonDanger : classNames.confirmButton;

  return (
    <>
      <p className={classNames.message}>{message}</p>
      <div className={classNames.actions}>
        {showCancel ? (
          <button type="button" className={classNames.cancelButton} disabled={confirmBusy} onClick={onCancel}>
            {cancelLabel}
          </button>
        ) : null}
        <button type="button" className={confirmButtonClass} disabled={confirmBusy} onClick={onConfirm}>
          {confirmBusy ? confirmBusyLabel : confirmLabel}
        </button>
      </div>
    </>
  );
}
