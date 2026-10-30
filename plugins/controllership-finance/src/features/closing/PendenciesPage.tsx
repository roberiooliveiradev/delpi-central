/**
 * P4 — fila de pendências e classificações (B-α, doc 11).
 *
 * Máquina de estados fechada aplicada no backend: OPEN → IN_ANALYSIS /
 * WAITING_EXTERNAL → RESOLVED | DISMISSED. Claim/reatribuição mudam só
 * responsabilidade (histórico preservado). Sugestões determinísticas/IA
 * são exibidas como recomendação — nunca como decisão. DISMISSED exige
 * justificativa. Não há SLA inventado: mostramos apenas `pending_since`.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { ActionButton } from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  claimPendency,
  confirmPendencyClassification,
  listPendencies,
  listPendencyHistory,
  reassignPendency,
  transitionPendency,
  type Pendency,
  type PendencyHistoryEvent,
  type PendencyState,
} from "../../api/pendenciesApi";
import { useViewerCapabilities } from "../../app/ViewerContext";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
  CfSectionLoading,
} from "../../app/cfFeedbackUi";
import {
  CfDialog,
  CfEmptyState,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  FilterInputField,
  FiltersRow,
} from "../../app/cfFiltersUi";
import { ClosingHero } from "../../app/ClosingHero";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";

type PanelError = { status: number; code: string | null; message: string };

const PERIOD_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

const ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para esta ação.",
  unauthorized: "Sessão expirada — autentique-se novamente.",
  competence_not_opened: "Competência não aberta.",
  pendency_not_found: "Pendência fora do escopo desta competência ou filial.",
  pendency_terminal: "Pendência já encerrada — não admite mutação.",
  invalid_pendency_transition:
    "Transição não permitida para o estado atual.",
  missing_dismiss_justification:
    "Descarte exige justificativa registrada.",
  classification_already_confirmed:
    "Classificação já confirmada por um responsável.",
  stale_revision: "Pendência alterada por outra sessão — recarregue.",
  invalid_pendency_kind: "Tipo de pendência inválido.",
  invalid_pendency_state: "Estado inválido para a pendência.",
};

const STATE_LABELS: Record<PendencyState, string> = {
  OPEN: "Aberta",
  IN_ANALYSIS: "Em análise",
  WAITING_EXTERNAL: "Aguardando externo",
  RESOLVED: "Resolvida",
  DISMISSED: "Descartada",
};

const STATE_VARIANTS: Record<
  PendencyState,
  "warning" | "info" | "success" | "neutral" | "danger"
> = {
  OPEN: "warning",
  IN_ANALYSIS: "info",
  WAITING_EXTERNAL: "info",
  RESOLVED: "success",
  DISMISSED: "neutral",
};

const KIND_LABELS: Record<string, string> = {
  MISSING_EVIDENCE: "Evidência ausente",
  VALIDATION_REJECTED: "Evidência rejeitada",
  RECONCILIATION_DIVERGENCE: "Divergência de conciliação",
  STRUCTURAL_CORRECTION: "Correção estrutural",
  EXTERNAL_DEPENDENCY: "Dependência externa",
  OTHER: "Outra",
};

/** Transições do grafo fechado (espelho UX — backend é a autoridade). */
const NEXT_STATES: Record<PendencyState, PendencyState[]> = {
  OPEN: ["IN_ANALYSIS", "WAITING_EXTERNAL", "DISMISSED"],
  IN_ANALYSIS: ["WAITING_EXTERNAL", "RESOLVED", "DISMISSED"],
  WAITING_EXTERNAL: ["IN_ANALYSIS", "RESOLVED", "DISMISSED"],
  RESOLVED: [],
  DISMISSED: [],
};

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

