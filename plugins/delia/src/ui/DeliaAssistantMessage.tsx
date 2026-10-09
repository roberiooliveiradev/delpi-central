import { useState } from "react";
import {
  Ban,
  Check,
  CircleAlert,
  CloudOff,
  Copy,
  ListChecks,
  Lock,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { ComponentType } from "react";

import type { DeliaConfirmationRequest } from "../api/interactionClient";
import {
  dedupeOwnerHintContent,
  presentationOwnerHint,
} from "../api/presentation";
import type { DeliaMessageKind } from "../api/presentation";
import type { StatusBadgeVariant } from "@delpi/plugin-ui/index";

import { DeliaStatusBadge } from "./deliaUi";
import type { ConversationDisplayTurn } from "./ConversationTimeline";

/** Semantic state presentation per canonical message_kind — the icon
 *  only restates the backend vocabulary, it never derives state from
 *  prose and never widens authority. */
const SEMANTIC_STATE: Record<
  Exclude<DeliaMessageKind, "RESULT">,
  { label: string; variant: StatusBadgeVariant; icon: ComponentType<{ size?: number }> }
> = {
  CLARIFICATION_REQUIRED: {
    label: "Esclarecimento necessário",
    variant: "info",
    icon: CircleAlert,
  },
  CONFIRMATION_REQUIRED: {
    label: "Confirmação pendente",
    variant: "warning",
    icon: ShieldCheck,
  },
  WRITE_REJECTED: {
    label: "Operação recusada",
    variant: "danger",
    icon: Ban,
  },
  AUTHZ_DENIED: {
    label: "Acesso não autorizado",
    variant: "danger",
    icon: Lock,
  },
  SOURCE_UNAVAILABLE: {
    label: "Fonte indisponível",
    variant: "warning",
    icon: CloudOff,
  },
  PRECONDITION_REQUIRED: {
    label: "Pré-condição pendente",
    variant: "warning",
    icon: ListChecks,
  },
};

export type DeliaAssistantMessageProps = {
  turn: ConversationDisplayTurn;
  loading: boolean;
  onConfirmation: (
    request: DeliaConfirmationRequest,
    decision: "CONFIRM" | "REJECT",
  ) => void;
};

/**
 * DELIA-UX-ASSISTANT-MESSAGE-COMPONENT-01 (doc 73/74 direction).
 *
 * One DÉLIA turn in the conversation timeline: the DÉLIA glyph (the
 * Sparkles mark already used by the Portal launcher/dock — never the
 * DELPI wordmark), the "DÉLIA" label, the real response text, then
 * visually subordinate metadata (semantic state, provenance,
 * epistemic class, limitations) and governed actions when present.
 *
 * Renders only contract data — no invented links, buttons, source
 * names, or structural blocks. presentation.v1 still governs what is
 * shown; this component never reinterprets it.
 */
export function DeliaAssistantMessage({
  turn,
  loading,
  onConfirmation,
}: DeliaAssistantMessageProps) {
  const [copied, setCopied] = useState(false);

  const ownerHint = presentationOwnerHint(turn.presentation ?? null);
  const displayContent = dedupeOwnerHintContent(turn.content, ownerHint);
  const semanticState =
    turn.presentation?.messageKind &&
    turn.presentation.messageKind !== "RESULT"
      ? SEMANTIC_STATE[
          turn.presentation.messageKind as Exclude<
            DeliaMessageKind,
            "RESULT"
          >
        ]
      : undefined;
  const StateIcon = semanticState?.icon;
  const hasMeta =
    Boolean(turn.epistemicClass) ||
    (turn.groundingStatus === "GROUNDED" && Boolean(turn.provenance?.source)) ||
    turn.groundingStatus === "NON_GROUNDED" ||
    (turn.limitations?.length ?? 0) > 0;

  function handleCopy() {
    try {
      const write = navigator.clipboard?.writeText(displayContent);
      if (!write) return;
      void write
        .then(() => {
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1500);
        })
        .catch(() => {});
    } catch {
      // Clipboard unavailable — the action silently no-ops.
    }
  }

  return (
    <>
      <span className="delia-turn__avatar" aria-hidden="true">
        <Sparkles size={14} />
      </span>
      <div className="delia-turn__bubble">
        <div className="delia-turn__head">
          <span className="delia-turn__label">DÉLIA</span>
          <button
            type="button"
            className="delia-turn__action"
            aria-label={
              copied ? "Resposta copiada" : "Copiar resposta"
            }
            onClick={handleCopy}
          >
            {copied ? <Check size={13} /> : <Copy size={13} />}
          </button>
        </div>

        {semanticState ? (
          <div className={`delia-turn__state delia-turn__state--${semanticState.variant}`}>
            {StateIcon ? (
              <StateIcon size={13} />
            ) : null}
            <DeliaStatusBadge
              label={semanticState.label}
              variant={semanticState.variant}
            />
          </div>
        ) : null}

        <p className="delia-turn__content">{displayContent}</p>

        {ownerHint ? (
          <p className="delia-turn__notice">
            A fonte informou: {ownerHint}
          </p>
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

        {hasMeta ? (
          <div className="delia-turn__meta" aria-label="Detalhes da resposta">
            {turn.epistemicClass ? (
              <span className="delia-turn__meta-item">
                classificação: {turn.epistemicClass}
              </span>
            ) : null}
            {turn.groundingStatus === "GROUNDED" &&
            turn.provenance?.source ? (
              <span className="delia-turn__meta-item">
                fonte: Cadastro de Produtos DELPI ·{" "}
                {turn.provenance.specialist_id ?? "especialista"}/
                {turn.provenance.protocol ?? "MCP"} ·{" "}
                {turn.provenance.observed_at ?? ""}
              </span>
            ) : null}
            {turn.groundingStatus === "NON_GROUNDED" ? (
              <span className="delia-turn__meta-item">
                sem fonte vinculada
              </span>
            ) : null}
            {turn.limitations && turn.limitations.length > 0 ? (
              <span className="delia-turn__meta-item">
                limitações: {turn.limitations.join(", ")}
              </span>
            ) : null}
          </div>
        ) : null}
      </div>
    </>
  );
}
