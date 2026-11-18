/**
 * Checklist vivo (CF-CHECKLIST-LIVE-004) — painel administrativo com
 * três seções, todas governadas pela BFF (`/admin/checklist-templates`):
 *
 * - `ChecklistSeriesSection` — séries/sequências do template e o fluxo
 *   excepcional de nova sequência (confirmação START_NEW_SEQUENCE);
 * - `ChecklistRevisionsSection` — revisões internas append-only sobre a
 *   versão PUBLISHED vigente (ADD/UPDATE/RETIRE/REACTIVATE/REORDER em
 *   lote, prévia de impacto, OCC e reversão compensatória);
 * - `ChecklistSyncSection` — runs da outbox de sincronização com
 *   reprocessamento autorizado de falhas.
 *
 * A página apenas renderiza e encaminha — autorização efetiva (MANAGE),
 * idempotência e regras de negócio ficam na BFF.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { GitBranch, History, RefreshCw } from "lucide-react";

import {
  applyChecklistRevision,
  listChecklistSeries,
  listChecklistSyncRuns,
  listVersionRevisions,
  previewChecklistRevision,
  retryChecklistSyncEvent,
  revertChecklistRevision,
  startChecklistSequence,
  type ChecklistRevision,
  type ChecklistSeries,
  type ChecklistSyncRun,
  type RevisionChangeInput,
  type RevisionPreview,
} from "../../api/adminApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfDataRecordCard,
  CfStatusBadge,
} from "../../app/controllershipFinanceUi";
import type { DataRecordCardField } from "@delpi/plugin-ui/index";
import {
  DataTableSection,
  type DataTableColumn,
} from "../../app/cfDataTableUi";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";
import {
  toQueryError,
  type QueryError,
} from "./checklistAdminShared";

const ICON_PROPS = {
  size: 15,
  strokeWidth: 1.9,
  "aria-hidden": true,
} as const;

const SERIES_STATUS_LABELS: Record<string, string> = {
  ACTIVE: "Ativa",
  CLOSED: "Encerrada",
};

const RUN_STATE_LABELS: Record<string, string> = {
  PENDING: "Pendente",
  APPLYING: "Aplicando",
  APPLIED: "Aplicado",
  APPLIED_WITH_EXCLUSIONS: "Aplicado com exclusões",
  SKIPPED: "Ignorado",
  PARTIAL: "Parcial",
  FAILED: "Falho",
};

function newIdemKey(): string {
  return `cf-live-${Date.now()}-${Math.random()
    .toString(36)
    .slice(2, 10)}`;
}

// -- Séries -----------------------------------------------------------------

export function ChecklistSeriesSection({
  templateId,
  onChanged,
}: {
  templateId: string;
  onChanged: () => void;
}) {
  const [series, setSeries] = useState<ChecklistSeries[] | null>(null);
  const [error, setError] = useState<QueryError | null>(null);
  const [busy, setBusy] = useState(false);
  const [startReason, setStartReason] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const requestId = useRef(0);

  const load = useCallback(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    listChecklistSeries(templateId, { signal: controller.signal })
      .then((items) => {
        if (controller.signal.aborted || requestId.current !== id)
          return;
        setSeries(items);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id)
          return;
        setError(toQueryError(err, "Falha ao listar sequências."));
      });
    return () => controller.abort();
  }, [templateId]);

  useEffect(() => load(), [load]);

  const columns: DataTableColumn<ChecklistSeries>[] = [
    {
      key: "series_no",
      header: "Sequência",
      headerHint: CF_HELP.checklistLive.seriesNo,
      className: "cf-table__col--compact",
      sortable: true,
      sortValue: (row) => row.series_no,
      render: (row) => `S${row.series_no}`,
    },
    {
      key: "status",
      header: "Estado",
      className: "cf-table__col--status",
      sortable: true,
      sortValue: (row) => row.status,
      render: (row) => (
        <CfStatusBadge
          label={SERIES_STATUS_LABELS[row.status] ?? row.status}
          variant={row.status === "ACTIVE" ? "success" : "neutral"}
        />
      ),
    },
    {
      key: "versions",
      header: "Nº de versões",
      className: "cf-table__col--compact",
      align: "right",
      sortable: true,
      sortValue: (row) => row.versions ?? 0,
      render: (row) => row.versions ?? "—",
    },
    {
      key: "started_at",
      header: "Iniciada em",
      className: "cf-table__col--wrap",
      sortable: true,
      sortValue: (row) => row.started_at,
      render: (row) => formatDateTime(row.started_at),
    },
    {
      key: "closed_at",
      header: "Encerrada em",
      className: "cf-table__col--wrap",
      sortable: true,
      sortValue: (row) => row.closed_at ?? "",
      render: (row) =>
        row.closed_at ? formatDateTime(row.closed_at) : "—",
    },
    {
      key: "reason",
      header: "Motivo",
      className: "cf-table__col--wrap",
      sortable: true,
      sortValue: (row) => row.start_reason ?? "",
      render: (row) => row.start_reason ?? "—",
    },
  ];

  const startSequence = () => {
    setBusy(true);
    setError(null);
    setFeedback(null);
    startChecklistSequence(templateId, {
      reason: startReason.trim(),
      confirmation: confirmation.trim(),
      idempotency_key: newIdemKey(),
    })
      .then((result) => {
        setFeedback(
          `Sequência S${result.series_no} iniciada — V1 em rascunho.`,
        );
        setStartReason("");
        setConfirmation("");
        setSeries(null);
        load();
        onChanged();
      })
      .catch((err: unknown) =>
        setError(toQueryError(err, "Falha ao iniciar sequência.")),
      )
      .finally(() => setBusy(false));
  };

  const confirmed = confirmation.trim() === "START_NEW_SEQUENCE";

  return (
    <section
      aria-label="Sequências do checklist"
      data-testid="checklist-series-section"
    >
      <DataTableSection<ChecklistSeries>
        title="Sequências"
        titleHint={CF_HELP.checklistLive.series}
        columns={columns}
        rows={series ?? []}
        rowKey={(row) => row.series_id}
        loading={series === null}
        emptyMessage="Nenhuma sequência registrada para este checklist."
        columnPreferencesKey="cf-checklist-live-series-columns"
        viewLayoutPreferencesKey="cf-checklist-live-series"
        renderCard={(row) => {
          const fields: DataRecordCardField[] = [
            {
              id: "status",
              label: "Estado",
              value:
                SERIES_STATUS_LABELS[row.status] ?? row.status,
            },
            {
              id: "started",
              label: "Iniciada em",
              value: formatDateTime(row.started_at),
            },
          ];
          return (
            <CfDataRecordCard
              title={`S${row.series_no}`}
              fields={fields}
            />
          );
        }}
        getSearchText={(row) =>
          `s${row.series_no} ${
            SERIES_STATUS_LABELS[row.status] ?? row.status
          }`
        }
      />
      {error ? (
        <CfQueryErrorBanner
          error={error}
          dataset="as sequências do checklist"
          onRetry={load}
        />
      ) : null}
      {feedback ? (
        <CfFeedbackMessage intent="success" title="Sequência iniciada">
          {feedback}
        </CfFeedbackMessage>
      ) : null}
      <div className="cf-live-start-sequence" role="group"
        aria-label="Iniciar nova sequência">
        <label className="cf-field">
          <span>Motivo da nova sequência</span>
          <input
            type="text"
            value={startReason}
            maxLength={500}
            onChange={(event) => setStartReason(event.target.value)}
            aria-label="Motivo da nova sequência"
          />
        </label>
        <label className="cf-field">
          <span>
            Confirmação — digite START_NEW_SEQUENCE
          </span>
          <input
            type="text"
            value={confirmation}
            onChange={(event) => setConfirmation(event.target.value)}
            aria-label="Confirmação da nova sequência"
            autoComplete="off"
          />
        </label>
        <CfActionButton
          type="button"
          variant="ghost"
          disabled={
            busy || !startReason.trim() || !confirmed
          }
          title={
            confirmed
              ? undefined
              : "Digite START_NEW_SEQUENCE para habilitar."
          }
          onClick={startSequence}
        >
          <GitBranch {...ICON_PROPS} />
          Iniciar nova sequência
        </CfActionButton>
      </div>
    </section>
  );
}

// -- Revisões sobre a versão PUBLISHED ---------------------------------------

export function ChecklistRevisionsSection({
  templateId,
  versionId,
  currentRevision,
  onChanged,
}: {
  templateId: string;
  versionId: string;
  currentRevision: number;
  onChanged: () => void;
}) {
  const [revisions, setRevisions] = useState<ChecklistRevision[] | null>(
    null,
  );
  const [error, setError] = useState<QueryError | null>(null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [expectedRevision, setExpectedRevision] = useState(
    currentRevision,
  );
  const [changesText, setChangesText] = useState("[]");
  const [preview, setPreview] = useState<RevisionPreview | null>(null);
  const requestId = useRef(0);

  const load = useCallback(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    listVersionRevisions(templateId, versionId, {
      signal: controller.signal,
    })
      .then((items) => {
        if (controller.signal.aborted || requestId.current !== id)
          return;
        setRevisions(items);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id)
          return;
        setError(toQueryError(err, "Falha ao listar revisões."));
      });
    return () => controller.abort();
  }, [templateId, versionId]);

  useEffect(() => load(), [load]);

  const parseChanges = (): RevisionChangeInput[] | null => {
    try {
      const parsed = JSON.parse(changesText) as RevisionChangeInput[];
      return Array.isArray(parsed) ? parsed : null;
    } catch {
      return null;
    }
  };

  const runPreview = () => {
    const changes = parseChanges();
    if (!changes) {
      setError(
        toQueryError(
          new Error("JSON de alterações inválido."),
          "Prévia indisponível.",
        ),
      );
      return;
    }
    setBusy(true);
    setError(null);
    previewChecklistRevision(templateId, versionId, changes)
      .then(setPreview)
      .catch((err: unknown) =>
        setError(toQueryError(err, "Falha ao pré-visualizar impacto.")),
      )
      .finally(() => setBusy(false));
  };

  const apply = () => {
    const changes = parseChanges();
    if (!changes || changes.length === 0) {
      setError(
        toQueryError(
          new Error("Informe ao menos uma alteração válida."),
          "Revisão não aplicada.",
        ),
      );
      return;
    }
    setBusy(true);
    setError(null);
    applyChecklistRevision(templateId, versionId, {
      reason: reason.trim(),
      expected_revision: expectedRevision,
      changes,
      idempotency_key: newIdemKey(),
    })
      .then((result) => {
        setFeedback(
          `Revisão ${result.revision_no} aplicada — ` +
            `sincronização ${result.sync_event_id} emitida.`,
        );
        setRevisions(null);
        setPreview(null);
        load();
        onChanged();
      })
      .catch((err: unknown) =>
        setError(toQueryError(err, "Falha ao aplicar revisão.")),
      )
      .finally(() => setBusy(false));
  };

  const revert = (revision: ChecklistRevision) => {
    setBusy(true);
    setError(null);
    revertChecklistRevision(templateId, versionId, revision.revision_id, {
      reason: `Reversão da revisão ${revision.revision_no}`,
      expected_revision: expectedRevision,
      idempotency_key: newIdemKey(),
    })
      .then(() => {
        setFeedback(`Revisão ${revision.revision_no} revertida.`);
        setRevisions(null);
        load();
        onChanged();
      })
      .catch((err: unknown) =>
        setError(toQueryError(err, "Falha ao reverter revisão.")),
      )
      .finally(() => setBusy(false));
  };

  const columns: DataTableColumn<ChecklistRevision>[] = [
    {
      key: "revision_no",
      header: "Revisão",
      className: "cf-table__col--compact",
      sortable: true,
      sortValue: (row) => row.revision_no,
      render: (row) => `R${row.revision_no}`,
    },
    {
      key: "reason",
      header: "Motivo",
      className: "cf-table__col--wrap",
      sortable: true,
      sortValue: (row) => row.reason,
      render: (row) => row.reason,
    },
    {
      key: "changes",
      header: "Alterações",
      className: "cf-table__col--compact",
      align: "right",
      sortable: true,
      sortValue: (row) => row.changes?.length ?? 0,
      render: (row) => row.changes?.length ?? "—",
    },
    {
      key: "reverts",
      header: "Compensa",
      headerHint: CF_HELP.checklistLive.revert,
      className: "cf-table__col--wrap",
      sortable: true,
      sortValue: (row) => row.reverts_revision_id ?? "",
      render: (row) =>
        row.reverts_revision_id ? "Revisão compensatória" : "—",
    },
    {
      key: "created_at",
      header: "Aplicada em",
      className: "cf-table__col--wrap",
      sortable: true,
      sortValue: (row) => row.created_at,
      render: (row) => formatDateTime(row.created_at),
    },
    {
      key: "actions",
      header: "",
      className: "cf-table__col--compact",
      render: (row) => (
        <CfActionButton
          type="button"
          variant="ghost"
          disabled={busy}
          title={CF_HELP.checklistLive.revert}
          onClick={() => revert(row)}
        >
          <History {...ICON_PROPS} />
          Reverter
        </CfActionButton>
      ),
    },
  ];

  return (
    <section
      aria-label="Revisões do checklist publicado"
      data-testid="checklist-revisions-section"
    >
      <DataTableSection<ChecklistRevision>
        title="Revisões"
        titleHint={CF_HELP.checklistLive.revisions}
        columns={columns}
        rows={revisions ?? []}
        rowKey={(row) => row.revision_id}
        loading={revisions === null}
        emptyMessage="Nenhuma revisão interna registrada."
        columnPreferencesKey="cf-checklist-live-revisions-columns"
        viewLayoutPreferencesKey="cf-checklist-live-revisions"
        renderCard={(row) => {
          const fields: DataRecordCardField[] = [
            {
              id: "applied",
              label: "Aplicada em",
              value: formatDateTime(row.created_at),
            },
            {
              id: "reason",
              label: "Motivo",
              value: row.reason,
            },
          ];
          return (
            <CfDataRecordCard
              title={`R${row.revision_no}`}
              fields={fields}
            />
          );
        }}
        getSearchText={(row) => `r${row.revision_no} ${row.reason}`}
      />
      {error ? (
        <CfQueryErrorBanner
          error={error}
          dataset="as revisões do checklist"
          onRetry={load}
        />
      ) : null}
      {feedback ? (
        <CfFeedbackMessage intent="success" title="Revisão aplicada">
          {feedback}
        </CfFeedbackMessage>
      ) : null}
      <div className="cf-live-revision-form" role="group"
        aria-label="Nova revisão em lote">
        <label className="cf-field">
          <span>Motivo</span>
          <input
            type="text"
            value={reason}
            maxLength={500}
            onChange={(event) => setReason(event.target.value)}
            aria-label="Motivo da revisão"
          />
        </label>
        <label className="cf-field">
          <span>
            Revisão esperada (OCC — vigente: {currentRevision})
          </span>
          <input
            type="number"
            min={1}
            value={expectedRevision}
            onChange={(event) =>
              setExpectedRevision(Number(event.target.value) || 1)
            }
            aria-label="Revisão esperada"
          />
        </label>
        <label className="cf-field">
          <span>
            Alterações (JSON — op, item_key, payload)
          </span>
          <textarea
            value={changesText}
            rows={5}
            onChange={(event) => setChangesText(event.target.value)}
            aria-label="Alterações da revisão em JSON"
            spellCheck={false}
          />
        </label>
        <div className="cf-live-actions">
          <CfActionButton
            type="button"
            variant="ghost"
            disabled={busy}
            onClick={runPreview}
          >
            Pré-visualizar impacto
          </CfActionButton>
          <CfActionButton
            type="button"
            variant="primary"
            disabled={busy || !reason.trim()}
            onClick={apply}
          >
            Aplicar revisão
          </CfActionButton>
        </div>
      </div>
      {preview ? (
        <CfFeedbackMessage
          intent="info"
          title="Prévia de impacto"
        >
          {`${preview.eligible_competences} competência(s) elegível(eis) ` +
            `— ${preview.affected_items.filter((i) => i.valid).length} ` +
            `alteração(ões) válida(s) de ` +
            `${preview.affected_items.length}.`}
        </CfFeedbackMessage>
      ) : null}
    </section>
  );
}

// -- Sincronização -------------------------------------------------------------

export function ChecklistSyncSection({
  templateId,
}: {
  templateId: string;
}) {
  const [runs, setRuns] = useState<ChecklistSyncRun[] | null>(null);
  const [error, setError] = useState<QueryError | null>(null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const requestId = useRef(0);

  const load = useCallback(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    listChecklistSyncRuns(templateId, undefined, {
      signal: controller.signal,
    })
      .then((items) => {
        if (controller.signal.aborted || requestId.current !== id)
          return;
        setRuns(items);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id)
          return;
        setError(toQueryError(err, "Falha ao listar sincronizações."));
      });
    return () => controller.abort();
  }, [templateId]);

  useEffect(() => load(), [load]);

  const retry = (run: ChecklistSyncRun) => {
    setBusy(true);
    setError(null);
    retryChecklistSyncEvent(templateId, run.event_id)
      .then((result) => {
        setFeedback(
          `${result.runs_reopened} run(s) reaberto(s) para ` +
            "reprocessamento.",
        );
        setRuns(null);
        load();
      })
      .catch((err: unknown) =>
        setError(toQueryError(err, "Falha ao reprocessar.")),
      )
      .finally(() => setBusy(false));
  };

  const columns: DataTableColumn<ChecklistSyncRun>[] = [
    {
      key: "state",
      header: "Estado",
      className: "cf-table__col--status",
      sortable: true,
      sortValue: (row) => row.state,
      render: (row) => (
        <CfStatusBadge
          label={RUN_STATE_LABELS[row.state] ?? row.state}
          variant={
            row.state === "APPLIED"
              ? "success"
              : row.state === "FAILED" || row.state === "PARTIAL"
                ? "danger"
                : "neutral"
          }
        />
      ),
    },
    {
      key: "competence",
      header: "Competência",
      className: "cf-table__col--compact",
      sortable: true,
      sortValue: (row) => row.competence_id,
      render: (row) => row.competence_id.slice(0, 8),
    },
    {
      key: "attempts",
      header: "Tentativas",
      className: "cf-table__col--compact",
      align: "right",
      sortable: true,
      sortValue: (row) => row.attempts,
      render: (row) => row.attempts,
    },
    {
      key: "skip_reason",
      header: "Exclusão",
      headerHint: CF_HELP.checklistLive.syncExclusions,
      className: "cf-table__col--wrap",
      sortable: true,
      sortValue: (row) => row.skip_reason ?? "",
      render: (row) => row.skip_reason ?? "—",
    },
    {
      key: "last_error",
      header: "Último erro",
      className: "cf-table__col--wrap",
      sortable: true,
      sortValue: (row) => row.last_error ?? "",
      render: (row) =>
        row.last_error ? row.last_error.slice(0, 80) : "—",
    },
    {
      key: "actions",
      header: "",
      className: "cf-table__col--compact",
      render: (row) =>
        row.state === "FAILED" || row.state === "PARTIAL" ? (
          <CfActionButton
            type="button"
            variant="ghost"
            disabled={busy}
            title={CF_HELP.checklistLive.syncRetry}
            onClick={() => retry(row)}
          >
            <RefreshCw {...ICON_PROPS} />
            Reprocessar
          </CfActionButton>
        ) : null,
    },
  ];

  return (
    <section
      aria-label="Sincronização do checklist"
      data-testid="checklist-sync-section"
    >
      <DataTableSection<ChecklistSyncRun>
        title="Sincronização"
        titleHint={CF_HELP.checklistLive.sync}
        columns={columns}
        rows={runs ?? []}
        rowKey={(row) => row.run_id}
        loading={runs === null}
        emptyMessage="Nenhuma execução de sincronização registrada."
        columnPreferencesKey="cf-checklist-live-sync-columns"
        viewLayoutPreferencesKey="cf-checklist-live-sync"
        renderCard={(row) => {
          const fields: DataRecordCardField[] = [
            {
              id: "state",
              label: "Estado",
              value:
                RUN_STATE_LABELS[row.state] ?? row.state,
            },
            {
              id: "attempts",
              label: "Tentativas",
              value: String(row.attempts),
            },
          ];
          return (
            <CfDataRecordCard
              title={row.competence_id.slice(0, 8)}
              fields={fields}
            />
          );
        }}
        getSearchText={(row) =>
          `${RUN_STATE_LABELS[row.state] ?? row.state} ` +
          `${row.skip_reason ?? ""}`
        }
      />
      {error ? (
        <CfQueryErrorBanner
          error={error}
          dataset="as execuções de sincronização"
          onRetry={load}
        />
      ) : null}
      {feedback ? (
        <CfFeedbackMessage
          intent="success"
          title="Reprocessamento solicitado"
        >
          {feedback}
        </CfFeedbackMessage>
      ) : null}
    </section>
  );
}
