/**
 * Exclusão administrativa de competência (CF-UX-054).
 * A visibilidade é do Portal; a autorização efetiva continua na BFF.
 */
import { useRef, useState } from "react";

import { ApiError } from "../../api/httpClient";
import {
  deleteCompetence,
  diagnoseCompetenceDeletion,
  type CompetenceDeletionDiagnosis,
  type ClosingCompetence,
} from "../../api/competencesApi";
import { CfFeedbackMessage } from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfDialog,
  CfTextAreaField,
  CfTextField,
} from "../../app/controllershipFinanceUi";

const MONTHS = [
  "janeiro",
  "fevereiro",
  "março",
  "abril",
  "maio",
  "junho",
  "julho",
  "agosto",
  "setembro",
  "outubro",
  "novembro",
  "dezembro",
];

function periodLabel(period: string): string {
  const [year, month] = period.split("-");
  const index = Number(month) - 1;
  const name = MONTHS[index];
  return name ? `${name} de ${year}` : period;
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Não foi possível concluir a exclusão.";
}

function blockedMessage(
  reasons: CompetenceDeletionDiagnosis["reasons"],
): string {
  const parts = (reasons ?? [])
    .filter((item) => item.count > 0)
    .map((item) => `${item.count} ${item.label}`);
  if (!parts.length) {
    return "Exclusão bloqueada. Existe uma dependência que impede a remoção.";
  }
  return `Exclusão bloqueada. Existem ${parts.join(" e ")}.`;
}

export function DeleteCompetenceControl({
  competence,
  onDeleted,
}: {
  competence: ClosingCompetence;
  onDeleted: (period: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [diagnosis, setDiagnosis] = useState<CompetenceDeletionDiagnosis | null>(
    null,
  );
  const [diagnosisError, setDiagnosisError] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const idempotencyKey = useRef("");
  const sending = useRef(false);

  function close() {
    if (busy) return;
    setOpen(false);
  }

  async function openDialog() {
    idempotencyKey.current = crypto.randomUUID();
    setReason("");
    setConfirmation("");
    setSubmitError(null);
    setDiagnosis(null);
    setDiagnosisError(null);
    setOpen(true);
    try {
      const result = await diagnoseCompetenceDeletion(competence.period);
      setDiagnosis(result);
    } catch (error) {
      setDiagnosisError(errorMessage(error));
    }
  }

  const eligible = diagnosis?.outcome === "eligible";
  const checking = diagnosis === null && diagnosisError === null;
  const canSubmit =
    !busy && eligible && confirmation.trim() === competence.period;

  async function submit() {
    if (!canSubmit || sending.current) return;
    sending.current = true;
    setBusy(true);
    setSubmitError(null);
    try {
      const result = await deleteCompetence(competence.period, {
        expected_competence_id: competence.competence_id,
        reason: reason.trim(),
        idempotency_key: idempotencyKey.current,
      });
      if (!result.deleted || result.period !== competence.period) {
        throw new Error("A Central de Fechamento não confirmou esta competência.");
      }
      setBusy(false);
      setOpen(false);
      onDeleted(result.period);
    } catch (error) {
      sending.current = false;
      setBusy(false);
      setSubmitError(errorMessage(error));
    }
  }

  const fieldsLocked = busy || !eligible;

  return (
    <>
      <CfActionButton
        type="button"
        variant="ghost"
        className="cf-action-btn--danger"
        onClick={() => void openDialog()}
      >
        Excluir competência
      </CfActionButton>
      {open ? (
        <CfDialog
          open
          title={`Excluir competência — ${periodLabel(competence.period)}`}
          onClose={close}
          closeAriaLabel="Fechar exclusão de competência"
          footer={
            <>
              <CfActionButton type="button" onClick={close} disabled={busy}>
                Cancelar
              </CfActionButton>
              <CfActionButton
                type="submit"
                form="delete-competence-form"
                disabled={!canSubmit}
                onClick={() => void submit()}
              >
                {busy ? "Excluindo…" : "Confirmar exclusão"}
              </CfActionButton>
            </>
          }
        >
          <form
            id="delete-competence-form"
            className="cf-validation-panel__form"
            onSubmit={(event) => {
              event.preventDefault();
              void submit();
            }}
          >
            <p>
              A competência <strong>{periodLabel(competence.period)}</strong>{" "}
              ({competence.period}) será removida. A operação é destrutiva e
              não tem recuperação automática. A auditoria de abertura
              permanece. Dependências operacionais impedem a exclusão.
            </p>
            <p className="cf-validation-panel__doc-detail">
              Identificador {competence.competence_id}
            </p>
            {checking ? (
              <CfFeedbackMessage intent="info" title="Verificando dependências…">
                O diagnóstico de elegibilidade ainda não terminou.
              </CfFeedbackMessage>
            ) : null}
            {diagnosisError ? (
              <CfFeedbackMessage intent="error" title="Diagnóstico indisponível">
                {diagnosisError}
              </CfFeedbackMessage>
            ) : null}
            {diagnosis?.outcome === "blocked" ? (
              <CfFeedbackMessage intent="error" title="Exclusão bloqueada">
                {blockedMessage(diagnosis.reasons)}
              </CfFeedbackMessage>
            ) : null}
            {eligible ? (
              <CfFeedbackMessage intent="success" title="Exclusão permitida">
                Nenhuma dependência operacional foi encontrada.
              </CfFeedbackMessage>
            ) : null}
            <CfTextAreaField
              label="Motivo (opcional)"
              hint="Você pode registrar uma justificativa para a auditoria."
              rows={4}
              fullWidth
              maxLength={500}
              value={reason}
              disabled={fieldsLocked}
              onChange={setReason}
            />
            <CfTextField
              label={`Digite ${competence.period} para confirmar`}
              fullWidth
              value={confirmation}
              disabled={fieldsLocked}
              onChange={setConfirmation}
            />
            {submitError ? (
              <CfFeedbackMessage intent="error" title="A exclusão não foi concluída">
                {submitError}
              </CfFeedbackMessage>
            ) : null}
          </form>
        </CfDialog>
      ) : null}
    </>
  );
}
