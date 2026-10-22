import {
  ConversationUserMessage,
  UnifiedAvatar,
} from "@delpi/plugin-ui/index";
import type {
  ActivityViewerProps,
  ConversationAuthorizedLink,
} from "@delpi/plugin-ui/index";

import type {
  DeliaActivityEvent,
  DeliaConfirmationRequest,
  DeliaInteractionProvenance,
  DeliaTurnObservability,
} from "../api/interactionClient";
import type {
  DeliaPresentation,
  DeliaTextFormat,
} from "../api/presentation";

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
  /** presentation.v1/v2 projection — semantic state surface only. */
  presentation?: DeliaPresentation | null;
  /** Fail-closed when wire claimed v2 but failed structural admission. */
  presentationFault?: "neutral_error" | null;
  /** Explicit format from admitted v2 text block; default plain/legacy. */
  contentFormat?: DeliaTextFormat;
  /** Source for markdown_safe rendering — never inferred from content. */
  markdownSource?: string | null;
  /** Host-published navigable destinations only (L1); empty until contract. */
  authorizedLinks?: readonly ConversationAuthorizedLink[];
  /** Explicit activity projection override — demo fixtures only;
   *  real turns derive it via `buildDeliaActivityView`. */
  activityView?: ActivityViewerProps;
  /** Observed ActivityEvent.v1 events retained for this turn —
   *  transient, request-scoped; the Context panel uses them for
   *  per-step timestamps. Never persisted (Prompt 5). */
  activityEvents?: readonly DeliaActivityEvent[];
  /** Bounded presentation-only observability projection (Prompt 5). */
  observability?: DeliaTurnObservability | null;
};

export type ConversationTimelineProps = {
  turns: ConversationDisplayTurn[];
  loading: boolean;
  respondingTurnId?: string | null;
  onResponseMotionComplete?: () => void;
  /** Selected assistant turn for the Context panel — transient
   *  conversation state only, never persisted (Prompt 5). */
  selectedTurnId?: string | null;
  onSelectTurn?: (turnId: string) => void;
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
  selectedTurnId,
  onSelectTurn,
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
              selected={turn.id === selectedTurnId}
              onSelect={
                onSelectTurn ? () => onSelectTurn(turn.id) : undefined
              }
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