function currentCompetence(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function pendingAge(createdAt: string): string {
  const created = new Date(createdAt).getTime();
  if (Number.isNaN(created)) return "—";
  const days = Math.floor((Date.now() - created) / 86400000);
  if (days <= 0) return "hoje";
  return days === 1 ? "há 1 dia" : `há ${days} dias`;
}

export function PendenciesPage() {
  const capabilities = useViewerCapabilities();
  const [period, setPeriod] = useState(currentCompetence());
  const [stateFilter, setStateFilter] = useState("");
  const [items, setItems] = useState<Pendency[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<PanelError | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [selected, setSelected] = useState<Pendency | null>(null);
  const [history, setHistory] = useState<PendencyHistoryEvent[]>([]);
  const [dismissFor, setDismissFor] = useState<Pendency | null>(null);
  const [dismissText, setDismissText] = useState("");
  const [reassignFor, setReassignFor] = useState<Pendency | null>(null);
  const [reassignTarget, setReassignTarget] = useState("");
  const [classifyFor, setClassifyFor] = useState<Pendency | null>(null);
  const [classifyValue, setClassifyValue] = useState("");
  const [classifyReason, setClassifyReason] = useState("");

  const periodValid = PERIOD_PATTERN.test(period);

  const reload = useCallback(async () => {
    if (!periodValid) return;
    setLoading(true);
    setError(null);
    try {
      const result = await listPendencies(period, {
        state: (stateFilter || undefined) as PendencyState | undefined,
      });
      setItems(result.items);
      setLastUpdated(new Date());
    } catch (err) {
      setError(mapError(err));
    } finally {
      setLoading(false);
    }
  }, [period, periodValid, stateFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const openHistory = useCallback(
    async (pendency: Pendency) => {
      setSelected(pendency);
      try {
        const detail = await listPendencyHistory(
          period,
          pendency.pendency_id,
        );
        setHistory(detail?.events ?? []);
      } catch {
        setHistory([]);
      }
    },
    [period],
  );

  async function run(action: () => Promise<unknown>, okMessage: string) {
    setBusy(true);
    setError(null);
    setFeedback(null);
    try {
      await action();
      setFeedback(okMessage);
      setSelected(null);
      setDismissFor(null);
      setReassignFor(null);
      setClassifyFor(null);
      await reload();
    } catch (err) {
      setError(mapError(err));
    } finally {
      setBusy(false);
    }
  }

  const actionsFor = useMemo(
    () =>
      (pendency: Pendency) => {
        const next = NEXT_STATES[pendency.state] ?? [];
        return (
          <div className="cf-pend-actions">
            {pendency.state === "OPEN" && !pendency.responsible_subject ? (
              <ActionButton
                type="button"
                onClick={() =>
                  run(
                    () =>
                      claimPendency(
                        period,
                        pendency.pendency_id,
                        pendency.revision,
                      ),
                    "Pendência assumida.",
                  )
                }
                disabled={busy}
              >
                Assumir
              </ActionButton>
            ) : null}
            {next
              .filter((target) => target !== "DISMISSED")
              .map((target) => (
                <ActionButton
                  key={target}
                  type="button"
                  onClick={() =>
                    run(
                      () =>
                        transitionPendency(period, pendency.pendency_id, {
                          toState: target,
                          revision: pendency.revision,
                        }),
                      `Pendência → ${STATE_LABELS[target]}.`,
                    )
                  }
                  disabled={busy}
                >
                  {STATE_LABELS[target]}
                </ActionButton>
              ))}
            {next.includes("DISMISSED") ? (
              <ActionButton
                type="button"
                onClick={() => {
                  setDismissFor(pendency);
                  setDismissText("");
                }}
                disabled={busy}
              >
                Descartar…
              </ActionButton>
            ) : null}
            {capabilities.manage &&
            pendency.state !== "RESOLVED" &&
            pendency.state !== "DISMISSED" ? (
              <>
                <ActionButton
                  type="button"
                  onClick={() => {
                    setReassignFor(pendency);
                    setReassignTarget("");
                  }}
                  disabled={busy}
                >
                  Reatribuir…
                </ActionButton>
                {!pendency.confirmed_classification ? (
                  <ActionButton
                    type="button"
                    onClick={() => {
                      setClassifyFor(pendency);
                      setClassifyValue(
                        pendency.suggested_classification ?? "",
                      );
                      setClassifyReason("");
                    }}
                    disabled={busy}
                  >
                    Confirmar classificação…
                  </ActionButton>
                ) : null}
              </>
            ) : null}
            <ActionButton
              type="button"
              onClick={() => void openHistory(pendency)}
              disabled={busy}
            >
              Histórico
            </ActionButton>
          </div>
        );
      },
    [period, busy, capabilities.manage, openHistory, reload],
  );

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Pendências do fechamento"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Pendências e classificações"
            hint={CF_HELP.pendencies.page}
          />
        }
        subtitle="Registro, triagem e tratamento governado das pendências da competência."
        filters={
          <form
            className="cf-settlements-filters"
            onSubmit={(event) => event.preventDefault()}
          >
            <FiltersRow>
              <FilterInputField
                id="cf-pend-period"
                label="Competência"
                type="month"
                value={period}
                onChange={setPeriod}
              />
              <FilterInputField
                id="cf-pend-state"
                label="Estado"
                type="text"
                value={stateFilter}
                onChange={setStateFilter}
                placeholder="OPEN, IN_ANALYSIS…"
              />
            </FiltersRow>
          </form>
        }
        updatedAt={lastUpdated}
        onRefresh={reload}
        refreshing={loading}
        onClearFilters={() => {
          setPeriod(currentCompetence());
          setStateFilter("");
        }}
      />

      <div className="cf-page-stack" aria-busy={loading}>
        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="as pendências da competência"
            onRetry={reload}
          />
        ) : null}
        {feedback ? (
          <CfFeedbackMessage intent="success" title="Ação registrada">
            {feedback}
          </CfFeedbackMessage>
        ) : null}

        <CfSectionCard title="Fila de pendências" hint={CF_HELP.pendencies.queue}>
          {loading && items.length === 0 ? (
            <CfSectionLoading label="Carregando pendências…" variant="panel" />
          ) : items.length === 0 ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Nenhuma pendência registrada para a competência e filtro atuais."
            />
          ) : (
            <table className="cf-pend-table">
              <thead>
                <tr>
                  <th>Pendência</th>
                  <th>Tipo</th>
                  <th>Estado</th>
                  <th>Responsável</th>
                  <th>Idade</th>
                  <th>Classificação</th>
                  <th aria-label="Ações" />
                </tr>
              </thead>
              <tbody>
                {items.map((pendency) => (
                  <tr key={pendency.pendency_id}>
                    <td>{pendency.title}</td>
                    <td>{KIND_LABELS[pendency.kind] ?? pendency.kind}</td>
                    <td>
                      <CfStatusBadge
                        variant={STATE_VARIANTS[pendency.state]}
                        label={STATE_LABELS[pendency.state]}
                      />
                    </td>
                    <td>{pendency.responsible_subject ?? "—"}</td>
                    <td>{pendingAge(pendency.created_at)}</td>
                    <td>
                      {pendency.confirmed_classification ? (
                        <span title={pendency.classification_reason ?? ""}>
                          {pendency.confirmed_classification} (confirmada)
                        </span>
                      ) : pendency.suggested_classification ? (
                        <span title={pendency.suggestion_rationale ?? ""}>
                          {pendency.suggested_classification} (sugestão
                          {pendency.suggestion_source === "AI"
                            ? " IA"
                            : pendency.suggestion_source === "DETERMINISTIC"
                              ? " automática"
                              : ""}
                          )
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>{actionsFor(pendency)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CfSectionCard>
      </div>

      {selected ? (
        <CfDialog
          open
          title={`Histórico — ${selected.title}`}
          onClose={() => setSelected(null)}
          closeAriaLabel="Fechar histórico"
        >
          {history.length === 0 ? (
            <p>Nenhum evento registrado.</p>
          ) : (
            <ul className="cf-pend-history">
              {history.map((event) => (
                <li key={event.event_id}>
                  <strong>{event.event_type}</strong> — {event.actor_subject}
                  {" em "}
                  {formatDateTime(event.created_at)}
                </li>
              ))}
            </ul>
          )}
        </CfDialog>
      ) : null}

      {dismissFor ? (
        <CfDialog
          open
          title={`Descartar — ${dismissFor.title}`}
          onClose={() => !busy && setDismissFor(null)}
          closeAriaLabel="Fechar descarte"
        >
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void run(
                () =>
                  transitionPendency(period, dismissFor.pendency_id, {
                    toState: "DISMISSED",
                    revision: dismissFor.revision,
                    justification: dismissText,
                  }),
                "Pendência descartada com justificativa.",
              );
            }}
          >
            <label>
              Justificativa (obrigatória)
              <textarea
                value={dismissText}
                onChange={(event) => setDismissText(event.target.value)}
                required
                rows={3}
              />
            </label>
            <div className="cf-pend-actions">
              <ActionButton type="submit" disabled={busy || !dismissText.trim()}>
                Confirmar descarte
              </ActionButton>
              <ActionButton
                type="button"
                onClick={() => setDismissFor(null)}
                disabled={busy}
              >
                Cancelar
              </ActionButton>
            </div>
          </form>
        </CfDialog>
      ) : null}

      {reassignFor ? (
        <CfDialog
          open
          title={`Reatribuir — ${reassignFor.title}`}
          onClose={() => !busy && setReassignFor(null)}
          closeAriaLabel="Fechar reatribuição"
        >
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void run(
                () =>
                  reassignPendency(
                    period,
                    reassignFor.pendency_id,
                    reassignTarget,
                    reassignFor.revision,
                  ),
                "Responsável atualizado — histórico preservado.",
              );
            }}
          >
            <label>
              Novo responsável (subject)
              <input
                type="text"
                value={reassignTarget}
                onChange={(event) => setReassignTarget(event.target.value)}
                required
              />
            </label>
            <div className="cf-pend-actions">
              <ActionButton
                type="submit"
                disabled={busy || !reassignTarget.trim()}
              >
                Reatribuir
              </ActionButton>
              <ActionButton
                type="button"
                onClick={() => setReassignFor(null)}
                disabled={busy}
              >
                Cancelar
              </ActionButton>
            </div>
          </form>
        </CfDialog>
      ) : null}

      {classifyFor ? (
        <CfDialog
          open
          title={`Confirmar classificação — ${classifyFor.title}`}
          onClose={() => !busy && setClassifyFor(null)}
          closeAriaLabel="Fechar classificação"
        >
          {classifyFor.suggested_classification ? (
            <CfFeedbackMessage intent="info" title="Sugestão não decide">
              Sugestão{classifyFor.suggestion_source === "AI" ? " de IA" : ""}:
              {" "}
              {classifyFor.suggested_classification} — é uma recomendação,
              não uma decisão. A confirmação humana é auditada.
            </CfFeedbackMessage>
          ) : null}
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void run(
                () =>
                  confirmPendencyClassification(
                    period,
                    classifyFor.pendency_id,
                    {
                      classification: classifyValue,
                      reason: classifyReason || undefined,
                      revision: classifyFor.revision,
                    },
                  ),
                "Classificação confirmada e auditada.",
              );
            }}
          >
            <label>
              Classificação
              <input
                type="text"
                value={classifyValue}
                onChange={(event) => setClassifyValue(event.target.value)}
                required
              />
            </label>
            <label>
              Motivo
              <input
                type="text"
                value={classifyReason}
                onChange={(event) => setClassifyReason(event.target.value)}
              />
            </label>
            <div className="cf-pend-actions">
              <ActionButton
                type="submit"
                disabled={busy || !classifyValue.trim()}
              >
                Confirmar
              </ActionButton>
              <ActionButton
                type="button"
                onClick={() => setClassifyFor(null)}
                disabled={busy}
              >
                Cancelar
              </ActionButton>
            </div>
          </form>
        </CfDialog>
      ) : null}
    </section>
  );
}
