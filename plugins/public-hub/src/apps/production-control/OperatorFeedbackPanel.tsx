import { useState } from "react";
import { CircleCheck, Clock3, Loader2, MessageSquareWarning, UserRound } from "lucide-react";
import type { MachineLoadOperation } from "./api.ts";
import { useOperatorSession } from "./OperatorSessionContext.ts";
import {
  feedbackReasonLabel,
  feedbackStatusPresentation,
  materialStatusLabel,
  resolveFeedbackPanelState,
} from "./operatorFeedback.ts";
import { OperatorFeedbackModal } from "./OperatorFeedbackModal.tsx";
import { useOperatorFeedback } from "./useOperatorFeedback.ts";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime.ts";
import { formatTimeHm } from "./runTimeline.ts";

type Props = {
  token: string;
  branch: string;
  operation: MachineLoadOperation;
  workCenter: string;
  realtimeConnected: boolean;
  resyncSignal: number;
  feedbackRealtimeEvent: MachineLoadRealtimeEvent | null;
  /**
   * P3: dentro da central «Solicitações do operador» o card do coordenador
   * fornece título e o estado de identificação — o painel renderiza só o
   * conteúdo do fluxo PCP (status, CTA, modal).
   */
  embedded?: boolean;
};

/**
 * Fluxo «Impedimento ao PCP» no detalhe da operação (C3). Sozinho forma a
 * seção «Comunicação com PCP»; `embedded` o embute como card da central de
 * solicitações (P3) sem duplicar lógica.
 *
 * Canal de comunicação — não é ação de máquina: o painel nunca chama
 * pause/stop/downtime. Sem sessão válida o envio não acontece; a identidade
 * nunca sai do frontend (vem da bench session no backend).
 */
