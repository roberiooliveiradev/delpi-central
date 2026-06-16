import { ChatModal } from "./shared/modal/ChatModal";
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
  return (
    <ChatModal
      open={open}
      onClose={onClose}
      size="sm"
      role="alertdialog"
      ariaLabelledBy="mdc-chat-alert-title"
      ariaDescribedBy="mdc-chat-alert-message"
      panelClassName="mdc-chat-alert-dialog"
    >
      <h2 id="mdc-chat-alert-title">{title}</h2>
      <p id="mdc-chat-alert-message">{message}</p>
      <footer>
        <button type="button" onClick={onClose}>
          {confirmLabel}
        </button>
      </footer>
    </ChatModal>
  );
}
