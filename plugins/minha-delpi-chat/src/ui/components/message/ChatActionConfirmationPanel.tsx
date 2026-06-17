import "./ChatActionConfirmationPanel.css";

export type ChatActionConfirmation = {
  actionId?: string;
  path?: string;
  sensitivity?: string;
  summary?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmQuery?: string;
  cancelQuery?: string;
};

export function ChatActionConfirmationPanel({
  confirmation,
  onUseQuery,
}: {
  confirmation: ChatActionConfirmation | null | undefined;
  onUseQuery?: (query: string) => void;
}) {
  if (!confirmation || !onUseQuery) {
    return null;
  }

  const confirmQuery = String(confirmation.confirmQuery || "confirmo").trim();
  const cancelQuery = String(confirmation.cancelQuery || "cancelar esta ação").trim();

  if (!confirmQuery) {
    return null;
  }

  return (
    <div
      className="mdc-chat-action-confirmation"
      role="group"
      aria-label="Confirmação de ação sensível"
    >
      <p className="mdc-chat-action-confirmation__hint">
        {confirmation.summary
          ? `Ação pendente: ${confirmation.summary}`
          : "Esta ação requer sua confirmação."}
      </p>
      <div className="mdc-chat-action-confirmation__actions">
        <button
          type="button"
          className="mdc-chat-action-confirmation__btn mdc-chat-action-confirmation__btn--confirm"
          onClick={() => onUseQuery(confirmQuery)}
        >
          {confirmation.confirmLabel || "Confirmar"}
        </button>
        <button
          type="button"
          className="mdc-chat-action-confirmation__btn mdc-chat-action-confirmation__btn--cancel"
          onClick={() => onUseQuery(cancelQuery)}
        >
          {confirmation.cancelLabel || "Cancelar"}
        </button>
      </div>
    </div>
  );
}
