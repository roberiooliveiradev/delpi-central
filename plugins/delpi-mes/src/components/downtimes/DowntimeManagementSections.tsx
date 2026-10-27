import { LoadingState, loadingStatePanelBemClasses } from "@delpi/plugin-ui/index";
import { useState } from "react";

import {
  classifyDowntime,
  concludeDowntimeTreatment,
  referDowntimeTreatment,
  upsertDowntimeTreatment,
} from "../../api/mesApi";
import { DelpiMesRequestError } from "../../api/httpClient";
import type { BranchCode } from "../../constants/routes";
import { DELPI_MES_COPY } from "../../content/copy";
import { useDowntimeManagement } from "../../hooks/useDowntimeManagement";
import type {
  DowntimeCauseKind,
  DowntimeHistoryItem,
  DowntimeItem,
  DowntimeReasonOption,
  DowntimeTreatment,
} from "../../types/mes";
import {
  isProcessIssueReasonCode,
  PROCESS_ISSUE_REASON_OPTIONS,
} from "../../utils/processIssueReasons";
import { formatDateTime } from "../../utils/downtimesPresentation";

const loadingClasses = loadingStatePanelBemClasses("delpi-mes");

const HISTORY_ACTION_LABELS: Record<string, string> = {
  downtime_reason_confirmed: "Classificação confirmada",
  downtime_reason_changed: "Motivo alterado",
  downtime_triage_created: "Triagem registrada",
  downtime_triage_updated: "Triagem atualizada",
  downtime_request_referred: "Encaminhada para Processos",
  downtime_treatment_concluded: "Tratamento concluído",
  automatic_downtime_started: "Parada detectada automaticamente",
};

const ACTOR_TYPE_LABELS: Record<string, string> = {
  operator: "Operador",
  manager: "Gestor",
  system: "Sistema",
};

const TREATMENT_STATUS_LABELS: Record<string, string> = {
  pending: "Em triagem",
  referred: "Encaminhada",
  concluded: "Concluída",
};

const REQUEST_STATUS_LABELS: Record<string, string> = {
  submitted: "Enviada",
  in_progress: "Em andamento",
  completed: "Concluída",
};

/** Mensagem segura por status — detalhes do domínio (409/422) chegam em PT
 * do backend; jamais vaza URL/token/erro interno. */
function describeManagementError(error: unknown, fallback: string): string {
  if (error instanceof DelpiMesRequestError) {
    if (error.status === 401) return "Sua sessão expirou. Entre novamente para continuar.";
    if (error.status === 403) return "Seu perfil não possui permissão para esta ação.";
    if (error.status === 404) return "Esta parada não foi encontrada. A listagem pode ter mudado.";
    if (error.status === 409 || error.status === 422) {
      const message = String(error.message ?? "").trim();
      if (message) return message;
    }
    if (error.status === 502 || error.status === 503) {
      return "Os dados MES estão temporariamente indisponíveis. Tente novamente.";
    }
  }
  return fallback;
}

function historyActionLabel(item: DowntimeHistoryItem): string {
  return HISTORY_ACTION_LABELS[item.action] ?? item.action;
}

function historyActorLabel(item: DowntimeHistoryItem): string {
  const type = ACTOR_TYPE_LABELS[item.actorType ?? ""] ?? item.actorType ?? "Sistema";
  return item.actorRef ? type + " " + item.actorRef : type;
}

function historyDetailHint(item: DowntimeHistoryItem): string | null {
  const details = item.details ?? {};
  const next = typeof details.reasonCode === "string" ? details.reasonCode : null;
  const previous =
    typeof details.previousReasonCode === "string" ? details.previousReasonCode : null;
  if (previous && next) return previous + " -> " + next;
  return next;
}

type ActionError = { message: string; conflict: boolean };

function ActionErrorNotice({
  error,
  onRetry,
}: {
  error: ActionError | null;
  onRetry?: () => void;
}) {
  if (!error) return null;
  return (
    <p className="delpi-mes-downtimes__form-error" role="alert">
      {error.message}
      {error.conflict && onRetry ? (
        <button type="button" onClick={onRetry}>Atualizar dados</button>
      ) : null}
    </p>
  );
}

