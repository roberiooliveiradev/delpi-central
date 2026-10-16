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
} from "lucide-react";
import type { ComponentType } from "react";

import type { DeliaConfirmationRequest } from "../api/interactionClient";
import {
  dedupeOwnerHintContent,
  presentationOwnerHint,
} from "../api/presentation";
import type { DeliaMessageKind } from "../api/presentation";
import {
  ActivityViewer,
  ConversationStatus,
  EvidenceDetails,
  GovernedConfirmation,
  IconButton,
  MessageActionBar,
  UnifiedAvatar,
} from "@delpi/plugin-ui/index";
import type { EvidenceDetailItem } from "@delpi/plugin-ui/index";
import type { StatusBadgeVariant } from "@delpi/plugin-ui/index";
import { buildDeliaActivityView } from "../activity/activityView";

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

/** Formats an observed_at timestamp for presentation; returns null for
 *  absent/invalid values so the caller shows nothing rather than raw
 *  ISO. Presentation-only — never invents a timestamp. */
function formatObservedAt(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

export type DeliaAssistantMessageProps = {
  turn: ConversationDisplayTurn;
  loading: boolean;
  responding?: boolean;
  onResponseMotionComplete?: () => void;
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
  responding = false,
  onResponseMotionComplete,
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
  const activityView = buildDeliaActivityView(turn);

  // EvidenceDetails projection — user-facing only. `protocol`,
  // `remote_capability` and other control-plane identifiers are
  // technical-only and stay off this surface (doc 79/80); specialist_id
  // is the legitimate owner label. observed_at renders only when valid;
  // limitations arrive verbatim. No materiality signal exists in the
  // current contract → materialLimitationLabel is intentionally absent.
  const groundedSource =
    turn.groundingStatus === "GROUNDED" ? turn.provenance?.source : null;
  const observedLabel = formatObservedAt(turn.provenance?.observed_at);
  const evidenceItems: EvidenceDetailItem[] = [];
  if (turn.epistemicClass) {
    evidenceItems.push({
      label: "Classificação",
      value: turn.epistemicClass,
    });
  }
  if (groundedSource) {
    evidenceItems.push({
      label: "Fonte",
      value:
        groundedSource.source_system || groundedSource.source_id,
    });
    if (turn.provenance?.specialist_id) {
      evidenceItems.push({
        label: "Especialista",
        value: turn.provenance.specialist_id,
      });
    }
    if (observedLabel) {
      evidenceItems.push({
        label: "Observado em",
        value: observedLabel,
      });
    }
  }
  const evidenceSummary = groundedSource ? (
    <>
      Fonte · {groundedSource.source_system || groundedSource.source_id}
      {observedLabel ? <> · consultado em {observedLabel}</> : null}
    </>
  ) : turn.groundingStatus === "NON_GROUNDED" ? (
    "Sem fonte vinculada"
  ) : undefined;
  const hasEvidence =
    Boolean(evidenceSummary) ||
    evidenceItems.length > 0 ||
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
        <UnifiedAvatar
          kind="assistant"
          label="DÉLIA"
          size="sm"
          motionState={semanticState ? "attention" : responding ? "responding" : "idle"}
          onMotionComplete={onResponseMotionComplete}
        />
      </span>
      <div className="delia-turn__bubble">
        <div className="delia-turn__head">
          <span className="delia-turn__label">DÉLIA</span>
        </div>

        {activityView ? (
          <ActivityViewer
            {...activityView}
            className="delia-turn__activity"
          />
        ) : null}

        {semanticState ? (
          <ConversationStatus
            label={semanticState.label}
            tone={semanticState.variant}
            icon={StateIcon ? <StateIcon size={13} /> : undefined}
          />
        ) : null}

        <p className="delia-turn__content">{displayContent}</p>

        {ownerHint ? (
          <p className="delia-turn__notice">
            A fonte informou: {ownerHint}
          </p>
        ) : null}

        {turn.confirmationRequest && !turn.confirmationAnswered ? (
          (() => {
            // §6.184: the pending purpose distinguishes a scope choice
            // (owner needs no extra confirmation) from a bound decision
            // that also satisfies the owner-required confirmation —
            // one action, truthful copy, no extra click. Absent purpose
            // (legacy surface) keeps the conservative confirmation copy.
            const purpose = (
              turn.confirmationRequest as DeliaConfirmationRequest
            ).pending_purpose;
            const ownerConfirmation =
              purpose !== "execution_scope_choice";
            return (
              <GovernedConfirmation
                title={
                  ownerConfirmation
                    ? "Confirmação necessária"
                    : "Operação pronta para execução"
                }
                description={
                  purpose ===
                  "execution_scope_plus_owner_confirmation"
                    ? "Esta operação exige confirmação explícita — executar confirma a proposta preparada."
                    : undefined
                }
                confirmLabel={
                  ownerConfirmation ? "Confirmar e executar" : "Executar"
                }
                cancelLabel="Cancelar"
                loading={loading}
                onConfirm={() =>
                  onConfirmation(
                    turn.confirmationRequest as DeliaConfirmationRequest,
                    "CONFIRM",
                  )
                }
                onCancel={() =>
                  onConfirmation(
                    turn.confirmationRequest as DeliaConfirmationRequest,
                    "REJECT",
                  )
                }
              />
            );
          })()
        ) : null}

        {hasEvidence ? (
          <EvidenceDetails
            className="delia-turn__evidence-details"
            sourceSummary={evidenceSummary}
            items={evidenceItems}
            limitations={turn.limitations}
          />
        ) : null}

        <MessageActionBar
          className="delia-turn__message-actions"
          align="start"
          aria-label="Ações da resposta"
        >
          <IconButton
            aria-label={
              copied ? "Resposta copiada" : "Copiar resposta"
            }
            onClick={handleCopy}
          >
            {copied ? <Check size={13} /> : <Copy size={13} />}
          </IconButton>
        </MessageActionBar>
      </div>
    </>
  );
}
