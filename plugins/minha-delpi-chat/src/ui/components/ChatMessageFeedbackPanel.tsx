import { CHAT_FEEDBACK_REASONS } from "../chatFeedbackReasons";

import "./ChatMessageFeedbackPanel.css";

type ChatMessageFeedbackPanelProps = {
  thanksMessage?: string | null;
  showReasonPicker?: boolean;
  onPickReason?: (reasonId: string) => void;
  onDismissReasons?: () => void;
};

export function ChatMessageFeedbackPanel({
  thanksMessage,
  showReasonPicker = false,
  onPickReason,
  onDismissReasons,
}: ChatMessageFeedbackPanelProps) {
  if (thanksMessage) {
    return <p className="mdc-chat-feedback-note">{thanksMessage}</p>;
  }

  if (!showReasonPicker) {
    return null;
  }

  return (
    <div className="mdc-chat-feedback-reasons" role="group" aria-label="Motivo do feedback">
      <p className="mdc-chat-feedback-reasons__hint">
        Obrigado pelo aviso. O que faltou nesta resposta?
      </p>
      <div className="mdc-chat-feedback-reasons__chips">
        {CHAT_FEEDBACK_REASONS.map((reason) => (
          <button
            key={reason.id}
            type="button"
            className="mdc-chat-feedback-reasons__chip"
            onClick={() => onPickReason?.(reason.id)}
          >
            {reason.label}
          </button>
        ))}
        <button
          type="button"
          className="mdc-chat-feedback-reasons__chip mdc-chat-feedback-reasons__chip--ghost"
          onClick={onDismissReasons}
        >
          Pular
        </button>
      </div>
    </div>
  );
}
