import { User } from "lucide-react";

import type {
  DeliaConfirmationRequest,
  DeliaInteractionProvenance,
} from "../api/interactionClient";
import type { DeliaPresentation } from "../api/presentation";

import { DeliaAssistantMessage } from "./DeliaAssistantMessage";

/** Transient UI display state only — not session persistence or memory. */
export type ConversationDisplayTurn = {
  id: string;
  role: "user" | "delia";
  content: string;
  epistemicClass?: string | null;
  limitations?: string[];
  groundingStatus?: "GROUNDED" | "NON_GROUNDED" | null;
  provenance?: DeliaInteractionProvenance | null;
  /** Bounded pending-write confirmation surface (digests only). */
  confirmationRequest?: DeliaConfirmationRequest | null;
  /** The structured decision was already submitted for this request. */
  confirmationAnswered?: boolean;
  /** presentation.v1 projection — semantic state surface only. */
  presentation?: DeliaPresentation | null;
};

export type ConversationTimelineProps = {
  turns: ConversationDisplayTurn[];
  loading: boolean;
  onConfirmation: (
    request: DeliaConfirmationRequest,
    decision: "CONFIRM" | "REJECT",
  ) => void;
};

/**
 * S2-B — session timeline of the current (transient) conversation.
 *
 * Owns turn ordering only; each DÉLIA turn delegates to
 * `DeliaAssistantMessage`. `role="log"` gives assistive tech a
 * polite-append region without re-announcing prior content. User
 * turns align right, DÉLIA turns align left (WF-02 / doc 73).
 */
export function ConversationTimeline({
  turns,
  loading,
  onConfirmation,
}: ConversationTimelineProps) {
  return (
    <ul className="delia-timeline" role="log" aria-label="Conversa atual">
      {turns.map((turn) => (
        <li
          key={turn.id}
          className={`delia-turn delia-turn--${turn.role}`}
        >
          {turn.role === "delia" ? (
            <DeliaAssistantMessage
              turn={turn}
              loading={loading}
              onConfirmation={onConfirmation}
            />
          ) : (
            <>
              <span className="delia-turn__avatar" aria-hidden="true">
                <User size={14} />
              </span>
              <div className="delia-turn__bubble">
                <span className="delia-turn__label">Você</span>
                <p className="delia-turn__content">{turn.content}</p>
              </div>
            </>
          )}
        </li>
      ))}
    </ul>
  );
}
