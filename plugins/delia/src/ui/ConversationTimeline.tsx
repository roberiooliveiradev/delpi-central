import { ConversationUserMessage, UnifiedAvatar } from "@delpi/plugin-ui/index";

import type { ActivityViewerProps } from "@delpi/plugin-ui/index";

import type {
  DeliaConfirmationRequest,
  DeliaInteractionProvenance,
} from "../api/interactionClient";
import type { DeliaPresentation } from "../api/presentation";

import { DeliaAssistantMessage } from "./DeliaAssistantMessage";
import type { DeliaCurrentUserIdentity } from "../identity/currentUser";

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
  /** Explicit activity projection override — demo fixtures only;
   *  real turns derive it via `buildDeliaActivityView`. */
  activityView?: ActivityViewerProps;
};

export type ConversationTimelineProps = {
  turns: ConversationDisplayTurn[];
  loading: boolean;
  respondingTurnId?: string | null;
  onResponseMotionComplete?: () => void;
  /** Real user identity published by the platform — presentation only;
   *  absent → neutral person fallback. */
  userIdentity?: DeliaCurrentUserIdentity;
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
  respondingTurnId,
  onResponseMotionComplete,
  userIdentity,
  onConfirmation,
}: ConversationTimelineProps) {
  return (
    <ul className="delia-timeline" role="log" aria-label="Conversa atual">
      {turns.map((turn) => (
        <li
          key={turn.id}
          className={turn.role === "delia" ? "delia-turn delia-turn--delia delpi-ui-message-action-scope" : undefined}
        >
          {turn.role === "delia" ? (
            <DeliaAssistantMessage
              turn={turn}
              loading={loading}
              responding={turn.id === respondingTurnId}
              onResponseMotionComplete={onResponseMotionComplete}
              onConfirmation={onConfirmation}
            />
          ) : (
            <ConversationUserMessage
              authorLabel="Você"
              avatar={
                <UnifiedAvatar
                  kind="person"
                  label="Você"
                  size="sm"
                  imageUrl={userIdentity?.imageUrl ?? null}
                  fallbackText={userIdentity?.displayName ?? null}
                />
              }
            >
              {turn.content}
            </ConversationUserMessage>
          )}
        </li>
      ))}
    </ul>
  );
}
