import { Check, MessageSquareWarning, X } from "lucide-react";

import { SectionCard, StateBox } from "./uiKit";

export type ApprovalDecisionKind = "approve" | "request_changes" | "reject";

type Props = {
  title?: string;
  hintWhenOpen?: string;
  canDecide: boolean;
  deciding: boolean;
  statusAllowsDecision: boolean;
  statusLabel: string;
  comment: string;
  commentError: string | null;
  onCommentChange: (value: string) => void;
  onDecide: (kind: ApprovalDecisionKind) => void;
  approveLabel?: string;
  kinds?: ApprovalDecisionKind[];
};

export function ApprovalDecisionPanel({
  title = "Decisão",
  hintWhenOpen,
  canDecide,
  deciding,
  statusAllowsDecision,
  statusLabel,
  comment,
  commentError,
  onCommentChange,
  onDecide,
  approveLabel = "Aprovar",
  kinds = ["approve", "request_changes", "reject"],
}: Props) {
  const showApprove = kinds.includes("approve");
  const showChanges = kinds.includes("request_changes");
  const showReject = kinds.includes("reject");
  const commentHint = showApprove
    ? "Obrigatório para solicitar ajustes ou reprovar"
    : "Obrigatório para solicitar ajustes no conjunto";

  return (
    <SectionCard
      title={title}
      hint={
        statusAllowsDecision
          ? hintWhenOpen ?? "Envie sempre a versão atual do planejamento."
          : "Este planejamento já não está aguardando decisão."
      }
    >
      {!statusAllowsDecision ? (
        <StateBox variant="default" dismissible={false}>
          Status atual: {statusLabel}. Novas decisões só são aceitas em «Enviado para
          aprovação».
        </StateBox>
      ) : (
        <>
          <label className="po-field">
            <span>Comentário / justificativa</span>
            <textarea
              rows={4}
              value={comment}
              onChange={(e) => onCommentChange(e.target.value)}
              placeholder={commentHint}
              disabled={deciding || !canDecide}
            />
          </label>
          {commentError ? (
            <StateBox variant="error" dismissible={false}>
              {commentError}
            </StateBox>
          ) : null}
          <div className="po-form-actions po-approval-decision__actions">
            {showApprove ? (
              <button
                type="button"
                className="po-btn po-btn--primary"
                disabled={!canDecide}
                onClick={() => onDecide("approve")}
              >
                <Check size={16} aria-hidden="true" />
                {deciding ? "Processando…" : approveLabel}
              </button>
            ) : null}
            {showChanges ? (
              <button
                type="button"
                className="po-btn po-btn--secondary"
                disabled={!canDecide}
                onClick={() => onDecide("request_changes")}
              >
                <MessageSquareWarning size={16} aria-hidden="true" />
                Solicitar ajustes
              </button>
            ) : null}
            {showReject ? (
              <button
                type="button"
                className="po-btn po-btn--secondary"
                disabled={!canDecide}
                onClick={() => onDecide("reject")}
              >
                <X size={16} aria-hidden="true" />
                Reprovar
              </button>
            ) : null}
          </div>
        </>
      )}
    </SectionCard>
  );
}
