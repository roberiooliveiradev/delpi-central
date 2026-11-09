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

  const blocked = diagnosis?.outcome !== "eligible";
  const canSubmit =
    !busy &&
    diagnosis?.outcome === "eligible" &&
    reason.trim().length >= 3 &&
    confirmation.trim() === competence.period;

  async function submit() {
    if (!canSubmit) return;
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
      setBusy(false);
      setSubmitError(errorMessage(error));
    }
  }

  return (
    <>
      <span
        onClick={(event) => event.stopPropagation()}
        onKeyDown={(event) => event.stopPropagation()}
      >
        <CfActionButton type="button" onClick={() => void openDialog()}>
          Excluir competência
        </CfActionButton>
      </span>
      {open ? (
        <CfDialog
          open
          title={`Excluir competência ${periodLabel(competence.period)}`}
          onClose={close}
          closeAriaLabel="Fechar exclusão de competência"
        >
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void submit();
            }}
          >
            <p>
              Esta é uma operação administrativa destrutiva. A competência{" "}
              <strong>{periodLabel(competence.period)}</strong> ({competence.period}
              , identificador {competence.competence_id}) será removida somente
              se não houver dependências operacionais. A auditoria de abertura
              permanece. Não há recuperação automática.
            </p>
            {diagnosisError ? (
              <CfFeedbackMessage intent="error" title="Diagnóstico indisponível">
                {diagnosisError}
              </CfFeedbackMessage>
            ) : null}
            {diagnosis?.outcome === "blocked" ? (
              <CfFeedbackMessage intent="error" title="Exclusão bloqueada">
                {(diagnosis.reasons ?? [])
                  .map((item) => `${item.label} (${item.count})`)
                  .join(", ") || "dependência encontrada"}
                .
              </CfFeedbackMessage>
            ) : null}
            {diagnosis?.outcome === "eligible" ? (
              <p>Nenhuma dependência operacional foi encontrada.</p>
            ) : null}
            <label>
              Motivo
              <textarea
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                required
                minLength={3}
                maxLength={500}
                disabled={busy || blocked}
              />
            </label>
            <label>
              Digite {competence.period} para confirmar
              <input
                value={confirmation}
                onChange={(event) => setConfirmation(event.target.value)}
                autoComplete="off"
                disabled={busy || blocked}
                aria-label={`Confirmação da competência ${competence.period}`}
              />
            </label>
            {submitError ? (
              <CfFeedbackMessage intent="error" title="A exclusão não foi concluída">
                {submitError}
              </CfFeedbackMessage>
            ) : null}
            <div>
              <CfActionButton type="button" onClick={close} disabled={busy}>
                Cancelar
              </CfActionButton>
              <CfActionButton type="submit" disabled={!canSubmit}>
                {busy ? "Excluindo…" : "Confirmar exclusão"}
              </CfActionButton>
            </div>
          </form>
        </CfDialog>
      ) : null}
    </>
  );
}
