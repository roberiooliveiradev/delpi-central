import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, MapPin, Plus, Send } from "lucide-react";

import {
  listCapexInvestments,
  listCapexPlanHistory,
  resolveCapexPlan,
  submitCapexPlan,
} from "../api/budgetPlanningApi";
import type {
  BudgetExercise,
  CapexInvestment,
  CapexPlan,
  CapexPlanHistoryEntry,
  CapexPlanIncompleteInvestment,
} from "../types/budgetPlanning";
import { formatMoneyBr, missingFieldLabel } from "../utils/capexInvestments";
import {
  activeInvestments,
  canSubmitPlanStatus,
  extractIncompleteInvestments,
  formatDateTimeBr,
  incompleteInvestments,
  isPlanIncompleteError,
  isPlanVersionConflictError,
  mapCapexPlanError,
  planLockReason,
  planStatusLabel,
  sumEstimatedAmounts,
} from "../utils/capexPlans";
import { capexInvestmentHref, capexNewInvestmentHref } from "../utils/routing";
import { CapexPlanHistoryTimeline } from "./CapexPlanHistoryTimeline";
import { HostContainedDialog, LoadingActivityCard, SectionCard, StateBox } from "./uiKit";

type CapexPlanWorkflowPanelProps = {
  exercise: BudgetExercise;
  costCenterId: string;
  unitId?: string | null;
  areaId?: string | null;
  canSubmit: boolean;
  /** Layout enxuto para o cockpit do centro (default nas telas embutidas). */
  variant?: "classic" | "cockpit";
  /** Identidade do centro — funde hero + status num único banner (variant cockpit). */
  cockpitHero?: {
    title: string;
    locationLabel: string;
    cycleYear: string;
  } | null;
  onPlanChange?: (plan: CapexPlan | null) => void;
  onSubmitted?: () => void;
  onSummaryChange?: (summary: {
    activeCount: number;
    incompleteCount: number;
    totalAmount: string;
  }) => void;
  onRequestNewInvestment?: () => void;
  onRequestEditInvestment?: (investmentId: string) => void;
};

function statusBadgeClass(status?: string | null): string {
  switch (status) {
    case "approved":
      return "po-badge po-badge--success";
    case "rejected":
    case "changes_requested":
      return "po-badge po-badge--warning";
    case "submitted":
      return "po-badge po-badge--muted";
    default:
      return "po-badge po-badge--success";
  }
}

