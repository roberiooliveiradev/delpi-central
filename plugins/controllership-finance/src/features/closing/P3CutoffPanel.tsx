/**
 * P3 — cutoff humano, conciliação e readiness (B-β, docs 10/15.1).
 *
 * Readiness é derivada no backend — o painel apenas exibe estado,
 * blockers e proveniência, e dispara as ações governadas (`manage`):
 * confirmar cutoff, registrar resultado de source e revalidar.
 * Paridade tolerada: exatamente R$ 0,00. `STOCK_CLOSED` reflete somente
 * o estado canônico sincronizado pelo owner — nunca ação local.
 */
import { useCallback, useEffect, useState } from "react";

import { ActionButton } from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  confirmP3Cutoff,
  getP3State,
  revalidateP3,
  upsertP3Reconciliation,
  type P3Status,
  type Reconciliation,
  type ReconciliationDomain,
  type SourceState,
} from "../../api/p3Api";
import { useViewerCapabilities } from "../../app/ViewerContext";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  CfDialog,
  CfSectionCard,
  CfStatusBadge,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";

type PanelError = { status: number; code: string | null; message: string };

const ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Somente ator elegível (manage) governa cutoff e conciliação.",
  unauthorized: "Sessão expirada — autentique-se novamente.",
  competence_not_opened: "Competência não aberta.",
  cutoff_already_confirmed: "O cutoff já foi confirmado nesta competência.",
  cutoff_not_confirmed: "Confirme o cutoff antes de revalidar.",
  stale_revision: "Registro alterado por outra sessão — recarregue.",
  invalid_source_state: "Estado de source inválido.",
  invalid_reconciliation_domain: "Domínio de conciliação inválido.",
};

const STATE_LABELS: Record<P3Status["state"], string> = {
  WAITING_FOR_CUTOFF: "Aguardando cutoff",
  REVALIDATION_REQUIRED: "Revalidação necessária",
  READY_TO_CLOSE: "Pronto para fechar",
  STOCK_CLOSED: "Estoque fechado (ERP)",
};

const STATE_VARIANTS: Record<
  P3Status["state"],
  "warning" | "info" | "success" | "neutral"
> = {
  WAITING_FOR_CUTOFF: "warning",
  REVALIDATION_REQUIRED: "info",
  READY_TO_CLOSE: "success",
  STOCK_CLOSED: "neutral",
};

const DOMAIN_LABELS: Record<ReconciliationDomain, string> = {
  ENTRADAS_SAIDAS: "Entradas/Saídas",
  P7: "Inventário P7",
  H02: "Posição H02",
};

const SOURCE_STATE_LABELS: Record<SourceState, string> = {
  AVAILABLE: "Disponível",
  STALE: "Desatualizada",
  UNAVAILABLE: "Indisponível",
  PARTIAL: "Parcial",
  ERROR: "Erro",
};

const BLOCKER_LABELS: Record<string, string> = {
  cutoff_not_confirmed: "Cutoff ainda não confirmado",
  revalidation_required: "Revalidação pós-cutoff pendente ou expirada",
};

function blockerLabel(blocker: string): string {
  if (BLOCKER_LABELS[blocker]) return BLOCKER_LABELS[blocker];
  if (blocker.startsWith("source_unavailable:")) {
    const domain = blocker.split(":")[1] as ReconciliationDomain;
    return `Fonte indisponível — ${DOMAIN_LABELS[domain] ?? domain}`;
  }
  if (blocker.startsWith("divergence:")) {
    const domain = blocker.split(":")[1] as ReconciliationDomain;
    return `Divergência monetária — ${DOMAIN_LABELS[domain] ?? domain}`;
  }
  return blocker;
}

function mapError(error: unknown): PanelError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code ?? null,
      message: ERROR_MESSAGES[error.code ?? ""] ?? error.message,
    };
  }
  return {
    status: 0,
    code: null,
    message: "Falha de comunicação com a API.",
  };
}

function formatMoney(value: string | null): string {
  if (value === null || value === undefined) return "—";
  const parsed = Number(value);
  if (Number.isNaN(parsed)) return value;
  return parsed.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
  });
}