export function DowntimeManagementSections({
  branch,
  item,
  reasons,
  reasonsLoading,
  canClassify,
  canTreat,
  canCreateProcessIssue,
  onChanged,
}: {
  branch: BranchCode;
  item: DowntimeItem;
  reasons: DowntimeReasonOption[];
  reasonsLoading: boolean;
  canClassify: boolean;
  canTreat: boolean;
  canCreateProcessIssue: boolean;
  onChanged: () => void;
}) {
  const management = useDowntimeManagement(branch, item.id);
  const treatment = management.treatment;
  const concluded = treatment?.status === "concluded";

  const notifyChanged = () => {
    void management.reload();
    onChanged();
  };

  return (
    <div className="delpi-mes-downtimes__management">
      <ClassificationSection
        key={item.id + "|" + (item.updatedAt ?? "") + "|" + (item.reasonCode ?? "")}
        branch={branch}
        item={item}
        reasons={reasons}
        reasonsLoading={reasonsLoading}
        canClassify={canClassify}
        onChanged={notifyChanged}
      />
      <TreatmentSection
        key={
          treatment
            ? treatment.downtimeId + "|" + (treatment.updatedAt ?? "")
            : item.id + "|new"
        }
        branch={branch}
        item={item}
        treatment={treatment}
        managementError={management.error}
        managementLoading={management.loading}
        canTreat={canTreat}
        canCreateProcessIssue={canCreateProcessIssue}
        readOnly={concluded}
        onChanged={notifyChanged}
        onRetry={management.reload}
      />
      <HistorySection
        items={management.history}
        loading={management.loading}
        error={management.error}
        onRetry={management.reload}
      />
    </div>
  );
}

