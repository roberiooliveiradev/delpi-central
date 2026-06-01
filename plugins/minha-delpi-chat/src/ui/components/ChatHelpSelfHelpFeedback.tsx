import { ThumbsDown, ThumbsUp } from "lucide-react";
import { useState } from "react";

import { HELP_SELF_HELP_FEEDBACK_REASONS } from "../helpSelfHelpFeedbackReasons";

import "./ChatHelpSelfHelpFeedback.css";

export type HelpSelfHelpFeedbackPayload = {
  helpful: boolean;
  reasonId?: string;
  topic?: string;
};

type ChatHelpSelfHelpFeedbackProps = {
  topic?: string | null;
  onFeedback?: (payload: HelpSelfHelpFeedbackPayload) => void;
};

export function ChatHelpSelfHelpFeedback({
  topic,
  onFeedback,
}: ChatHelpSelfHelpFeedbackProps) {
  const [phase, setPhase] = useState<"ask" | "reasons" | "thanks">("ask");

  if (!onFeedback) {
    return null;
  }

  if (phase === "thanks") {
    return (
      <p className="mdc-chat-help-feedback__thanks" role="status">
        Obrigado — isso ajuda a melhorar o guia do chat.
      </p>
    );
  }

  if (phase === "reasons") {
    return (
      <div className="mdc-chat-help-feedback__reasons" role="group" aria-label="Motivo">
        <p className="mdc-chat-help-feedback__hint">O que faltou nesta explicação?</p>
        <div className="mdc-chat-help-feedback__chips">
          {HELP_SELF_HELP_FEEDBACK_REASONS.map((reason) => (
            <button
              key={reason.id}
              type="button"
              className="mdc-chat-help-feedback__chip"
              onClick={() => {
                onFeedback({ helpful: false, reasonId: reason.id, topic: topic ?? undefined });
                setPhase("thanks");
              }}
            >
              {reason.label}
            </button>
          ))}
          <button
            type="button"
            className="mdc-chat-help-feedback__chip mdc-chat-help-feedback__chip--ghost"
            onClick={() => {
              onFeedback({ helpful: false, topic: topic ?? undefined });
              setPhase("thanks");
            }}
          >
            Pular
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mdc-chat-help-feedback" role="group" aria-label="Feedback da ajuda">
      <span className="mdc-chat-help-feedback__label">Isso ajudou?</span>
      <button
        type="button"
        className="mdc-chat-help-feedback__action"
        aria-label="Sim, ajudou"
        title="Sim, ajudou"
        onClick={() => {
          onFeedback({ helpful: true, topic: topic ?? undefined });
          setPhase("thanks");
        }}
      >
        <ThumbsUp size={15} aria-hidden="true" />
      </button>
      <button
        type="button"
        className="mdc-chat-help-feedback__action"
        aria-label="Não ajudou"
        title="Não ajudou"
        onClick={() => setPhase("reasons")}
      >
        <ThumbsDown size={15} aria-hidden="true" />
      </button>
    </div>
  );
}
