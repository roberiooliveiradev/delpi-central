import { AlertTriangle, X } from "lucide-react";

import { ModalPortal } from "./ModalPortal";
import "./chat-modal-surface.css";
import "./ChatConfirmDialog.css";

type ChatConfirmDialogProps = {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
};

export function ChatConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  danger,
  onConfirm,
  onCancel,
}: ChatConfirmDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <ModalPortal>
    <div
      className="mdc-modal-scrim--centered mdc-chat-confirm-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onCancel();
        }
      }}
    >
      <section
        className="mdc-modal-panel mdc-chat-confirm"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mdc-chat-confirm-title"
      >
        <header className="mdc-chat-confirm__header">
          <span
            className={
              danger
                ? "mdc-chat-confirm__icon mdc-chat-confirm__icon--danger"
                : "mdc-chat-confirm__icon"
            }
          >
            <AlertTriangle size={19} aria-hidden="true" />
          </span>

          <div>
            <h2 id="mdc-chat-confirm-title">{title}</h2>
            <p>{description}</p>
          </div>

          <button
            type="button"
            className="mdc-chat-confirm__close"
            onClick={onCancel}
            aria-label="Fechar"
          >
            <X size={17} aria-hidden="true" />
          </button>
        </header>

        <footer className="mdc-chat-confirm__actions">
          <button type="button" onClick={onCancel}>
            {cancelLabel}
          </button>

          <button
            type="button"
            className={danger ? "mdc-chat-confirm__danger" : undefined}
            onClick={() => void onConfirm()}
          >
            {confirmLabel}
          </button>
        </footer>
      </section>
    </div>
    </ModalPortal>
  );
}
