import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  CircleCheckBig,
  Clock3,
  Loader2,
  MessageSquareWarning,
  UserRound,
  Wrench,
  X,
} from "lucide-react";
import type { MachineLoadOperation } from "./api.ts";
import { useOperatorSession } from "./OperatorSessionContext.ts";
import {
  feedbackReasonLabel,
  feedbackStatusPresentation,
  materialStatusLabel,
} from "./operatorFeedback.ts";
import type { OperatorFeedbackState } from "./useOperatorFeedback.ts";
import type { FeedbackSubmitResult } from "./useOperatorFeedback.ts";
import {
  PROCESS_ISSUE_DISCLAIMER,
  PROCESS_ISSUE_MATERIAL_CODE_MAX_LENGTH,
  PROCESS_ISSUE_NOTE_MAX_LENGTH,
  PROCESS_ISSUE_REASONS,
  PROCESS_ISSUE_TOOL_CODE_MAX_LENGTH,
  processIssueConfirmationMessage,
  processIssueReason,
} from "./processIssue.ts";
import { useProcessIssue } from "./useProcessIssue.ts";
import { PcpFeedbackStep } from "./PcpFeedbackStep.tsx";

type Props = {
  open: boolean;
  token: string;
  branch: string;
  operation: MachineLoadOperation;
  workCenter: string;
  /** Estado PCP — criado pelo launcher (badge usa o mesmo dado). */
  feedback: OperatorFeedbackState;
  onClose: () => void;
};

type HelpStep =
  | "destinations"
  | "pcp"
  | "process-reason"
  | "process-details"
  | "pcp-success"
  | "process-success";

type HelpDestination = {
  id: "pcp" | "process";
  label: string;
  description: string;
  Icon: typeof Wrench;
};

/**
 * Destinos da central — pequena configuração pensada para crescer (Qualidade,
 * Manutenção, Logística…) sem redesenhar o launcher nem a etapa de escolha.
 */
const HELP_DESTINATIONS: readonly HelpDestination[] = [
  {
    id: "pcp",
    label: "Produção / PCP",
    description:
      "Informar algo que está impedindo ou dificultando a produção.",
    Icon: MessageSquareWarning,
  },
  {
    id: "process",
    label: "Processos",
    description:
      "Informar um problema de roteiro, ferramenta, material ou posto de trabalho.",
    Icon: Wrench,
  },
] as const;

const STEP_TITLES: Record<HelpStep, string> = {
  destinations: "Pedir ajuda",
  pcp: "Produção / PCP",
  "process-reason": "Processos",
  "process-details": "Processos",
  "pcp-success": "Impedimento informado",
  "process-success": "Solicitação enviada",
};

const STEP_BACK: Partial<Record<HelpStep, HelpStep>> = {
  pcp: "destinations",
  "process-reason": "destinations",
  "process-details": "process-reason",
};

/**
 * Central «Pedir ajuda» — única superfície sobreposta (bottom sheet no
 * mobile, modal limitado no desktop) que conduz o operador por etapas:
 * destino → problema → detalhes → envio. Os domínios continuam donos do
 * próprio estado: useOperatorFeedback (PCP, injetado pelo launcher) e
 * useProcessIssue (Processos, com idempotência por tentativa). Rascunhos
 * moram aqui: «Voltar» preserva, fechar descarta.
 */
