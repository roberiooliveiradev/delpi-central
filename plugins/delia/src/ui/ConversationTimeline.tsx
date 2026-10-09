import type {
  DeliaConfirmationRequest,
  DeliaInteractionProvenance,
} from "../api/interactionClient";
import {
  dedupeOwnerHintContent,
  presentationOwnerHint,
} from "../api/presentation";
import type {
  DeliaMessageKind,
  DeliaPresentation,
} from "../api/presentation";
import { Sparkles, User } from "lucide-react";
import type { StatusBadgeVariant } from "@delpi/plugin-ui/index";

import { DeliaStatusBadge } from "./deliaUi";

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

/** Semantic state badge per canonical message_kind (RESULT renders
 *  neutral — no badge). Presentation only; never derives state from
 *  prose and never widens authority. */
const MESSAGE_KIND_BADGE: Record<
  Exclude<DeliaMessageKind, "RESULT">,
  { label: string; variant: StatusBadgeVariant }
> = {
  CLARIFICATION_REQUIRED: {
    label: "Esclarecimento necessário",
    variant: "info",
  },
  CONFIRMATION_REQUIRED: {
    label: "Confirmação pendente",
    variant: "warning",
  },
  WRITE_REJECTED: { label: "Operação recusada", variant: "danger" },
  AUTHZ_DENIED: { label: "Acesso não autorizado", variant: "danger" },
  SOURCE_UNAVAILABLE: { label: "Fonte indisponível", variant: "warning" },
  PRECONDITION_REQUIRED: {
    label: "Pré-condição pendente",
    variant: "warning",
  },
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
 * Renders only real turn data: question, answer, semantic state,
 * provenance and limitations. `role="log"` gives assistive tech a
 * polite-append region without re-announcing prior content. User
 * turns align right, DÉLIA turns align left (WF-02).
 */
export function ConversationTimeline({
  turns,
  loading,
  onConfirmation,
}: ConversationTimelineProps) {
  return (
    <ul className="delia-timeline" role="log" aria-label="Conversa atual">
      {turns.map((turn) => {
        const ownerHint =
          turn.role === "delia"
            ? presentationOwnerHint(turn.presentation ?? null)
            : null;
        const displayContent = dedupeOwnerHintContent(
          turn.content,
          ownerHint,
        );
        const stateBadge =
          turn.presentation?.messageKind &&
          turn.presentation.messageKind !== "RESULT"
            ? MESSAGE_KIND_BADGE[
                turn.presentation.messageKind as Exclude<
                  DeliaMessageKind,
                  "RESULT"
                >
              ]
            : undefined;
        return (
          <li
            key={turn.id}
            className={`delia-turn delia-turn--${turn.role}`}
          >
            <span
              className="delia-turn__avatar"
              aria-hidden="true"
              title={turn.role === "user" ? "Você" : "DÉLIA"}
            >
              {turn.role === "user" ? (
                <User size={14} />
              ) : (
                <Sparkles size={14} />
              )}
            </span>
            <div className="delia-turn__bubble">
            <span className="delia-turn__label">
              {turn.role === "user" ? "Você" : "DÉLIA"}
            </span>
            {stateBadge ? (
              <DeliaStatusBadge
                label={stateBadge.label}
                variant={stateBadge.variant}
                className="delia-turn__state"
              />
            ) : null}
            <p className="delia-turn__content">{displayContent}</p>
            {ownerHint ? (
              <p className="delia-turn__notice">
                A fonte informou: {ownerHint}
              </p>
            ) : null}
            {turn.epistemicClass ? (
              <span className="delia-turn__meta">
                classificação: {turn.epistemicClass}
              </span>
            ) : null}
            {turn.groundingStatus === "GROUNDED" &&
            turn.provenance?.source ? (
              <span className="delia-turn__meta">
                fonte: Cadastro de Produtos DELPI ·{" "}
                {turn.provenance.specialist_id ?? "especialista"}/
                {turn.provenance.protocol ?? "MCP"} ·{" "}
                {turn.provenance.observed_at ?? ""}
              </span>
            ) : null}
            {turn.limitations && turn.limitations.length > 0 ? (
              <span className="delia-turn__meta">
                limitações: {turn.limitations.join(", ")}
              </span>
            ) : null}
            {turn.confirmationRequest && !turn.confirmationAnswered ? (
              <div
                className="delia-confirmation"
                role="group"
                aria-label="Confirmação pendente"
              >
                <button
                  type="button"
                  className="delia-confirmation__confirm"
                  disabled={loading}
                  onClick={() =>
                    onConfirmation(
                      turn.confirmationRequest as DeliaConfirmationRequest,
                      "CONFIRM",
                    )
                  }
                >
                  Confirmar
                </button>
                <button
                  type="button"
                  className="delia-confirmation__cancel"
                  disabled={loading}
                  onClick={() =>
                    onConfirmation(
                      turn.confirmationRequest as DeliaConfirmationRequest,
                      "REJECT",
                    )
                  }
                >
                  Cancelar
                </button>
              </div>
            ) : null}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
