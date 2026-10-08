import { useState } from "react";
import {
  CircleCheckBig,
  ClipboardList,
  Loader2,
  MessageSquareWarning,
  UserRound,
  Wrench,
  X,
} from "lucide-react";
import type { MachineLoadOperation } from "./api.ts";
import { useOperatorSession } from "./OperatorSessionContext.ts";
import { OperatorFeedbackPanel } from "./OperatorFeedbackPanel.tsx";
import { ProcessIssueModal } from "./ProcessIssueModal.tsx";
import { processIssueConfirmationMessage } from "./processIssue.ts";
import type { ProcessIssueDraft } from "./processIssue.ts";
import { useProcessIssue } from "./useProcessIssue.ts";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime.ts";

type Props = {
  token: string;
  branch: string;
  operation: MachineLoadOperation;
  workCenter: string;
  realtimeConnected: boolean;
  resyncSignal: number;
  feedbackRealtimeEvent: MachineLoadRealtimeEvent | null;
};

/**
 * «Solicitações do operador» — central de comunicação da operação (P3).
 *
 * Dois destinos, uma identificação: Produção/PCP (impedimento, fluxo C1–C6
 * preservado via OperatorFeedbackPanel embedded) e Processos (problema de
 * processo, POST P2 com idempotência ponta a ponta). O card de Processos não
 * acompanha status — o operador reporta e segue trabalhando.
 */
export function OperatorRequestsPanel({
  token,
  branch,
  operation,
  workCenter,
  realtimeConnected,
  resyncSignal,
  feedbackRealtimeEvent,
}: Props) {
  const { session, status: sessionStatus, invalidate, openIdentify } =
    useOperatorSession();
  const issues = useProcessIssue({
    token,
    productionOrder: operation.production_order,
    operationCode: operation.operation_code,
    sessionToken: session?.sessionToken ?? null,
    onAuthError: invalidate,
  });
  const [issueModalOpen, setIssueModalOpen] = useState(false);
  const [issueModalError, setIssueModalError] = useState<string | null>(null);

  const openIssueModal = () => {
    issues.beginAttempt();
    setIssueModalError(null);
    setIssueModalOpen(true);
  };

  const closeIssueModal = () => {
    setIssueModalOpen(false);
    setIssueModalError(null);
    issues.cancelAttempt();
  };

  const submitIssue = async (draft: ProcessIssueDraft) => {
    setIssueModalError(null);
    const result = await issues.submit(draft);
    if (!result.ok && result.message) {
      setIssueModalError(result.message);
    }
    if (result.ok) {
      setIssueModalOpen(false);
      setIssueModalError(null);
    }
    return result;
  };

  return (
    <section
      className="pcp-pub__requests"
      aria-labelledby="pcp-requests-section-title"
    >
      <h3 id="pcp-requests-section-title" className="pcp-pub__detail-section">
        <ClipboardList size={18} strokeWidth={2.2} aria-hidden="true" />
        Solicitações do operador
      </h3>

      {sessionStatus === "restoring" ? (
        <p className="pcp-pub__feedback-muted" role="status">
          <Loader2 className="pcp-pub__spin" size={16} aria-hidden="true" />
          Verificando identificação do operador…
        </p>
      ) : null}

      {sessionStatus === "anonymous" ? (
        <div className="pcp-pub__feedback-card pcp-pub__feedback-card--neutral">
          <p className="pcp-pub__feedback-muted">
            Identifique-se para enviar solicitações desta operação.
          </p>
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--ghost"
            onClick={openIdentify}
          >
            <UserRound size={18} strokeWidth={2.2} aria-hidden="true" />
            Identificar operador
          </button>
        </div>
      ) : null}

      {sessionStatus === "identified" ? (
        <div className="pcp-pub__requests-grid">
          <div className="pcp-pub__request-card">
            <div className="pcp-pub__request-card-head">
              <span className="pcp-pub__request-card-icon" aria-hidden="true">
                <MessageSquareWarning size={20} strokeWidth={2.2} />
              </span>
              <div>
                <p className="pcp-pub__request-card-title">Produção / PCP</p>
                <p className="pcp-pub__request-card-sub">
                  Impedimento de produção
                </p>
              </div>
            </div>
            <p className="pcp-pub__feedback-muted">
              Informe uma situação que impeça ou dificulte a produção.
            </p>
            <OperatorFeedbackPanel
              embedded
              token={token}
              branch={branch}
              operation={operation}
              workCenter={workCenter}
              realtimeConnected={realtimeConnected}
              resyncSignal={resyncSignal}
              feedbackRealtimeEvent={feedbackRealtimeEvent}
            />
          </div>

          <div className="pcp-pub__request-card">
            <div className="pcp-pub__request-card-head">
              <span
                className="pcp-pub__request-card-icon pcp-pub__request-card-icon--process"
                aria-hidden="true"
              >
                <Wrench size={20} strokeWidth={2.2} />
              </span>
              <div>
                <p className="pcp-pub__request-card-title">Processos</p>
                <p className="pcp-pub__request-card-sub">
                  Problema de processo
                </p>
              </div>
            </div>
            <p className="pcp-pub__feedback-muted">
              Informe problemas de roteiro, ferramenta, material ou posto.
            </p>
            {issues.confirmation ? (
              <p
                className="pcp-pub__request-confirmation"
                role="status"
              >
                <CircleCheckBig
                  size={18}
                  strokeWidth={2.2}
                  aria-hidden="true"
                />
                {processIssueConfirmationMessage(
                  issues.confirmation.requestNumber,
                )}
                <button
                  type="button"
                  className="pcp-pub__request-confirmation-dismiss"
                  aria-label="Dispensar confirmação"
                  onClick={issues.clearConfirmation}
                >
                  <X size={16} strokeWidth={2.2} aria-hidden="true" />
                </button>
              </p>
            ) : null}
            <button
              type="button"
              className="pcp-pub__btn pcp-pub__btn--primary pcp-pub__feedback-cta"
              onClick={openIssueModal}
            >
              <Wrench size={18} strokeWidth={2.2} aria-hidden="true" />
              Informar Processos
            </button>
          </div>
        </div>
      ) : null}

      <ProcessIssueModal
        open={issueModalOpen}
        operation={operation}
        workCenter={workCenter}
        busy={issues.submitting}
        error={issueModalError}
        onSubmit={submitIssue}
        onClose={closeIssueModal}
      />
    </section>
  );
}