export function OperatorHelpSheet({
  open,
  token,
  branch,
  operation,
  workCenter,
  feedback,
  onClose,
}: Props) {
  const {
    session,
    status: sessionStatus,
    invalidate,
    openIdentify,
    identifyOpen,
  } = useOperatorSession();
  const issues = useProcessIssue({
    token,
    productionOrder: operation.production_order,
    operationCode: operation.operation_code,
    sessionToken: session?.sessionToken ?? null,
    onAuthError: invalidate,
  });

  const [step, setStep] = useState<HelpStep>("destinations");
  const [stepError, setStepError] = useState<string | null>(null);
  // Rascunho Processos — preservado na navegação interna, descartado ao fechar.
  const [issueCode, setIssueCode] = useState<string | null>(null);
  const [toolCode, setToolCode] = useState("");
  const [materialCode, setMaterialCode] = useState("");
  const [issueNote, setIssueNote] = useState("");
  // Rascunho PCP — mesma regra de preservação.
  const [pcpNote, setPcpNote] = useState("");
  const [pcpSelected, setPcpSelected] = useState<Set<string>>(new Set());
  // Tentativa P3: começa ao entrar no fluxo Processos e só termina no
  // fechamento/sucesso — retry do mesmo payload dentro da sessão reutiliza key.
  const [processAttempt, setProcessAttempt] = useState(false);
  const titleRef = useRef<HTMLHeadingElement>(null);

  const busy = issues.submitting || feedback.submitting;
  const backTarget = STEP_BACK[step] ?? null;

  // Reset somente na abertura (false → true): nova sessão do fluxo.
  const [wasOpen, setWasOpen] = useState(open);
  if (open !== wasOpen) {
    setWasOpen(open);
    if (open) {
      setStep("destinations");
      setStepError(null);
      setIssueCode(null);
      setToolCode("");
      setMaterialCode("");
      setIssueNote("");
      setPcpNote("");
      setPcpSelected(new Set());
      setProcessAttempt(false);
    }
  }

  const requestClose = () => {
    if (busy || identifyOpen) return;
    if (processAttempt) {
      issues.cancelAttempt();
      setProcessAttempt(false);
    }
    onClose();
  };

  const goToDestination = (id: HelpDestination["id"]) => {
    setStepError(null);
    if (id === "pcp") {
      setStep("pcp");
      return;
    }
    if (!processAttempt) {
      issues.beginAttempt();
      setProcessAttempt(true);
    }
    setStep("process-reason");
  };

  const goBack = () => {
    if (!backTarget || busy) return;
    setStepError(null);
    setStep(backTarget);
  };

  const submitPcp = async () => {
    const result: FeedbackSubmitResult = await feedback.submit(
      pcpNote.trim() || null,
      [...pcpSelected],
    );
    if (result.ok) {
      setStepError(null);
      setStep("pcp-success");
    } else {
      setStepError(result.message);
    }
  };

  const submitIssue = async () => {
    const reason = processIssueReason(issueCode);
    if (!reason || busy) return;
    const result = await issues.submit({
      issueCode: reason.code,
      toolCode: toolCode.trim() || null,
      materialCode: materialCode.trim() || null,
      note: issueNote.trim() || null,
    });
    if (result.ok) {
      setStepError(null);
      setStep("process-success");
    } else {
      setStepError(result.message);
    }
  };

  // Escape/backdrop fecham a superfície — nunca durante submit (dúvida sobre
  // o resultado) nem enquanto o modal de identificação está por cima.
  const busyRef = useRef(busy);
  const identifyOpenRef = useRef(identifyOpen);
  const requestCloseRef = useRef(requestClose);
  useEffect(() => {
    busyRef.current = busy;
    identifyOpenRef.current = identifyOpen;
    requestCloseRef.current = requestClose;
  });
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (
        event.key === "Escape" &&
        !busyRef.current &&
        !identifyOpenRef.current
      ) {
        requestCloseRef.current();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  // Foco no título da etapa — orienta a troca de contexto no wizard.
  useEffect(() => {
    if (!open) return;
    const frame = requestAnimationFrame(() => titleRef.current?.focus());
    return () => cancelAnimationFrame(frame);
  }, [open, step, sessionStatus]);

  if (!open) return null;

  const reason = processIssueReason(issueCode);
  const activeFeedback = feedback.active;
  const activePresentation = feedbackStatusPresentation(
    activeFeedback?.status,
  );

  const contextLine = "OP " + operation.production_order + " · Operação " + operation.operation_code + " · " + workCenter;

  return (
    <div
      className="pcp-pub-sheet"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-help-title"
    >
      <button
        type="button"
        className="pcp-pub-modal__backdrop"
        aria-label="Fechar"
        onClick={requestClose}
      />
      <div className="pcp-pub-modal__panel pcp-pub-sheet__panel">
        <div className="pcp-pub-sheet__head">
          {backTarget ? (
            <button
              type="button"
              className="pcp-pub-sheet__back"
              onClick={goBack}
              disabled={busy}
            >
              <ArrowLeft size={18} strokeWidth={2.2} aria-hidden="true" />
              Voltar
            </button>
          ) : (
            <span className="pcp-pub-sheet__head-spacer" aria-hidden="true" />
          )}
          <h3
            id="pcp-help-title"
            ref={titleRef}
            tabIndex={-1}
            className="pcp-pub-sheet__title"
          >
            {STEP_TITLES[step]}
          </h3>
          <button
            type="button"
            className="pcp-pub-sheet__close"
            aria-label="Fechar janela"
            onClick={requestClose}
            disabled={busy}
          >
            <X size={20} strokeWidth={2.2} aria-hidden="true" />
          </button>
        </div>

        <p className="pcp-pub-sheet__context">{contextLine}</p>

        <div className="pcp-pub-sheet__body">
          {feedback.notice ? (
            <p className="pcp-pub-sheet__notice" role="status">
              {feedback.notice}
            </p>
          ) : null}

          {sessionStatus === "restoring" ? (
            <p className="pcp-pub__feedback-muted" role="status">
              <Loader2 className="pcp-pub__spin" size={16} aria-hidden="true" />
              Verificando identificação do operador…
            </p>
          ) : null}

          {sessionStatus === "anonymous" ? (
            <div className="pcp-pub-sheet__identify">
              <p className="pcp-pub__feedback-muted">
                Identifique-se para enviar uma solicitação.
              </p>
              {stepError ? (
                <p className="pcp-pub__run-error" role="alert">
                  {stepError}
                </p>
              ) : null}
              <button
                type="button"
                className="pcp-pub__btn pcp-pub__btn--primary"
                onClick={openIdentify}
              >
                <UserRound size={18} strokeWidth={2.2} aria-hidden="true" />
                Identificar operador
              </button>
            </div>
          ) : null}

          {sessionStatus === "identified" && step === "destinations" ? (
            <>
              {activeFeedback ? (
                <div className="pcp-pub-sheet__ongoing" role="status">
                  <p className="pcp-pub-sheet__eyebrow">Em andamento</p>
                  <div className="pcp-pub-sheet__ongoing-head">
                    <span
                      className={
                        "pcp-pub-sheet__ongoing-icon" +
                        (activeFeedback.status === "acknowledged"
                          ? " is-treating"
                          : "")
                      }
                      aria-hidden="true"
                    >
                      <Clock3 size={18} strokeWidth={2.2} />
                    </span>
                    <div>
                      <p className="pcp-pub-sheet__ongoing-title">
                        {feedbackReasonLabel(activeFeedback.reasonCode)}
                      </p>
                      <p className="pcp-pub__feedback-muted">
                        {activePresentation.label}
                      </p>
                    </div>
                  </div>
                  {activeFeedback.materials?.length ? (
                    <ul
                      className="pcp-pub__feedback-material-statuses"
                      aria-label="Materiais informados"
                    >
                      {activeFeedback.materials.map((material) => (
                        <li
                          key={material.productCode}
                          className={
                            "pcp-pub__feedback-material-status" +
                            " is-" +
                            material.status
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
                </div>
              ) : null}

              {feedback.error && !activeFeedback ? (
                <div className="pcp-pub-sheet__notice" role="alert">
                  <span>{feedback.error}</span>
                  <button
                    type="button"
                    className="pcp-pub__btn pcp-pub__btn--ghost"
                    onClick={() => void feedback.refresh()}
                  >
                    Tentar novamente
                  </button>
                </div>
              ) : null}

              <p className="pcp-pub-sheet__question">
                O que você precisa comunicar?
              </p>
              <div className="pcp-pub-sheet__destinations">
                {HELP_DESTINATIONS.map((destination) => (
                  <button
                    key={destination.id}
                    type="button"
                    className="pcp-pub-sheet__destination"
                    onClick={() => goToDestination(destination.id)}
                  >
                    <span
                      className="pcp-pub-sheet__destination-icon"
                      aria-hidden="true"
                    >
                      <destination.Icon size={20} strokeWidth={2.2} />
                    </span>
                    <span className="pcp-pub-sheet__destination-body">
                      <strong>{destination.label}</strong>
                      <span>{destination.description}</span>
                    </span>
                    <span
                      className="pcp-pub-sheet__destination-chevron"
                      aria-hidden="true"
                    >
                      ›
                    </span>
                  </button>
                ))}
              </div>
            </>
          ) : null}

          {sessionStatus === "identified" && step === "pcp" ? (
            <PcpFeedbackStep
              token={token}
              branch={branch}
              operation={operation}
              note={pcpNote}
              selected={pcpSelected}
              busy={busy}
              error={stepError}
              onNoteChange={setPcpNote}
              onToggleMaterial={(code) =>
                setPcpSelected((prev) => {
                  const next = new Set(prev);
                  if (next.has(code)) next.delete(code);
                  else next.add(code);
                  return next;
                })
              }
              onSubmit={() => void submitPcp()}
              onCancel={requestClose}
            />
          ) : null}

          {sessionStatus === "identified" && step === "process-reason" ? (
            <>
              <p className="pcp-pub-sheet__question">
                Qual problema você encontrou?
              </p>
              <div className="pcp-pub-sheet__choices">
                {PROCESS_ISSUE_REASONS.map((item) => (
                  <button
                    key={item.code}
                    type="button"
                    className="pcp-pub-sheet__choice"
                    onClick={() => {
                      setIssueCode(item.code);
                      setStepError(null);
                      setStep("process-details");
                    }}
                  >
                    <span className="pcp-pub-sheet__choice-label">
                      {item.label}
                    </span>
                    <span
                      className="pcp-pub-sheet__destination-chevron"
                      aria-hidden="true"
                    >
                      ›
                    </span>
                  </button>
                ))}
              </div>
            </>
          ) : null}

          {sessionStatus === "identified" && step === "process-details" ? (
            <>
              <p className="pcp-pub-sheet__eyebrow pcp-pub-sheet__eyebrow--step">
                {reason?.label ?? "Problema de processo"}
              </p>

              {reason?.auxiliaryField === "toolCode" ? (
                <>
                  <label
                    className="pcp-pub__feedback-note-label"
                    htmlFor="pcp-help-issue-tool-code"
                  >
                    {reason.auxiliaryLabel}
                  </label>
                  <input
                    id="pcp-help-issue-tool-code"
                    className="pcp-pub__feedback-note pcp-pub__issue-aux-input"
                    type="text"
                    value={toolCode}
                    onChange={(event) => setToolCode(event.target.value)}
                    maxLength={PROCESS_ISSUE_TOOL_CODE_MAX_LENGTH}
                    disabled={busy}
                    placeholder={reason.auxiliaryPlaceholder ?? ""}
                  />
                </>
              ) : null}

              {reason?.auxiliaryField === "materialCode" ? (
                <>
                  <label
                    className="pcp-pub__feedback-note-label"
                    htmlFor="pcp-help-issue-material-code"
                  >
                    {reason.auxiliaryLabel}
                  </label>
                  <input
                    id="pcp-help-issue-material-code"
                    className="pcp-pub__feedback-note pcp-pub__issue-aux-input"
                    type="text"
                    value={materialCode}
                    onChange={(event) => setMaterialCode(event.target.value)}
                    maxLength={PROCESS_ISSUE_MATERIAL_CODE_MAX_LENGTH}
                    disabled={busy}
                    placeholder={reason.auxiliaryPlaceholder ?? ""}
                  />
                </>
              ) : null}

              <label
                className="pcp-pub__feedback-note-label"
                htmlFor="pcp-help-issue-note"
              >
                Observação <span>(opcional)</span>
              </label>
              <textarea
                id="pcp-help-issue-note"
                className="pcp-pub__feedback-note"
                value={issueNote}
                onChange={(event) => setIssueNote(event.target.value)}
                maxLength={PROCESS_ISSUE_NOTE_MAX_LENGTH}
                rows={3}
                disabled={busy}
                placeholder="Acrescente algum detalhe que possa ajudar Processos."
              />

              <p className="pcp-pub__feedback-disclaimer">
                {PROCESS_ISSUE_DISCLAIMER}
              </p>

              {stepError ? (
                <p
                  className="pcp-pub__run-error"
                  role="alert"
                  aria-live="assertive"
                >
                  {stepError}
                </p>
              ) : null}

              <div className="pcp-pub__run-actions">
                <button
                  type="button"
                  className="pcp-pub__btn pcp-pub__btn--primary"
                  onClick={() => void submitIssue()}
                  disabled={busy}
                  aria-busy={busy}
                >
                  {issues.submitting ? "Enviando…" : "Enviar para Processos"}
                </button>
                <button
                  type="button"
                  className="pcp-pub__btn pcp-pub__btn--ghost"
                  onClick={requestClose}
                  disabled={busy}
                >
                  Cancelar
                </button>
              </div>
            </>
          ) : null}

          {step === "pcp-success" ? (
            <div className="pcp-pub-sheet__success" role="status">
              <span className="pcp-pub-sheet__success-icon" aria-hidden="true">
                <CircleCheckBig size={28} strokeWidth={2} />
              </span>
              <p className="pcp-pub-sheet__success-title">
                {activePresentation.label}
              </p>
              <p className="pcp-pub__feedback-muted">
                {activePresentation.hint} O acompanhamento fica disponível em
                Pedir ajuda.
              </p>
              <button
                type="button"
                className="pcp-pub__btn pcp-pub__btn--primary"
                onClick={requestClose}
              >
                Concluir
              </button>
            </div>
          ) : null}

          {step === "process-success" ? (
            <div className="pcp-pub-sheet__success" role="status">
              <span className="pcp-pub-sheet__success-icon" aria-hidden="true">
                <CircleCheckBig size={28} strokeWidth={2} />
              </span>
              <p className="pcp-pub-sheet__success-title">
                {processIssueConfirmationMessage(
                  issues.confirmation?.requestNumber,
                )}
              </p>
              <button
                type="button"
                className="pcp-pub__btn pcp-pub__btn--primary"
                onClick={requestClose}
              >
                Concluir
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