function ClassificationSection({
  branch,
  item,
  reasons,
  reasonsLoading,
  canClassify,
  onChanged,
}: {
  branch: BranchCode;
  item: DowntimeItem;
  reasons: DowntimeReasonOption[];
  reasonsLoading: boolean;
  canClassify: boolean;
  onChanged: () => void;
}) {
  // O formulário remonta via key quando a classificação canônica muda —
  // o estado local sempre reflete o item mais recente sem efeito de sync.
  const [reasonCode, setReasonCode] = useState(item.reasonCode ?? "");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<ActionError | null>(null);
  const copy = DELPI_MES_COPY.downtimesManagement;

  if (!canClassify) {
    return (
      <section
        className="delpi-mes-downtimes__management-section"
        aria-labelledby="downtime-classify-title"
      >
        <h3 id="downtime-classify-title">Classificação</h3>
        <p className="delpi-mes-downtimes__hint">{copy.classifyDenied}</p>
      </section>
    );
  }

  const submit = async () => {
    if (!reasonCode || !item.updatedAt || saving) return;
    setSaving(true);
    setError(null);
    try {
      await classifyDowntime(item.id, {
        branch,
        reasonCode,
        note: note.trim() || null,
        expectedUpdatedAt: item.updatedAt,
      });
      setNote("");
      onChanged();
    } catch (reason) {
      const conflict = reason instanceof DelpiMesRequestError && reason.status === 409;
      setError({
        message: describeManagementError(reason, "Não foi possível salvar a classificação."),
        conflict,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <section
      className="delpi-mes-downtimes__management-section"
      aria-labelledby="downtime-classify-title"
    >
      <h3 id="downtime-classify-title">Classificação</h3>
      <p className="delpi-mes-downtimes__hint">{copy.classifyHint}</p>
      <div className="delpi-mes-downtimes__form">
        <label>
          Motivo
          <select
            value={reasonCode}
            onChange={(event) => setReasonCode(event.target.value)}
            disabled={saving || reasonsLoading}
          >
            <option value="">Selecione…</option>
            {reasons.map((reason) => (
              <option key={reason.code} value={reason.code}>
                {reason.label}
                {reason.active ? "" : " (inativo)"}
              </option>
            ))}
          </select>
        </label>
        <label>
          Observação
          <input
            type="text"
            value={note}
            maxLength={500}
            placeholder={copy.notePlaceholder}
            onChange={(event) => setNote(event.target.value)}
            disabled={saving}
          />
        </label>
        {item.confirmedAt ? (
          <p className="delpi-mes-downtimes__meta">
            Confirmada em {formatDateTime(item.confirmedAt)}
            {item.confirmedByRef ? " por " + item.confirmedByRef : ""}
          </p>
        ) : null}
        <ActionErrorNotice error={error} onRetry={onChanged} />
        <div className="delpi-mes-downtimes__form-actions">
          <button
            type="button"
            onClick={() => void submit()}
            disabled={saving || !reasonCode || !item.updatedAt}
          >
            {saving ? "Salvando…" : item.confirmed ? "Alterar motivo" : "Confirmar classificação"}
          </button>
        </div>
      </div>
    </section>
  );
}

function TreatmentSection({
  branch,
  item,
  treatment,
  managementLoading,
  managementError,
  canTreat,
  canCreateProcessIssue,
  readOnly,
  onChanged,
  onRetry,
}: {
  branch: BranchCode;
  item: DowntimeItem;
  treatment: DowntimeTreatment | null;
  managementLoading: boolean;
  managementError: string | null;
  canTreat: boolean;
  canCreateProcessIssue: boolean;
  readOnly: boolean;
  onChanged: () => void;
  onRetry: () => void;
}) {
  const copy = DELPI_MES_COPY.downtimesManagement;
  // Estado inicial semeado da triagem canônica — remount via key quando
  // o registro muda, sem efeito de sincronização.
  const [analysis, setAnalysis] = useState(treatment?.analysis ?? "");
  const [causeKind, setCauseKind] = useState<DowntimeCauseKind>(
    treatment?.causeKind ?? "hypothesis",
  );
  const [causeNote, setCauseNote] = useState(treatment?.causeNote ?? "");
  const [actionNeeded, setActionNeeded] = useState(treatment?.actionNeeded ?? false);
  const [justification, setJustification] = useState(treatment?.justification ?? "");
  const [issueCode, setIssueCode] = useState("");
  const [issueNote, setIssueNote] = useState("");
  const [conclusionReason, setConclusionReason] = useState("");
  const [busy, setBusy] = useState<"save" | "refer" | "conclude" | null>(null);
  const [error, setError] = useState<ActionError | null>(null);

  if (managementLoading) {
    return (
      <section
        className="delpi-mes-downtimes__management-section"
        aria-labelledby="downtime-triage-title"
      >
        <h3 id="downtime-triage-title">Triagem e tratamento</h3>
        <LoadingState classNames={loadingClasses} defaultMessage="Carregando a triagem…" />
      </section>
    );
  }

  if (managementError) {
    return (
      <section
        className="delpi-mes-downtimes__management-section"
        aria-labelledby="downtime-triage-title"
      >
        <h3 id="downtime-triage-title">Triagem e tratamento</h3>
        <ActionErrorNotice
          error={{ message: managementError, conflict: false }}
          onRetry={onRetry}
        />
      </section>
    );
  }

  const editable = canTreat && !readOnly;
  const run = async (kind: "save" | "refer" | "conclude", action: () => Promise<void>) => {
    if (busy) return;
    setBusy(kind);
    setError(null);
    try {
      await action();
      onChanged();
    } catch (reason) {
      const conflict = reason instanceof DelpiMesRequestError && reason.status === 409;
      setError({
        message: describeManagementError(reason, "Não foi possível concluir a ação."),
        conflict,
      });
    } finally {
      setBusy(null);
    }
  };

  const save = () =>
    run("save", async () => {
      await upsertDowntimeTreatment(item.id, {
        branch,
        analysis: analysis.trim(),
        causeKind,
        causeNote: causeNote.trim() || null,
        actionNeeded,
        justification: justification.trim(),
        expectedUpdatedAt: treatment?.updatedAt ?? null,
      });
    });

  const refer = () =>
    run("refer", async () => {
      await referDowntimeTreatment(item.id, {
        branch,
        issueCode,
        note: issueNote.trim() || null,
      });
    });

  const conclude = () =>
    run("conclude", async () => {
      await concludeDowntimeTreatment(item.id, {
        branch,
        reason: conclusionReason.trim(),
      });
    });

  const canSave =
    editable && analysis.trim().length > 0 && justification.trim().length > 0;
  const linkedRequest = treatment?.request ?? null;
  const linkedRef = treatment?.requestRef ?? null;
  const concludeBlocked =
    Boolean(linkedRef) && (!linkedRequest || linkedRequest.status !== "completed");

  return (
    <section
      className="delpi-mes-downtimes__management-section"
      aria-labelledby="downtime-triage-title"
    >
      <h3 id="downtime-triage-title">
        Triagem e tratamento
        {treatment ? (
          <span className="delpi-mes-downtimes__treatment-status">
            {TREATMENT_STATUS_LABELS[treatment.status] ?? treatment.status}
          </span>
        ) : null}
      </h3>
      {!canTreat ? <p className="delpi-mes-downtimes__hint">{copy.treatDenied}</p> : null}
      {treatment === null && !editable ? (
        <p className="delpi-mes-downtimes__hint">{copy.treatmentEmpty}</p>
      ) : null}

      {readOnly && treatment ? (
        <dl className="delpi-mes-downtimes__treatment-summary">
          <div>
            <dt>Análise</dt>
            <dd>{treatment.analysis}</dd>
          </div>
          <div>
            <dt>Causa</dt>
            <dd>
              {treatment.causeKind === "confirmed" ? "Confirmada" : "Hipótese"}
              {treatment.causeNote ? " — " + treatment.causeNote : ""}
            </dd>
          </div>
          <div>
            <dt>Ação necessária</dt>
            <dd>{treatment.actionNeeded ? "Sim" : "Não"}</dd>
          </div>
          <div>
            <dt>Justificativa</dt>
            <dd>{treatment.justification}</dd>
          </div>
          <div>
            <dt>Conclusão</dt>
            <dd>{treatment.conclusionReason ?? "—"}</dd>
          </div>
          <div>
            <dt>Concluída</dt>
            <dd>
              {formatDateTime(treatment.concludedAt)}
              {treatment.concludedBy ? " por " + treatment.concludedBy : ""}
            </dd>
          </div>
        </dl>
      ) : editable ? (
        <div className="delpi-mes-downtimes__form">
          <label>
            Análise
            <textarea
              value={analysis}
              maxLength={2000}
              rows={3}
              placeholder={copy.analysisPlaceholder}
              onChange={(event) => setAnalysis(event.target.value)}
              disabled={busy !== null}
            />
          </label>
          <div className="delpi-mes-downtimes__form-row">
            <label>
              Causa
              <select
                value={causeKind}
                onChange={(event) => setCauseKind(event.target.value as DowntimeCauseKind)}
                disabled={busy !== null}
              >
                <option value="hypothesis">Hipótese</option>
                <option value="confirmed">Confirmada</option>
              </select>
            </label>
            <label>
              Detalhe da causa
              <input
                type="text"
                value={causeNote}
                maxLength={500}
                onChange={(event) => setCauseNote(event.target.value)}
                disabled={busy !== null}
              />
            </label>
          </div>
          <label className="delpi-mes-downtimes__checkbox">
            <input
              type="checkbox"
              checked={actionNeeded}
              onChange={(event) => setActionNeeded(event.target.checked)}
              disabled={busy !== null}
            />
            Requer ação corretiva
          </label>
          <label>
            Justificativa
            <textarea
              value={justification}
              maxLength={2000}
              rows={2}
              placeholder={copy.justificationPlaceholder}
              onChange={(event) => setJustification(event.target.value)}
              disabled={busy !== null}
            />
          </label>
          <div className="delpi-mes-downtimes__form-actions">
            <button
              type="button"
              onClick={() => void save()}
              disabled={!canSave || busy !== null}
            >
              {busy === "save"
                ? "Salvando…"
                : treatment
                  ? "Atualizar triagem"
                  : "Registrar triagem"}
            </button>
          </div>
        </div>
      ) : null}

      {linkedRef ? (
        <div className="delpi-mes-downtimes__request" aria-live="polite">
          <h4>Solicitação vinculada</h4>
          {linkedRequest ? (
            <p>
              {linkedRequest.requestNumber ?? linkedRequest.requestId}
              {" · "}
              {linkedRequest.statusAlias ??
                REQUEST_STATUS_LABELS[linkedRequest.status ?? ""] ??
                linkedRequest.status ??
                "—"}
            </p>
          ) : (
            <p>
              {linkedRef.requestId}
              {treatment && !treatment.requestStatusAvailable ? " · situação indisponível" : ""}
            </p>
          )}
        </div>
      ) : null}

      {editable && treatment && !linkedRef ? (
        <div className="delpi-mes-downtimes__referral">
          <h4>Encaminhar para Processos</h4>
          {canCreateProcessIssue ? (
            <div className="delpi-mes-downtimes__form">
              <label>
                Tipo de problema
                <select
                  value={issueCode}
                  onChange={(event) => setIssueCode(event.target.value)}
                  disabled={busy !== null}
                >
                  <option value="">Selecione…</option>
                  {PROCESS_ISSUE_REASON_OPTIONS.map((option) => (
                    <option key={option.code} value={option.code}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Observação
                <input
                  type="text"
                  value={issueNote}
                  maxLength={500}
                  onChange={(event) => setIssueNote(event.target.value)}
                  disabled={busy !== null}
                />
              </label>
              <p className="delpi-mes-downtimes__hint">{copy.referralDisclaimer}</p>
              <div className="delpi-mes-downtimes__form-actions">
                <button
                  type="button"
                  onClick={() => void refer()}
                  disabled={busy !== null || !isProcessIssueReasonCode(issueCode)}
                >
                  {busy === "refer" ? "Encaminhando…" : "Encaminhar solicitação"}
                </button>
              </div>
            </div>
          ) : (
            <p className="delpi-mes-downtimes__hint">{copy.referralDenied}</p>
          )}
        </div>
      ) : null}

      {editable && treatment ? (
        <div className="delpi-mes-downtimes__conclusion">
          <h4>Concluir tratamento</h4>
          <div className="delpi-mes-downtimes__form">
            <label>
              Motivo da conclusão
              <input
                type="text"
                value={conclusionReason}
                maxLength={2000}
                onChange={(event) => setConclusionReason(event.target.value)}
                disabled={busy !== null}
              />
            </label>
            {concludeBlocked ? (
              <p className="delpi-mes-downtimes__hint">{copy.concludeBlocked}</p>
            ) : null}
            <div className="delpi-mes-downtimes__form-actions">
              <button
                type="button"
                onClick={() => void conclude()}
                disabled={busy !== null || conclusionReason.trim().length === 0}
              >
                {busy === "conclude" ? "Concluindo…" : "Concluir tratamento"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <ActionErrorNotice error={error} onRetry={onChanged} />
      {treatment?.updatedBy ? (
        <p className="delpi-mes-downtimes__meta">
          Última atualização {formatDateTime(treatment.updatedAt)} por {treatment.updatedBy}
        </p>
      ) : null}
    </section>
  );
}

function HistorySection({
  items,
  loading,
  error,
  onRetry,
}: {
  items: DowntimeHistoryItem[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}) {
  return (
    <section
      className="delpi-mes-downtimes__management-section"
      aria-labelledby="downtime-history-title"
    >
      <h3 id="downtime-history-title">Histórico</h3>
      {loading ? (
        <LoadingState classNames={loadingClasses} defaultMessage="Carregando o histórico…" />
      ) : error ? (
        <p className="delpi-mes-downtimes__form-error" role="alert">
          {error}
          <button type="button" onClick={onRetry}>Tentar novamente</button>
        </p>
      ) : items.length === 0 ? (
        <p className="delpi-mes-downtimes__hint">
          Nenhum evento de gestão registrado para esta parada.
        </p>
      ) : (
        <ul className="delpi-mes-downtimes__history">
          {items.map((entry) => (
            <li key={entry.id}>
              <strong>{historyActionLabel(entry)}</strong>
              <span>
                {formatDateTime(entry.occurredAt)}
                {" · "}
                {historyActorLabel(entry)}
                {historyDetailHint(entry) ? " · " + historyDetailHint(entry) : ""}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