export function P3CutoffPanel({ period }: { period: string }) {
  const capabilities = useViewerCapabilities();
  const [status, setStatus] = useState<P3Status | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<PanelError | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [reconDialog, setReconDialog] =
    useState<ReconciliationDomain | null>(null);
  const [reconState, setReconState] = useState<SourceState>("AVAILABLE");
  const [expectedAmount, setExpectedAmount] = useState("");
  const [reportedAmount, setReportedAmount] = useState("");
  const [reconProvenance, setReconProvenance] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setStatus(await getP3State(period));
    } catch (err) {
      setError(mapError(err));
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function run(action: () => Promise<unknown>, okMessage: string) {
    setBusy(true);
    setError(null);
    setFeedback(null);
    try {
      await action();
      setFeedback(okMessage);
      await reload();
    } catch (err) {
      setError(mapError(err));
    } finally {
      setBusy(false);
    }
  }

  const onConfirmCutoff = () =>
    run(
      () => confirmP3Cutoff(period),
      "Cutoff confirmado e auditado.",
    );

  const onRevalidate = () =>
    run(
      () => revalidateP3(period),
      "Revalidação registrada na trilha.",
    );

  const onSubmitReconciliation = () =>
    run(async () => {
      if (!reconDialog) return;
      const domain = reconDialog;
      const provenance = reconProvenance.trim()
        ? { source: reconProvenance.trim(), registered_by: "portal" }
        : { source: "manual_confirmed", registered_by: "portal" };
      await upsertP3Reconciliation(period, domain, {
        sourceState: reconState,
        expectedAmount: expectedAmount.trim() || undefined,
        reportedAmount: reportedAmount.trim() || undefined,
        provenance,
      });
      setReconDialog(null);
    }, "Resultado da fonte registrado.");

  if (loading && !status) {
    return (
      <CfSectionCard title="Cutoff e conciliação (P3)">
        <p aria-live="polite">Carregando estado do fechamento…</p>
      </CfSectionCard>
    );
  }

  if (error && !status) {
    return (
      <CfSectionCard title="Cutoff e conciliação (P3)">
        <CfQueryErrorBanner
          error={error}
          dataset="o estado P3 da competência"
          onRetry={reload}
        />
      </CfSectionCard>
    );
  }

  if (!status) return null;

  const canManage = capabilities.manage;

  return (
    <CfSectionCard
      title="Cutoff e conciliação (P3)"
      hint={CF_HELP.p3.panel}
    >
      <div className="cf-p3-panel" aria-live="polite">
        <div className="cf-p3-status-row">
          <CfStatusBadge
            variant={STATE_VARIANTS[status.state]}
            label={STATE_LABELS[status.state]}
          />
          {status.cutoff ? (
            <span className="cf-p3-cutoff-info">
              Cutoff por {status.cutoff.confirmed_by} em{" "}
              {formatDateTime(status.cutoff.confirmed_at)}
            </span>
          ) : (
            <span className="cf-p3-cutoff-info">
              Nenhum cutoff confirmado — dados são preliminares.
            </span>
          )}
        </div>

        {status.blockers.length > 0 ? (
          <ul className="cf-p3-blockers" aria-label="Bloqueios de prontidão">
            {status.blockers.map((blocker) => (
              <li key={blocker}>{blockerLabel(blocker)}</li>
            ))}
          </ul>
        ) : null}

        <table className="cf-p3-table">
          <thead>
            <tr>
              <th>Fonte</th>
              <th>Estado</th>
              <th>Esperado</th>
              <th>Apurado</th>
              <th>Divergência</th>
              {canManage ? <th aria-label="Ações" /> : null}
            </tr>
          </thead>
          <tbody>
            {status.reconciliations.map((recon: Reconciliation) => (
              <tr key={recon.domain}>
                <td>{DOMAIN_LABELS[recon.domain]}</td>
                <td>{SOURCE_STATE_LABELS[recon.source_state]}</td>
                <td>{formatMoney(recon.expected_amount)}</td>
                <td>{formatMoney(recon.reported_amount)}</td>
                <td>{formatMoney(recon.divergence)}</td>
                {canManage ? (
                  <td>
                    <ActionButton
                      type="button"
                      onClick={() => setReconDialog(recon.domain)}
                      disabled={busy}
                    >
                      Registrar resultado
                    </ActionButton>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>

        {status.last_revalidation ? (
          <p className="cf-p3-revalidation">
            Última revalidação: {status.last_revalidation.result} por{" "}
            {status.last_revalidation.validated_by} em{" "}
            {formatDateTime(status.last_revalidation.validated_at)}
            {status.revalidation_valid
              ? " — vigente para os inputs atuais."
              : " — expirada: inputs mudaram."}
          </p>
        ) : (
          <p className="cf-p3-revalidation">
            Nenhuma revalidação pós-cutoff registrada.
          </p>
        )}

        {feedback ? (
          <CfFeedbackMessage intent="success" title="Ação registrada">
            {feedback}
          </CfFeedbackMessage>
        ) : null}
        {error ? (
          <CfFeedbackMessage intent="error" title="Falha na ação">
            {error.message}
          </CfFeedbackMessage>
        ) : null}

        {canManage ? (
          <div className="cf-p3-actions">
            {!status.cutoff ? (
              <ActionButton
                type="button"
                onClick={onConfirmCutoff}
                disabled={busy}
              >
                Confirmar cutoff
              </ActionButton>
            ) : null}
            {status.cutoff ? (
              <ActionButton
                type="button"
                onClick={onRevalidate}
                disabled={busy}
              >
                Revalidar fontes
              </ActionButton>
            ) : null}
          </div>
        ) : (
          <CfFeedbackMessage intent="info" title="Ações governadas">
            Cutoff, conciliação e revalidação exigem autorização de gestor
            do fechamento.
          </CfFeedbackMessage>
        )}
      </div>

      {reconDialog ? (
        <CfDialog
          open
          title={`Registrar resultado — ${DOMAIN_LABELS[reconDialog]}`}
          onClose={() => !busy && setReconDialog(null)}
          closeAriaLabel="Fechar registro de resultado"
        >
          <form
            className="cf-p3-recon-form"
            onSubmit={(event) => {
              event.preventDefault();
              void onSubmitReconciliation();
            }}
          >
            <label>
              Estado da fonte
              <select
                value={reconState}
                onChange={(event) =>
                  setReconState(event.target.value as SourceState)
                }
              >
                {(
                  [
                    "AVAILABLE",
                    "STALE",
                    "UNAVAILABLE",
                    "PARTIAL",
                    "ERROR",
                  ] as SourceState[]
                ).map((value) => (
                  <option key={value} value={value}>
                    {SOURCE_STATE_LABELS[value]}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Valor esperado (R$)
              <input
                type="text"
                inputMode="decimal"
                value={expectedAmount}
                onChange={(event) =>
                  setExpectedAmount(event.target.value)
                }
                placeholder="0.00"
              />
            </label>
            <label>
              Valor apurado (R$)
              <input
                type="text"
                inputMode="decimal"
                value={reportedAmount}
                onChange={(event) =>
                  setReportedAmount(event.target.value)
                }
                placeholder="0.00"
              />
            </label>
            <label>
              Proveniência
              <input
                type="text"
                value={reconProvenance}
                onChange={(event) =>
                  setReconProvenance(event.target.value)
                }
                placeholder="ex.: relatório oficial MATR460 conferido"
              />
            </label>
            <CfFeedbackMessage intent="info" title="Paridade exata">
              Fonte indisponível permanece explícita — nunca é convertida
              em zero. Paridade aceita: exatamente R$ 0,00.
            </CfFeedbackMessage>
            <div className="cf-p3-actions">
              <ActionButton type="submit" disabled={busy}>
                Registrar
              </ActionButton>
              <ActionButton
                type="button"
                onClick={() => setReconDialog(null)}
                disabled={busy}
              >
                Cancelar
              </ActionButton>
            </div>
          </form>
        </CfDialog>
      ) : null}
    </CfSectionCard>
  );
}
