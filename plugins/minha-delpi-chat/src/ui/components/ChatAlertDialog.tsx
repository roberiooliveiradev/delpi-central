import { ModalPortal } from "./ModalPortal";
import "./chat-modal-surface.css";
import "./ChatAlertDialog.css";

type ChatAlertDialogProps = {
  open: boolean;
  title?: string;
  message: string;
  confirmLabel?: string;
  onClose: () => void;
};

export function ChatAlertDialog({
  open,
  title = "Aviso",
  message,
  confirmLabel = "Entendi",
  onClose,
}: ChatAlertDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <ModalPortal>
      <div
        className="mdc-modal-scrim--centered"
        role="presentation"
        onMouseDown={(event) => {
          if (event.target === event.currentTarget) {
            onClose();
          }
        }}
      >
        <section
          className="mdc-modal-panel mdc-chat-alert-dialog"
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="mdc-chat-alert-title"
          aria-describedby="mdc-chat-alert-message"
          onMouseDown={(event) => event.stopPropagation()}
        >
          <h2 id="mdc-chat-alert-title">{title}</h2>
          <p id="mdc-chat-alert-message">{message}</p>
          <footer>
            <button type="button" onClick={onClose}>
              {confirmLabel}
            </button>
          </footer>
        </section>
      </div>
    </ModalPortal>
  );
}