export function OperatorFeedbackPanel({
  token,
  branch,
  operation,
  workCenter,
  realtimeConnected,
  resyncSignal,
  feedbackRealtimeEvent,
  embedded = false,
}: Props) {
  const { session, status: sessionStatus, invalidate, openIdentify } =
    useOperatorSession();
  const feedback = useOperatorFeedback({
    token,
    productionOrder: operation.production_order,
    operationCode: operation.operation_code,
    sessionToken: session?.sessionToken ?? null,
    realtimeConnected,
    feedbackRealtimeEvent,
    resyncSignal,
    onAuthError: invalidate,
  });
  const [modalOpen, setModalOpen] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const state = resolveFeedbackPanelState({
    sessionStatus,
    loading: feedback.loading,
    error: feedback.error,
    active: feedback.active,
  });
  const presentation = feedbackStatusPresentation(feedback.active?.status);

  const submit = async (note: string | null, materialCodes: string[]) => {
    setModalError(null);
    const result = await feedback.submit(note, materialCodes);
    if (!result.ok && result.message) {
      setModalError(result.message);
    }
    return result;
  };

  const body = (
    <>
      {!embedded && state === "restoring" ? (
        <p className="pcp-pub__feedback-muted" role="status">
          <Loader2 className="pcp-pub__spin" size={16} aria-hidden="true" />
          Verificando identificação do operador…
        </p>
      ) : null}

      {!embedded && state === "anonymous" ? (
        <div className="pcp-pub__feedback-card pcp-pub__feedback-card--neutral">
          <p className="pcp-pub__feedback-muted">
            Identifique-se para comunicar esta operação ao PCP.
          </p>
          {feedback.notice ? (
            <p className="pcp-pub__feedback-muted" role="status">
              {feedback.notice}
            </p>
          ) : null}
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

      {state === "loading" ? (
        <p className="pcp-pub__feedback-muted" role="status">
          <Loader2 className="pcp-pub__spin" size={16} aria-hidden="true" />
          Verificando avisos desta operação…
        </p>
      ) : null}

      {state === "error" ? (
        <div className="pcp-pub__feedback-card pcp-pub__feedback-card--neutral">
          <p className="pcp-pub__feedback-muted" role="status">
            {feedback.error}
          </p>
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--ghost"
            onClick={() => void feedback.refresh()}
          >
            Tentar novamente
          </button>
        </div>
      ) : null}

      {state === "none" ? (
        <div className="pcp-pub__feedback-card pcp-pub__feedback-card--cta">
          <p className="pcp-pub__feedback-muted">
            Encontrou algum impedimento que impeça esta operação de ser
            produzida?
          </p>
          {feedback.notice ? (
            <p className="pcp-pub__feedback-muted" role="status">
              {feedback.notice}
            </p>
          ) : null}
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--primary pcp-pub__feedback-cta"
            onClick={() => setModalOpen(true)}
          >
            <MessageSquareWarning size={18} strokeWidth={2.2} aria-hidden="true" />
            Informar ao PCP
          </button>
        </div>
      ) : null}

      {state === "open" || state === "acknowledged" ? (
        <div
          className={
            "pcp-pub__feedback-card " +
            (state === "acknowledged"
              ? "pcp-pub__feedback-card--treating"
              : "pcp-pub__feedback-card--informed")
          }
          role="status"
        >
          <div className="pcp-pub__feedback-status-head">
            <span className="pcp-pub__feedback-status-icon" aria-hidden="true">
              {state === "acknowledged" ? (
                <CircleCheck size={20} strokeWidth={2.2} />
              ) : (
                <Clock3 size={20} strokeWidth={2.2} />
              )}
            </span>
            <div>
              <p className="pcp-pub__feedback-status-label">
                {presentation.label}
              </p>
              <p className="pcp-pub__feedback-muted">{presentation.hint}</p>
            </div>
          </div>
          <dl className="pcp-pub__feedback-status-facts">
            <div>
              <dt>Motivo</dt>
              <dd>{feedbackReasonLabel(feedback.active?.reasonCode)}</dd>
            </div>
            <div>
              <dt>Aviso</dt>
              <dd>
                {feedback.active?.createdAt
                  ? formatTimeHm(feedback.active.createdAt)
                  : "—"}
              </dd>
            </div>
          </dl>
          {feedback.active?.materials?.length ? (
            <ul
              className="pcp-pub__feedback-material-statuses"
              aria-label="Materiais informados"
            >
              {feedback.active.materials.map((material) => (
                <li
                  key={material.productCode}
                  className={
                    "pcp-pub__feedback-material-status" +
                    " is-" + material.status
                  }
                >
                  <span className="pcp-pub__feedback-material-status-body">
                    <strong>{material.productCode}</strong>
                    <span>{material.description}</span>
                  </span>
                  <span className="pcp-pub__feedback-material-badge">
                    {materialStatusLabel(material.status)}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
          {feedback.active?.note ? (
            <p className="pcp-pub__feedback-note-view">
              “{feedback.active.note}”
            </p>
          ) : null}
        </div>
      ) : null}

      <OperatorFeedbackModal
        open={modalOpen}
        token={token}
        branch={branch}
        operation={operation}
        workCenter={workCenter}
        busy={feedback.submitting}
        error={modalError}
        onSubmit={submit}
        onClose={() => {
          setModalOpen(false);
          setModalError(null);
        }}
      />
    </>
  );

  if (embedded) {
    // A central (P3) fornece seção, título e identificação — o painel entrega
    // apenas o conteúdo do fluxo PCP dentro do card «Produção / PCP».
    return (
      <div className="pcp-pub__feedback pcp-pub__feedback--embedded">
        {body}
      </div>
    );
  }

  return (
    <section
      className="pcp-pub__feedback"
      aria-labelledby="pcp-feedback-section-title"
    >
      <h3 id="pcp-feedback-section-title" className="pcp-pub__detail-section">
        <MessageSquareWarning size={18} strokeWidth={2.2} aria-hidden="true" />
        Comunicação com PCP
      </h3>
      {body}
    </section>
  );
}
