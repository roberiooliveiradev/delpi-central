import { AlertTriangle, CircleHelp } from "lucide-react";
import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type ConfirmModalClassNames = {
  root: string;
  rootDanger: string;
  iconWrap: string;
  iconWrapDanger: string;
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
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    root: pair(`${prefix}-confirm-modal`, "delpi-ui-confirm-modal"),
    rootDanger: pair(`${prefix}-confirm-modal--danger`, "delpi-ui-confirm-modal--danger"),
    iconWrap: pair(`${prefix}-confirm-modal__icon`, "delpi-ui-confirm-modal__icon"),
    iconWrapDanger: pair(
      `${prefix}-confirm-modal__icon--danger`,
      "delpi-ui-confirm-modal__icon--danger",
    ),
    message: pair(`${prefix}-confirm-modal__message`, "delpi-ui-confirm-modal__message"),
    actions: [
      pair(`${prefix}-${actionsBlock}`, "delpi-ui-confirm-modal__actions"),
      pair(`${prefix}-${actionsBlock}--${actionsAlign}`, `delpi-ui-confirm-modal__actions--${actionsAlign}`),
    ].join(" "),
    cancelButton: delpiUiClass(`${prefix}-ghost-btn`, "delpi-ui-ghost-btn"),
    confirmButton: delpiUiClass(`${prefix}-primary-btn`, "delpi-ui-primary-btn"),
    confirmButtonDanger: delpiUiClass(`${prefix}-danger-btn`, "delpi-ui-danger-btn"),
  };
}

export function confirmModalPacClasses(): ConfirmModalClassNames {
  return confirmModalBemClasses("pac");
}

export function confirmModalTransformometroClasses(): ConfirmModalClassNames {
  return {
    root: "ds-confirm-modal",
    rootDanger: "ds-confirm-modal--danger",
    iconWrap: "ds-confirm-modal__icon",
    iconWrapDanger: "ds-confirm-modal__icon--danger",
    message: "ds-confirm-modal__message",
    actions: "ds-cadastro-form__actions ds-form-actions--end",
    cancelButton: "ds-ghost-btn",
    confirmButton: "ds-primary-btn",
    confirmButtonDanger: "ds-danger-btn",
  };
}

/**
 * Corpo do modal de confirmação/escolha — ícone de contexto + mensagem + ações.
 * Visual alinhado a padrões Primer/Linear (risco visível, labels de ação explícitos).
 */
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
  const Icon = variant === "danger" ? AlertTriangle : CircleHelp;
  const rootClass = [classNames.root, variant === "danger" ? classNames.rootDanger : ""]
    .filter(Boolean)
    .join(" ");
  const iconClass = [classNames.iconWrap, variant === "danger" ? classNames.iconWrapDanger : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass} data-confirm-variant={variant}>
      <div className={iconClass} aria-hidden="true">
        <Icon size={22} strokeWidth={2} />
      </div>
      <p className={classNames.message}>{message}</p>
      <div className={classNames.actions}>
        {showCancel ? (
          <button
            type="button"
            className={classNames.cancelButton}
            disabled={confirmBusy}
            onClick={onCancel}
            autoFocus={variant === "danger"}
          >
            {cancelLabel}
          </button>
        ) : null}
        <button
          type="button"
          className={confirmButtonClass}
          disabled={confirmBusy}
          onClick={onConfirm}
          autoFocus={variant !== "danger" || !showCancel}
        >
          {confirmBusy ? confirmBusyLabel : confirmLabel}
        </button>
      </div>
    </div>
  );
}
