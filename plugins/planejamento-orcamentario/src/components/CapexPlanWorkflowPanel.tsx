import { useCallback, useEffect, useMemo, useState } from "react";
import { Send } from "lucide-react";

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
import { formatCostCenterLabel } from "../utils/orgCostCenters";
import { capexInvestmentHref } from "../utils/routing";
import { CapexPlanHistoryTimeline } from "./CapexPlanHistoryTimeline";
import { LoadingActivityCard, SectionCard, StateBox } from "./uiKit";

type CapexPlanWorkflowPanelProps = {
  exercise: BudgetExercise;
  costCenterId: string;
  unitId?: string | null;
  areaId?: string | null;
  canSubmit: boolean;
  onPlanChange?: (plan: CapexPlan | null) => void;
  onSubmitted?: () => void;
};

export function CapexPlanWorkflowPanel({
  exercise,
  costCenterId,
  unitId,
  areaId,
  canSubmit,
  onPlanChange,
  onSubmitted,
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

  const draftItems = useMemo(() => activeInvestments(summaryItems), [summaryItems]);
  const incompleteLocal = useMemo(() => incompleteInvestments(draftItems), [draftItems]);
  const totalAmount = useMemo(() => sumEstimatedAmounts(draftItems), [draftItems]);

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

  async function handleSubmit() {
    if (!plan) return;
    const confirmed = window.confirm(
      [
        `Enviar o planejamento do centro de custo ${costCenterId} para aprovação?`,
        "",
        `Investimentos ativos: ${draftItems.length}`,
        `Valor total: ${formatMoneyBr(totalAmount)}`,
        "",
        "Após o envio, a edição ficará bloqueada durante a análise.",
      ].join("\n"),
    );
    if (!confirmed) return;

    setSubmitting(true);
    setError(null);
    setSuccessMsg(null);
    setIncomplete([]);
    try {
      const updated = await submitCapexPlan(plan.id, { version: plan.version });
      setPlan(updated);
      onPlanChange?.(updated);
      setSuccessMsg("Planejamento enviado para aprovação. Edição bloqueada até a decisão.");
      const [hist, invResult] = await Promise.all([
        listCapexPlanHistory(updated.id),
        listCapexInvestments({
          exercise_id: exercise.id,
          cost_center_id: costCenterId,
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

  return (
    <SectionCard
      title="Planejamento do centro de custo"
      hint="Aprovação ocorre sobre o conjunto de investimentos deste centro no exercício."
    >
      {loading ? (
        <LoadingActivityCard title="Carregando planejamento CAPEX…" variant="panel" />
      ) : null}

      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
          {versionConflict ? (
            <>
              {" "}
              <button
                type="button"
                className="po-btn po-btn--secondary"
                style={{ marginLeft: 8 }}
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
          <p style={{ margin: "8px 0 0" }}>{plan.decision_comment}</p>
          <p className="po-muted" style={{ marginTop: 8 }}>
            Você pode editar os investimentos e reenviar o planejamento.
          </p>
        </StateBox>
      ) : null}

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
              <dt>Área</dt>
              <dd>{plan.area_id || areaId || "—"}</dd>
            </div>
            <div>
              <dt>Centro de custo</dt>
              <dd>
                {formatCostCenterLabel({
                  branch: plan.branch ?? plan.unit_id ?? unitId,
                  code: plan.cost_center_id,
                })}
              </dd>
            </div>
            <div>
              <dt>Status do planejamento</dt>
              <dd>
                <span
                  className={`po-badge ${
                    plan.status === "approved"
                      ? "po-badge--success"
                      : plan.status === "rejected" || plan.status === "changes_requested"
                        ? "po-badge--warning"
                        : plan.status === "submitted"
                          ? "po-badge--muted"
                          : "po-badge--success"
                  }`}
                >
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
            <div>
              <dt>Comentário da última decisão</dt>
              <dd>{plan.decision_comment?.trim() || "—"}</dd>
            </div>
          </dl>

          {incomplete.length > 0 ? (
            <StateBox variant="error" dismissible={false}>
              <strong>Investimentos incompletos</strong>
              <ul className="po-link-list" style={{ marginTop: 8 }}>
                {incomplete.map((row) => (
                  <li key={String(row.id ?? row.description)}>
                    {row.id ? (
                      <a href={capexInvestmentHref(row.id)}>
                        {row.description?.trim() || `Investimento ${row.id.slice(0, 8)}…`}
                      </a>
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

          <div className="po-form-actions" style={{ marginTop: 16 }}>
            {showSubmit ? (
              <button
                type="button"
                className="po-btn po-btn--primary"
                disabled={submitting}
                onClick={() => void handleSubmit()}
              >
                <Send size={16} aria-hidden="true" />
                {submitting
                  ? "Enviando…"
                  : "Enviar planejamento para aprovação"}
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
  );
}
