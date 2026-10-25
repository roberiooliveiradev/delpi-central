/**
 * P5 — pacotes por destinatário, submissão in-portal, review por área e
 * conclusão mensal (docs 12/37; contrato C2).
 *
 * FINALIZE != ENVIAR: "Finalizar pacote" congela a PackageVersion;
 * "Enviar para análise" a disponibiliza dentro da Minha DELPI aos
 * revisores designados — nunca como anexo de e-mail. Aceites são por
 * área obrigatória da versão vigente e irreversíveis; nova versão exige
 * novos aceites. A conclusão mensal é derivada no backend — a página
 * apenas reflete o estado real (sem verde falso).
 */
import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { ActionButton } from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  confirmTerminalRejection,
  createPackageComplement,
  createReviewAssignment,
  deactivateReviewAssignment,
  finalizePackage,
  getMonthlyClosingState,
  getPackage,
  listPackages,
  openClarification,
  recordReviewDecision,
  reopenPackageVersion,
  resolveClarification,
  revertTerminalRejection,
  submitPackageForReview,
  type ClosingPackage,
  type MonthlyClosingState,
} from "../../api/packagesApi";
import { useViewerCapabilities } from "../../app/ViewerContext";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
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
  package_not_found: "Pacote fora do seu escopo de atribuição.",
  package_version_not_found: "Versão do pacote não encontrada.",
  invalid_package_transition:
    "Transição não permitida para o estado atual do pacote.",
  stale_revision: "Pacote alterado por outra sessão — recarregue.",
  missing_reason: "A ação exige motivo registrado.",
  reviewer_not_assigned:
    "Você não possui atribuição de revisor para este pacote/área.",
  area_decision_terminal:
    "O aceite desta área é irreversível nesta versão.",
  clarification_not_found: "Esclarecimento não encontrado.",
  terminal_rejection_active:
    "Competência com rejeição terminal ativa.",
  terminal_rejection_not_found: "Sem rejeição terminal ativa.",
  coordinator_required:
    "Rejeição terminal exige coordenador formal designado.",
  official_document_required:
    "Proveniência oficial exige artefato anexado na competência.",
};

const STATE_LABELS: Record<string, string> = {
  PACKAGE_INCOMPLETE: "Pacote incompleto",
  PACKAGE_FINALIZED: "Pacote finalizado",
  PACKAGE_SUBMITTED_FOR_REVIEW: "Enviado para análise",
};

const REVIEW_LABELS: Record<string, string> = {
  REVIEW_PENDING: "Aguardando análise",
  REVIEW_IN_PROGRESS: "Em análise",
  CHANGES_REQUESTED: "Ajustes solicitados",
  WAITING_FOR_CLARIFICATION: "Aguardando esclarecimento",
  CLARIFICATION_RESOLVED: "Esclarecimento resolvido",
  REVIEW_ACCEPTED: "Revisão aceita",
  REVIEW_REJECTED: "Revisão rejeitada",
};

const CLOSING_LABELS: Record<string, string> = {
  PENDING: "Fechamento pendente",
  MONTHLY_CLOSING_COMPLETED: "Fechamento mensal concluído",
  TERMINALLY_REJECTED: "Competência rejeitada (terminal)",
};

const BADGE_VARIANTS: Record<
  string,
  "warning" | "info" | "success" | "neutral" | "danger"
> = {
  PACKAGE_INCOMPLETE: "warning",
  PACKAGE_FINALIZED: "info",
  PACKAGE_SUBMITTED_FOR_REVIEW: "info",
  REVIEW_ACCEPTED: "success",
  REVIEW_REJECTED: "danger",
  MONTHLY_CLOSING_COMPLETED: "success",
  TERMINALLY_REJECTED: "danger",
  PENDING: "warning",
};