export function CapexPlanWorkflowPanel({
  exercise,
  costCenterId,
  unitId,
  areaId: _areaId,
  canSubmit,
  variant = "classic",
  cockpitHero = null,
  onPlanChange,
  onSubmitted,
  onSummaryChange,
  onRequestNewInvestment,
  onRequestEditInvestment,
}: CapexPlanWorkflowPanelProps) {
  const [plan, setPlan] = useState<CapexPlan | null>(null);
  const [history, setHistory] = useState<CapexPlanHistoryEntry[]>([]);
  const [summaryItems, setSummaryItems] = useState<CapexInvestment[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [incomplete, setIncomplete] = useState<CapexPlanIncompleteInvestment[]>([]);
  const [versionConflict, setVersionConflict] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [submitConfirmOpen, setSubmitConfirmOpen] = useState(false);

  const draftItems = useMemo(() => activeInvestments(summaryItems), [summaryItems]);
  const incompleteLocal = useMemo(() => incompleteInvestments(draftItems), [draftItems]);
  const totalAmount = useMemo(() => sumEstimatedAmounts(draftItems), [draftItems]);

  useEffect(() => {
    onSummaryChange?.({
      activeCount: draftItems.length,
      incompleteCount: incompleteLocal.length,
      totalAmount,
    });
  }, [draftItems.length, incompleteLocal.length, onSummaryChange, totalAmount]);

  const loadPlan = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      setVersionConflict(false);
      try {
        const [resolved, invResult] = await Promise.all([
          resolveCapexPlan(
            {
              exercise_id: exercise.id,
              cost_center_id: costCenterId,
              unit_id: unitId || undefined,
            },
            signal,
          ),
          listCapexInvestments(
            {
              exercise_id: exercise.id,
              cost_center_id: costCenterId,
              unit_id: unitId || undefined,
              status: "draft",
              page: 1,
              page_size: 500,
            },
            signal,
          ),
        ]);
        if (signal?.aborted) return;
        setPlan(resolved);
        onPlanChange?.(resolved);
        setSummaryItems(invResult.items);
        const hist = await listCapexPlanHistory(resolved.id, signal);
        if (signal?.aborted) return;
        setHistory(hist.items);
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setError(mapCapexPlanError(err));
        setPlan(null);
        onPlanChange?.(null);
        setHistory([]);
        setSummaryItems([]);
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [costCenterId, exercise.id, onPlanChange, unitId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void loadPlan(controller.signal);
    return () => controller.abort();
  }, [loadPlan]);

  const showSubmit =
    canSubmit && canSubmitPlanStatus(plan) && !loading && !versionConflict;
  const lockReason = planLockReason(plan);
  const newHref = capexNewInvestmentHref({
    costCenterId,
    unitId: unitId || undefined,
  });

  function openSubmitConfirm() {
    if (!plan || submitting) return;
    setSubmitConfirmOpen(true);
  }

  function closeSubmitConfirm() {
    if (submitting) return;
    setSubmitConfirmOpen(false);
  }

  async function handleSubmit() {
    if (!plan) return;

    setSubmitting(true);
    setError(null);
    setSuccessMsg(null);
    setIncomplete([]);
    try {
      const updated = await submitCapexPlan(plan.id, { version: plan.version });
      setSubmitConfirmOpen(false);
      setPlan(updated);
      onPlanChange?.(updated);
      setSuccessMsg("Enviado para aprovação. Edição bloqueada até a decisão.");
      const [hist, invResult] = await Promise.all([
        listCapexPlanHistory(updated.id),
        listCapexInvestments({
          exercise_id: exercise.id,
          cost_center_id: costCenterId,
          unit_id: unitId || undefined,
          status: "draft",
          page: 1,
          page_size: 500,
        }),
      ]);
      setHistory(hist.items);
      setSummaryItems(invResult.items);
      onSubmitted?.();
    } catch (err: unknown) {
      if (isPlanVersionConflictError(err)) {
        setVersionConflict(true);
        setError(mapCapexPlanError(err));
      } else if (isPlanIncompleteError(err)) {
        setIncomplete(extractIncompleteInvestments(err));
        setError(mapCapexPlanError(err));
      } else {
        setError(mapCapexPlanError(err));
      }
    } finally {
      setSubmitting(false);
    }
  }

  const nextStep = (() => {
    if (loading || !plan) return null;
    if (lockReason) {
      return { kind: "locked" as const, message: lockReason };
    }
    if (draftItems.length === 0) {
      return {
        kind: "empty" as const,
        title: "Comece cadastrando um investimento",
        href: onRequestNewInvestment ? undefined : newHref,
        onAction: onRequestNewInvestment,
        label: "Novo investimento",
      };
    }
    if (incompleteLocal.length > 0) {
      return {
        kind: "incomplete" as const,
        title: `Há ${incompleteLocal.length} investimento${
          incompleteLocal.length === 1 ? "" : "s"
        } incompleto${incompleteLocal.length === 1 ? "" : "s"}`,
        href: "#po-cockpit-investments",
        label: "Completar pendências",
      };
    }
    if (showSubmit) {
      return {
        kind: "ready" as const,
        title: "Tudo pronto para enviar",
        label: submitting ? "Enviando…" : "Enviar para aprovação",
      };
    }
    return null;
  })();

  const alerts = (
    <>
      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
          {versionConflict ? (
            <>
              {" "}
              <button
                type="button"
                className="po-btn po-btn--secondary po-btn--sm"
                onClick={() => void loadPlan()}
              >
                Recarregar dados
              </button>
            </>
          ) : null}
        </StateBox>
      ) : null}

      {successMsg ? (
        <StateBox variant="success" dismissible={false}>
          {successMsg}
        </StateBox>
      ) : null}

      {plan?.status === "changes_requested" && plan.decision_comment?.trim() ? (
        <StateBox variant="warning" dismissible={false}>
          <strong>Ajustes solicitados pelo aprovador</strong>
          <p className="po-cockpit-status__note">{plan.decision_comment}</p>
          <p className="po-muted">Edite os investimentos e reenvie quando estiver pronto.</p>
        </StateBox>
      ) : null}

      {incomplete.length > 0 ? (
        <StateBox variant="error" dismissible={false}>
          <strong>Investimentos incompletos</strong>
          <ul className="po-link-list" style={{ marginTop: 8 }}>
            {incomplete.map((row) => (
              <li key={String(row.id ?? row.description)}>
                {row.id ? (
                  onRequestEditInvestment ? (
                    <button
                      type="button"
                      className="po-link-button"
                      onClick={() => onRequestEditInvestment(row.id!)}
                    >
                      {row.description?.trim() || `Investimento ${row.id.slice(0, 8)}…`}
                    </button>
                  ) : (
                    <a href={capexInvestmentHref(row.id)}>
                      {row.description?.trim() || `Investimento ${row.id.slice(0, 8)}…`}
                    </a>
                  )
                ) : (
                  <span>{row.description?.trim() || "Investimento sem identificação"}</span>
                )}
                {row.missing_fields?.length ? (
                  <span className="po-muted">
                    {" "}
                    — pendências: {row.missing_fields.map(missingFieldLabel).join(", ")}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        </StateBox>
      ) : null}
    </>
  );

  const historyBlock = (
    <div className="po-cockpit-history">
      <button
        type="button"
        className="po-cockpit-history__toggle"
        aria-expanded={historyOpen}
        onClick={() => setHistoryOpen((v) => !v)}
      >
        <span>Ver histórico</span>
        <ChevronDown
          size={16}
          aria-hidden="true"
          className={historyOpen ? "is-open" : undefined}
        />
      </button>
      {historyOpen ? (
        <div className="po-cockpit-history__body">
          <CapexPlanHistoryTimeline items={history} />
        </div>
      ) : null}
    </div>
  );

  const submitConfirmDialog = (
    <HostContainedDialog
      open={submitConfirmOpen}
      title="Enviar para aprovação?"
      description="Confirme antes de bloquear a edição deste planejamento."
      onClose={closeSubmitConfirm}
      footer={
        <div className="po-form-actions">
          <button
            type="button"
            className="po-btn po-btn--secondary"
            disabled={submitting}
            onClick={closeSubmitConfirm}
          >
            Cancelar
          </button>
          <button
            type="button"
            className="po-btn po-btn--primary"
            disabled={submitting}
            onClick={() => void handleSubmit()}
          >
            <Send size={16} aria-hidden="true" />
            {submitting ? "Enviando…" : "Sim, enviar"}
          </button>
        </div>
      }
    >
      <div className="po-submit-confirm">
        <p className="po-submit-confirm__lead">
          Enviar o planejamento de investimentos deste centro para aprovação?
        </p>
        <dl className="po-submit-confirm__summary">
          <div>
            <dt>Investimentos</dt>
            <dd>{draftItems.length}</dd>
          </div>
          <div>
            <dt>Valor total</dt>
            <dd>{formatMoneyBr(totalAmount)}</dd>
          </div>
        </dl>
        <p className="po-muted po-submit-confirm__note">
          Após o envio, a edição ficará bloqueada durante a análise.
        </p>
      </div>
    </HostContainedDialog>
  );

  if (variant === "cockpit") {
    const heroYear = cockpitHero?.cycleYear || String(exercise.year);
    const heroTitle = cockpitHero?.title || "Investimentos";
    const heroLocation = cockpitHero?.locationLabel;

    return (
      <>
      <section
        className={`po-cockpit-status${cockpitHero ? " po-cockpit-status--banner" : ""}`}
        aria-label="Status do planejamento de investimentos"
      >
        {loading ? (
          <LoadingActivityCard title="Carregando status…" variant="panel" />
        ) : null}

        {alerts}

        {!loading && plan ? (
          <>
            <header className="po-cockpit-status__header">
              <div className="po-cockpit-status__heading">
                <p className="po-cockpit-status__eyebrow">Elaboração · {heroYear}</p>
                <h2 className="po-cockpit-status__title">{heroTitle}</h2>
                {cockpitHero ? (
                  <p className="po-cockpit-status__lead">
                    Cadastre os investimentos, complete as pendências e envie o conjunto para
                    aprovação neste centro.
                  </p>
                ) : null}
                <div className="po-cockpit-status__chips">
                  <span className="po-cockpit-status__chip">
                    <span className="po-cockpit-status__chip-label">Ciclo</span>
                    {heroYear}
                  </span>
                  {heroLocation ? (
                    <span className="po-cockpit-status__chip">
                      <span className="po-cockpit-status__chip-label">Local</span>
                      <MapPin size={13} aria-hidden="true" />
                      {heroLocation}
                    </span>
                  ) : null}
                  <span className={statusBadgeClass(plan.status)}>
                    {planStatusLabel(plan.status)}
                  </span>
                </div>
              </div>

              {nextStep && nextStep.kind !== "locked" ? (
                <div className="po-cockpit-status__actions">
                  {nextStep.kind !== "ready" ? (
                    <p className="po-cockpit-status__actions-hint">{nextStep.title}</p>
                  ) : null}
                  {nextStep.kind === "empty" ? (
                    nextStep.onAction ? (
                      <button
                        type="button"
                        className="po-btn po-btn--primary"
                        onClick={nextStep.onAction}
                      >
                        <Plus size={16} aria-hidden="true" />
                        {nextStep.label}
                      </button>
                    ) : nextStep.href ? (
                      <a className="po-btn po-btn--primary" href={nextStep.href}>
                        <Plus size={16} aria-hidden="true" />
                        {nextStep.label}
                      </a>
                    ) : null
                  ) : null}
                  {nextStep.kind === "incomplete" && nextStep.href ? (
                    <a className="po-btn po-btn--primary" href={nextStep.href}>
                      {nextStep.label}
                    </a>
                  ) : null}
                  {nextStep.kind === "ready" ? (
                    <button
                      type="button"
                      className="po-btn po-btn--primary"
                      disabled={submitting}
                      onClick={openSubmitConfirm}
                    >
                      <Send size={16} aria-hidden="true" />
                      {nextStep.label}
                    </button>
                  ) : null}
                </div>
              ) : null}
            </header>

            <div className="po-cockpit-status__metrics" role="group" aria-label="Resumo do planejamento">
              <div className="po-cockpit-status__metric">
                <span className="po-cockpit-status__metric-value">{draftItems.length}</span>
                <span className="po-cockpit-status__metric-label">Investimentos</span>
              </div>
              <div className="po-cockpit-status__metric">
                <span
                  className={`po-cockpit-status__metric-value${
                    incompleteLocal.length ? " is-warn" : ""
                  }`}
                >
                  {incompleteLocal.length}
                </span>
                <span className="po-cockpit-status__metric-label">Incompletos</span>
              </div>
              <div className="po-cockpit-status__metric po-cockpit-status__metric--wide">
                <span className="po-cockpit-status__metric-value">
                  {formatMoneyBr(totalAmount)}
                </span>
                <span className="po-cockpit-status__metric-label">Valor total</span>
              </div>
            </div>

            {nextStep?.kind === "locked" ? (
              <StateBox variant="warning" dismissible={false}>
                {nextStep.message}
              </StateBox>
            ) : null}

            {!canSubmit && canSubmitPlanStatus(plan) ? (
              <p className="po-muted po-cockpit-status__permission">
                Você não tem permissão para enviar este planejamento.
              </p>
            ) : null}

            {historyBlock}
          </>
        ) : null}
      </section>
      {submitConfirmDialog}
    </>
    );
  }

  return (
    <>
    <SectionCard
      title="Planejamento do centro de custo"
      hint="Aprovação ocorre sobre o conjunto de investimentos deste centro no exercício."
    >
      {loading ? (
        <LoadingActivityCard title="Carregando planejamento CAPEX…" variant="panel" />
      ) : null}

      {alerts}

      {lockReason ? (
        <StateBox variant="warning" dismissible={false}>
          {lockReason}
        </StateBox>
      ) : null}

      {!loading && plan ? (
        <>
          <dl className="po-detail-grid">
            <div>
              <dt>Exercício</dt>
              <dd>
                {exercise.year} — {exercise.name}
              </dd>
            </div>
            <div>
              <dt>Filial</dt>
              <dd>{plan.unit_id || unitId || "—"}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <span className={statusBadgeClass(plan.status)}>
                  {planStatusLabel(plan.status)}
                </span>
              </dd>
            </div>
            <div>
              <dt>Investimentos ativos</dt>
              <dd>{draftItems.length}</dd>
            </div>
            <div>
              <dt>Itens incompletos</dt>
              <dd>{incompleteLocal.length}</dd>
            </div>
            <div>
              <dt>Valor total</dt>
              <dd>{formatMoneyBr(totalAmount)}</dd>
            </div>
            <div>
              <dt>Última alteração</dt>
              <dd>{formatDateTimeBr(plan.updated_at)}</dd>
            </div>
            <div>
              <dt>Data de submissão</dt>
              <dd>{formatDateTimeBr(plan.submitted_at)}</dd>
            </div>
          </dl>

          <div className="po-form-actions" style={{ marginTop: 16 }}>
            {showSubmit ? (
              <button
                type="button"
                className="po-btn po-btn--primary"
                disabled={submitting}
                onClick={openSubmitConfirm}
              >
                <Send size={16} aria-hidden="true" />
                {submitting ? "Enviando…" : "Enviar planejamento para aprovação"}
              </button>
            ) : null}
            {!canSubmit && canSubmitPlanStatus(plan) ? (
              <p className="po-muted">
                Você não possui permissão para submeter o planejamento CAPEX.
              </p>
            ) : null}
          </div>

          <div style={{ marginTop: 20 }}>
            <h3 style={{ margin: "0 0 12px", fontSize: "1rem" }}>Histórico do workflow</h3>
            <CapexPlanHistoryTimeline items={history} />
          </div>
        </>
      ) : null}
    </SectionCard>
    {submitConfirmDialog}
    </>
  );
}
