import "./ChatMessageFeedbackPanel.css";

export type ChatFeedbackCorrectiveAction = {
  id: string;
  label: string;
  action: "send_query" | "dismiss" | string;
  query?: string;
};

export type ChatFeedbackReason = {
  id: string;
  label: string;
};

type ChatMessageFeedbackPanelProps = {
  reasons: ChatFeedbackReason[];
  primaryReasonIds: string[];
  thanksMessage?: string | null;
  showReasonPicker?: boolean;
  showExtendedReasons?: boolean;
  correctiveActions?: ChatFeedbackCorrectiveAction[] | null;
  onPickReason?: (reasonId: string) => void;
  onDismissReasons?: () => void;
  onShowExtendedReasons?: () => void;
  onCorrectiveAction?: (action: ChatFeedbackCorrectiveAction) => void;
  onDismissCorrective?: () => void;
};

export function ChatMessageFeedbackPanel({
  reasons,
  primaryReasonIds,
  thanksMessage,
  showReasonPicker = false,
  showExtendedReasons = false,
  correctiveActions,
  onPickReason,
  onDismissReasons,
  onShowExtendedReasons,
  onCorrectiveAction,
  onDismissCorrective,
}: ChatMessageFeedbackPanelProps) {
  if (thanksMessage) {
    return <p className="mdc-chat-feedback-note">{thanksMessage}</p>;
  }

  if (correctiveActions && correctiveActions.length > 0) {
    return (
      <div className="mdc-chat-feedback-reasons" role="group" aria-label="Ações corretivas">
        <p className="mdc-chat-feedback-reasons__hint">
          Quer que eu tente corrigir agora?
        </p>
        <div className="mdc-chat-feedback-reasons__chips">
          {correctiveActions.map((action) => (
            <button
              key={action.id}
              type="button"
              className={[
                "mdc-chat-feedback-reasons__chip",
                action.action === "dismiss"
                  ? "mdc-chat-feedback-reasons__chip--ghost"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => onCorrectiveAction?.(action)}
            >
              {action.label}
            </button>
          ))}
          <button
            type="button"
            className="mdc-chat-feedback-reasons__chip mdc-chat-feedback-reasons__chip--ghost"
            onClick={onDismissCorrective}
          >
            Encerrar
          </button>
        </div>
      </div>
    );
  }

  if (!showReasonPicker) {
    return null;
  }

  const byId = new Map(reasons.map((reason) => [reason.id, reason]));
  const primaryReasons = primaryReasonIds
    .map((id) => byId.get(id))
    .filter((reason): reason is ChatFeedbackReason => Boolean(reason));
  const primaryIds = new Set(primaryReasons.map((reason) => reason.id));
  const extendedReasons = showExtendedReasons
    ? reasons.filter((reason) => !primaryIds.has(reason.id))
    : [];
  const visibleReasons = [...primaryReasons, ...extendedReasons];

  return (
    <div className="mdc-chat-feedback-reasons" role="group" aria-label="Motivo do feedback">
      <p className="mdc-chat-feedback-reasons__hint">
        Obrigado pelo aviso. O que faltou nesta resposta?
      </p>
      <div className="mdc-chat-feedback-reasons__chips">
        {visibleReasons.map((reason) => (
          <button
            key={reason.id}
            type="button"
            className="mdc-chat-feedback-reasons__chip"
            onClick={() => onPickReason?.(reason.id)}
          >
            {reason.label}
          </button>
        ))}
        {!showExtendedReasons ? (
          <button
            type="button"
            className="mdc-chat-feedback-reasons__chip mdc-chat-feedback-reasons__chip--ghost"
            onClick={onShowExtendedReasons}
          >
            Mais motivos
          </button>
        ) : null}
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