const AREA_LABELS: Record<string, string> = {
  CONTABIL: "Contábil",
  FISCAL: "Fiscal",
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

type ReasonDialogKind =
  | "reopen"
  | "complement"
  | "reject_terminal"
  | "revert_terminal";

export function PackagesPage() {
  const capabilities = useViewerCapabilities();
  const [period, setPeriod] = useState(currentCompetence());
  const [packages, setPackages] = useState<ClosingPackage[]>([]);
  const [closing, setClosing] = useState<MonthlyClosingState | null>(null);
  const [selected, setSelected] = useState<ClosingPackage | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<PanelError | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [reasonDialog, setReasonDialog] =
    useState<ReasonDialogKind | null>(null);
  const [reasonText, setReasonText] = useState("");
  const [decisionArea, setDecisionArea] = useState<string | null>(null);
  const [decisionOutcome, setDecisionOutcome] = useState<
    "ACCEPTED" | "CHANGES_REQUESTED" | "REJECTED" | null
  >(null);
  const [decisionNote, setDecisionNote] = useState("");
  const [clarifyOpen, setClarifyOpen] = useState(false);
  const [clarifyText, setClarifyText] = useState("");
  const [assignOpen, setAssignOpen] = useState(false);
  const [assignRole, setAssignRole] = useState<"REVIEWER" | "COORDINATOR">(
    "REVIEWER",
  );
  const [assignSubject, setAssignSubject] = useState("");
  const [assignArea, setAssignArea] = useState("");

  const periodValid = PERIOD_PATTERN.test(period);

  const reload = useCallback(async () => {
    if (!periodValid) return;
    setLoading(true);
    setError(null);
    try {
      const [list, closingState] = await Promise.all([
        listPackages(period),
        getMonthlyClosingState(period),
      ]);
      setPackages(list.packages);
      setClosing(closingState);
      if (selected?.package_id) {
        const detail = await getPackage(period, selected.package_id);
        setSelected(detail);
      }
      setLastUpdated(new Date());
    } catch (err) {
      setError(mapError(err));
    } finally {
      setLoading(false);
    }
  }, [period, periodValid, selected?.package_id]);

  useEffect(() => {
    void reload();
  }, [period]);

  const openDetail = useCallback(
    async (pkg: ClosingPackage) => {
      if (!pkg.package_id) {
        setSelected(pkg);
        return;
      }
      try {
        const detail = await getPackage(period, pkg.package_id);
        setSelected(detail ?? pkg);
      } catch (err) {
        setError(mapError(err));
      }
    },
    [period],
  );

  const runAction = useCallback(
    async (action: () => Promise<unknown>, message: string) => {
      setBusy(true);
      setFeedback(null);
      try {
        await action();
        setFeedback(message);
        await reload();
      } catch (err) {
        setError(mapError(err));
      } finally {
        setBusy(false);
      }
    },
    [reload],
  );

  const version = selected?.current_version ?? null;

  const submitReason = () => {
    if (!reasonText.trim() || !reasonDialog) return;
    const text = reasonText.trim();
    setReasonDialog(null);
    setReasonText("");
    if (reasonDialog === "reopen" && version) {
      void runAction(
        () => reopenPackageVersion(period, version.package_version_id, text),
        "Pacote reaberto — nova versão de trabalho criada.",
      );
    } else if (reasonDialog === "complement" && version) {
      void runAction(
        () =>
          createPackageComplement(
            period,
            version.package_version_id,
            text,
          ),
        "Complemento criado — nova versão em elaboração.",
      );
    } else if (reasonDialog === "reject_terminal") {
      void runAction(
        () => confirmTerminalRejection(period, text),
        "Rejeição terminal registrada.",
      );
    } else if (reasonDialog === "revert_terminal") {
      void runAction(
        () => revertTerminalRejection(period, text),
        "Rejeição terminal revertida.",
      );
    }
  };

  const submitDecision = () => {
    if (!version || !decisionArea || !decisionOutcome) return;
    void runAction(
      () =>
        recordReviewDecision(period, version.package_version_id, {
          area: decisionArea,
          outcome: decisionOutcome,
          note: decisionNote.trim() || undefined,
        }),
      "Decisão de revisão registrada.",
    );
    setDecisionArea(null);
    setDecisionOutcome(null);
    setDecisionNote("");
  };

  const submitClarification = () => {
    if (!version || !clarifyText.trim()) return;
    void runAction(
      () =>
        openClarification(period, version.package_version_id, {
          question: clarifyText.trim(),
        }),
      "Esclarecimento solicitado.",
    );
    setClarifyOpen(false);
    setClarifyText("");
  };

  const submitAssignment = () => {
    if (!assignSubject.trim() || !selected) return;
    void runAction(
      () =>
        createReviewAssignment(period, {
          role: assignRole,
          subject: assignSubject.trim(),
          recipientArea: selected.recipient_area,
          area: assignRole === "REVIEWER" ? assignArea.trim() : undefined,
        }),
      "Atribuição registrada.",
    );
    setAssignOpen(false);
    setAssignSubject("");
    setAssignArea("");
  };

  const manageActions = (pkg: ClosingPackage) => {
    const v = pkg.current_version;
    return (
      <span className="cf-actions-cell">
        {v === null || v.status === "DRAFT" ? (
          <ActionButton
            variant="primary"
            disabled={busy}
            onClick={() =>
              void runAction(
                () => finalizePackage(period, pkg.recipient_area),
                "Pacote finalizado — versão imutável criada.",
              )
            }
          >
            Finalizar pacote
          </ActionButton>
        ) : null}
        {v?.status === "FINALIZED" ? (
          <>
            <ActionButton
              variant="primary"
              disabled={busy}
              onClick={() =>
                void runAction(
                  () =>
                    submitPackageForReview(
                      period,
                      v.package_version_id,
                      v.revision,
                    ),
                  "Enviado para análise dentro da Minha DELPI.",
                )
              }
            >
              Enviar para análise
            </ActionButton>
            <ActionButton
              variant="ghost"
              disabled={busy}
              onClick={() => setReasonDialog("reopen")}
            >
              Reabrir
            </ActionButton>
          </>
        ) : null}
        {v?.status === "SUBMITTED" ? (
          <ActionButton
            variant="ghost"
            disabled={busy}
            onClick={() => setReasonDialog("complement")}
          >
            Criar complemento
          </ActionButton>
        ) : null}
      </span>
    );
  };

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Pacotes do fechamento"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Pacotes e revisão"
            hint={CF_HELP.packages.page}
          />
        }
        subtitle="Pacotes por destinatário, envio para análise e conclusão mensal — tudo dentro da Minha DELPI."
        filters={
          <form
            className="cf-settlements-filters"
            onSubmit={(event) => event.preventDefault()}
          >
            <FiltersRow>
              <FilterInputField
                id="cf-pkg-period"
                label="Competência"
                type="month"
                value={period}
                onChange={setPeriod}
              />
            </FiltersRow>
          </form>
        }
        updatedAt={lastUpdated}
        onRefresh={reload}
        refreshing={loading}
        onClearFilters={() => setPeriod(currentCompetence())}
      />

      <div className="cf-page-stack" aria-busy={loading}>
        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="os pacotes da competência"
            onRetry={reload}
          />
        ) : null}
        {feedback ? (
          <CfFeedbackMessage intent="success" title="Ação registrada">
            {feedback}
          </CfFeedbackMessage>
        ) : null}

        {closing ? (
          <CfSectionCard
            title="Estado do fechamento mensal"
            hint={CF_HELP.packages.closing}
          >
            <p>
              <CfStatusBadge
                variant={BADGE_VARIANTS[closing.state] ?? "neutral"}
                label={CLOSING_LABELS[closing.state] ?? closing.state}
              />
            </p>
            {closing.blocking_reasons.length > 0 ? (
              <ul className="cf-blockers-list">
                {closing.blocking_reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            ) : null}
            {capabilities.manage &&
            closing.state !== "TERMINALLY_REJECTED" ? (
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setReasonDialog("reject_terminal")}
              >
                Registrar rejeição terminal
              </ActionButton>
            ) : null}
            {capabilities.manage &&
            closing.state === "TERMINALLY_REJECTED" ? (
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setReasonDialog("revert_terminal")}
              >
                Reverter rejeição terminal
              </ActionButton>
            ) : null}
          </CfSectionCard>
        ) : null}

        <CfSectionCard
          title="Pacotes por destinatário"
          hint={CF_HELP.packages.list}
        >
          {loading && packages.length === 0 ? (
            <p aria-live="polite">Carregando pacotes…</p>
          ) : packages.length === 0 ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Nenhum pacote visível para esta competência e o seu escopo."
            />
          ) : (
            <table className="cf-pend-table">
              <thead>
                <tr>
                  <th>Destinatário</th>
                  <th>Estado</th>
                  <th>Revisão</th>
                  <th>Versão</th>
                  <th aria-label="Ações" />
                </tr>
              </thead>
              <tbody>
                {packages.map((pkg) => (
                  <tr key={pkg.recipient_area}>
                    <td>{AREA_LABELS[pkg.recipient_area] ?? pkg.recipient_area}</td>
                    <td>
                      <CfStatusBadge
                        variant={BADGE_VARIANTS[pkg.state] ?? "neutral"}
                        label={STATE_LABELS[pkg.state] ?? pkg.state}
                      />
                    </td>
                    <td>
                      <CfStatusBadge
                        variant={
                          BADGE_VARIANTS[pkg.review_state] ?? "neutral"
                        }
                        label={
                          REVIEW_LABELS[pkg.review_state] ??
                          pkg.review_state
                        }
                      />
                    </td>
                    <td>
                      {pkg.current_version
                        ? `v${pkg.current_version.version_no}`
                        : "—"}
                    </td>
                    <td>
                      <ActionButton
                        variant="ghost"
                        onClick={() => void openDetail(pkg)}
                      >
                        Detalhes
                      </ActionButton>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CfSectionCard>

        {selected ? (
          <CfSectionCard
            title={`Pacote — ${
              AREA_LABELS[selected.recipient_area] ??
              selected.recipient_area
            }`}
            hint={CF_HELP.packages.detail}
          >
            {selected.blockers && selected.blockers.length > 0 ? (
              <ul className="cf-blockers-list">
                {selected.blockers.map((blocker) => (
                  <li key={blocker}>{blocker}</li>
                ))}
              </ul>
            ) : null}
            {capabilities.manage ? manageActions(selected) : null}
            {selected.required_areas.length > 0 ? (
              <p>
                Áreas obrigatórias da versão vigente:{" "}
                {selected.required_areas.join(", ")}
              </p>
            ) : null}
            {Object.keys(selected.area_decisions).length > 0 ? (
              <ul className="cf-decisions-list">
                {Object.values(selected.area_decisions).map((d) => (
                  <li key={d.decision_id}>
                    {d.area}: {d.outcome}
                    {d.note ? ` — ${d.note}` : ""} (
                    {formatDateTime(d.created_at)})
                  </li>
                ))}
              </ul>
            ) : null}
            {version?.status === "SUBMITTED" ? (
              <>
                <CfSectionCard
                  title="Revisão"
                  hint={CF_HELP.packages.review}
                >
                  {selected.assignments
                    .filter((a) => a.active)
                    .map((a) => (
                      <p key={a.assignment_id}>
                        {a.role} {a.area ? `— ${a.area}` : ""}{" "}
                        {capabilities.manage ? (
                          <ActionButton
                            variant="ghost"
                            disabled={busy}
                            onClick={() =>
                              void runAction(
                                () =>
                                  deactivateReviewAssignment(
                                    period,
                                    a.assignment_id,
                                    "reatribuição",
                                  ),
                                "Atribuição desativada.",
                              )
                            }
                          >
                            Desativar
                          </ActionButton>
                        ) : null}
                      </p>
                    ))}
                  {capabilities.manage ? (
                    <ActionButton
                      variant="ghost"
                      onClick={() => setAssignOpen(true)}
                    >
                      Atribuir revisor/coordenador…
                    </ActionButton>
                  ) : null}
                  {(selected.required_areas.length > 0 ||
                    selected.assignments.length > 0) && (
                    <div className="cf-decision-form">
                      <select
                        aria-label="Área da decisão"
                        value={decisionArea ?? ""}
                        onChange={(e) =>
                          setDecisionArea(e.target.value || null)
                        }
                      >
                        <option value="">Selecione a área…</option>
                        {selected.required_areas.map((a) => (
                          <option key={a} value={a}>
                            {a}
                          </option>
                        ))}
                      </select>
                      <select
                        aria-label="Resultado da revisão"
                        value={decisionOutcome ?? ""}
                        onChange={(e) =>
                          setDecisionOutcome(
                            (e.target.value || null) as
                              | "ACCEPTED"
                              | "CHANGES_REQUESTED"
                              | "REJECTED"
                              | null,
                          )
                        }
                      >
                        <option value="">Resultado…</option>
                        <option value="ACCEPTED">Aceitar</option>
                        <option value="CHANGES_REQUESTED">
                          Solicitar ajustes
                        </option>
                        <option value="REJECTED">Rejeitar</option>
                      </select>
                      <input
                        aria-label="Motivo da decisão"
                        placeholder="Motivo (obrigatório para ajustes/rejeição)"
                        value={decisionNote}
                        onChange={(e) => setDecisionNote(e.target.value)}
                      />
                      <ActionButton
                        variant="primary"
                        disabled={
                          busy || !decisionArea || !decisionOutcome
                        }
                        onClick={submitDecision}
                      >
                        Registrar decisão
                      </ActionButton>
                      <ActionButton
                        variant="ghost"
                        disabled={busy}
                        onClick={() => setClarifyOpen(true)}
                      >
                        Solicitar esclarecimento…
                      </ActionButton>
                    </div>
                  )}
                  {selected.versions?.some((v) =>
                    v.clarifications.length > 0,
                  ) ? (
                    <ul className="cf-clarifications-list">
                      {selected.versions
                        ?.flatMap((v) => v.clarifications)
                        .map((c) => (
                          <li key={c.clarification_id}>
                            {c.state}: {c.question}
                            {c.response ? ` → ${c.response}` : ""}
                            {c.state === "OPEN" &&
                            capabilities.manage ? (
                              <ActionButton
                                variant="ghost"
                                disabled={busy}
                                onClick={() =>
                                  void runAction(
                                    () =>
                                      resolveClarification(
                                        period,
                                        c.clarification_id,
                                        "Resposta registrada pela Controladoria.",
                                      ),
                                    "Esclarecimento resolvido.",
                                  )
                                }
                              >
                                Resolver
                              </ActionButton>
                            ) : null}
                          </li>
                        ))}
                    </ul>
                  ) : null}
                </CfSectionCard>
              </>
            ) : null}
            {selected.versions && selected.versions.length > 1 ? (
              <details>
                <summary>Histórico de versões</summary>
                <ul>
                  {selected.versions.map((v) => (
                    <li key={v.package_version_id}>
                      v{v.version_no} — {v.status}
                      {v.submitted_at
                        ? ` (enviada em ${formatDateTime(v.submitted_at)})`
                        : ""}
                      {v.change_reason ? ` — ${v.change_reason}` : ""}
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}
          </CfSectionCard>
        ) : null}
      </div>

      {reasonDialog ? (
        <CfDialog
          open
          title="Motivo obrigatório"
          onClose={() => setReasonDialog(null)}
          closeAriaLabel="Cancelar"
        >
          <label htmlFor="cf-reason-input">Motivo</label>
          <input
            id="cf-reason-input"
            value={reasonText}
            onChange={(e) => setReasonText(e.target.value)}
          />
          <ActionButton
            variant="primary"
            disabled={!reasonText.trim() || busy}
            onClick={submitReason}
          >
            Confirmar
          </ActionButton>
        </CfDialog>
      ) : null}

      {clarifyOpen ? (
        <CfDialog
          open
          title="Solicitar esclarecimento"
          onClose={() => setClarifyOpen(false)}
          closeAriaLabel="Cancelar"
        >
          <label htmlFor="cf-clarify-input">Pergunta</label>
          <input
            id="cf-clarify-input"
            value={clarifyText}
            onChange={(e) => setClarifyText(e.target.value)}
          />
          <ActionButton
            variant="primary"
            disabled={!clarifyText.trim() || busy}
            onClick={submitClarification}
          >
            Enviar
          </ActionButton>
        </CfDialog>
      ) : null}

      {assignOpen ? (
        <CfDialog
          open
          title="Atribuir revisor ou coordenador"
          onClose={() => setAssignOpen(false)}
          closeAriaLabel="Cancelar"
        >
          <label htmlFor="cf-assign-role">Papel</label>
          <select
            id="cf-assign-role"
            value={assignRole}
            onChange={(e) =>
              setAssignRole(e.target.value as "REVIEWER" | "COORDINATOR")
            }
          >
            <option value="REVIEWER">Revisor</option>
            <option value="COORDINATOR">Coordenador</option>
          </select>
          <label htmlFor="cf-assign-subject">Identidade Core (UUID)</label>
          <input
            id="cf-assign-subject"
            value={assignSubject}
            onChange={(e) => setAssignSubject(e.target.value)}
          />
          {assignRole === "REVIEWER" ? (
            <>
              <label htmlFor="cf-assign-area">Área</label>
              <input
                id="cf-assign-area"
                value={assignArea}
                onChange={(e) => setAssignArea(e.target.value)}
              />
            </>
          ) : null}
          <ActionButton
            variant="primary"
            disabled={!assignSubject.trim() || busy}
            onClick={submitAssignment}
          >
            Atribuir
          </ActionButton>
        </CfDialog>
      ) : null}
    </section>
  );
}
