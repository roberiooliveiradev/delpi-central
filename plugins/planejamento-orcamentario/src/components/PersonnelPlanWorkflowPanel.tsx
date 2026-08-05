import { useCallback, useEffect, useState } from "react";
import { Send } from "lucide-react";

import {
  listPersonnelPlanHistory,
  resolvePersonnelPlan,
  submitPersonnelPlan,
} from "../api/budgetPlanningApi";
import type {
  BudgetExercise,
  PersonnelPlan,
  PersonnelPlanHistoryEntry,
  PersonnelPlanIncompleteLine,
} from "../types/budgetPlanning";
import { formatCostCenterLabel } from "../utils/orgCostCenters";
import {
  canSubmitPersonnelPlanStatus,
  extractIncompletePersonnelLines,
  formatPersonnelDateTimeBr,
  headcountFieldLabel,
  isPersonnelPlanIncompleteError,
  isPersonnelPlanVersionConflictError,
  mapPersonnelError,
  personnelPlanLockReason,
  personnelPlanStatusLabel,
} from "../utils/personnelPlans";
import { PersonnelPlanHistoryTimeline } from "./PersonnelPlanHistoryTimeline";
import { LoadingActivityCard, SectionCard, StateBox } from "./uiKit";

type PersonnelPlanWorkflowPanelProps = {
  exercise: BudgetExercise;
  costCenterId: string;
  unitId: string;
  areaId?: string | null;
  canSubmit: boolean;
  /** Autosave ou mutação de linha em andamento — bloqueia envio. */
  hasPendingLineWork?: boolean;
  onPlanChange?: (plan: PersonnelPlan | null) => void;
  onSubmitted?: (plan: PersonnelPlan) => void;
  /** Foco em linha incompleta na grade. */
  onFocusLine?: (lineId: string) => void;
};

export function PersonnelPlanWorkflowPanel({
  exercise,
  costCenterId,
  unitId,
  areaId,
  canSubmit,
  hasPendingLineWork = false,
  onPlanChange,
  onSubmitted,
  onFocusLine,
}: PersonnelPlanWorkflowPanelProps) {
  const [plan, setPlan] = useState<PersonnelPlan | null>(null);
  const [history, setHistory] = useState<PersonnelPlanHistoryEntry[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [incomplete, setIncomplete] = useState<PersonnelPlanIncompleteLine[]>([]);
  const [versionConflict, setVersionConflict] = useState(false);

  const loadPlan = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      setHistoryError(null);
      setVersionConflict(false);
      try {
        const resolved = await resolvePersonnelPlan(
          {
            exercise_id: exercise.id,
            cost_center_id: costCenterId,
            unit_id: unitId,
          },
          signal,
        );
        if (signal?.aborted) return;
        setPlan(resolved);
        onPlanChange?.(resolved);
        try {
          const hist = await listPersonnelPlanHistory(resolved.id, signal);
          if (signal?.aborted) return;
          setHistory(hist.items);
        } catch (histErr: unknown) {
          if (signal?.aborted) return;
          setHistory([]);
          setHistoryError(mapPersonnelError(histErr));
        }
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setError(mapPersonnelError(err));
        setPlan(null);
        onPlanChange?.(null);
        setHistory([]);
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
    canSubmit &&
    canSubmitPersonnelPlanStatus(plan) &&
    Boolean(plan) &&
    !loading &&
    !versionConflict &&
    !hasPendingLineWork &&
    !submitting;
  const lockReason = personnelPlanLockReason(plan);

  async function handleSubmit() {
    if (!plan) return;
    const confirmed = window.confirm(
      [
        `Enviar o Orçamento de Pessoal do centro ${costCenterId} (filial ${unitId}) para aprovação?`,
        "",
        `Exercício: ${exercise.year} — ${exercise.name}`,
        `Cargos ativos: ${plan.position_count}`,
        `Linhas incompletas: ${plan.incomplete_line_count}`,
        `Dez/2027 (total): ${plan.totals?.headcount_dec_2027 ?? 0}`,
        "",
        "Após o envio, a edição das linhas ficará bloqueada durante a análise.",
      ].join("\n"),
    );
    if (!confirmed) return;

    setSubmitting(true);
    setError(null);
    setSuccessMsg(null);
    setIncomplete([]);
    try {
      const updated = await submitPersonnelPlan(plan.id, { version: plan.version });
      setPlan(updated);
      onPlanChange?.(updated);
      setSuccessMsg(
        "Orçamento enviado para aprovação. A grade está em somente leitura até a decisão.",
      );
      try {
        const hist = await listPersonnelPlanHistory(updated.id);
        setHistory(hist.items);
        setHistoryError(null);
      } catch (histErr: unknown) {
        setHistoryError(mapPersonnelError(histErr));
      }
      onSubmitted?.(updated);
    } catch (err: unknown) {
      if (isPersonnelPlanVersionConflictError(err)) {
        setVersionConflict(true);
        setError(mapPersonnelError(err));
      } else if (isPersonnelPlanIncompleteError(err)) {
        setIncomplete(extractIncompletePersonnelLines(err));
        setError(mapPersonnelError(err));
      } else {
        setError(mapPersonnelError(err));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <SectionCard
      title="Workflow do Orçamento de Pessoal"
      hint="A aprovação ocorre sobre o conjunto de cargos deste centro de custo no exercício."
    >
      {loading ? (
        <LoadingActivityCard title="Carregando workflow de Pessoal…" variant="panel" />
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

      {plan?.status === "changes_requested" ? (
        <StateBox variant="warning" dismissible={false}>
          <strong>Ajustes solicitados pelo aprovador</strong>
          {plan.decision_comment?.trim() ? (
            <p style={{ margin: "8px 0 0" }}>{plan.decision_comment}</p>
          ) : null}
          <p className="po-muted" style={{ marginTop: 8 }}>
            Decisão em {formatPersonnelDateTimeBr(plan.reviewed_at)}
            {plan.reviewed_by ? ` por ${plan.reviewed_by}` : ""}. Corrija as linhas e
            reenvie o orçamento.
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
              <dd>{plan.unit_id || unitId}</dd>
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
              <dt>Status</dt>
              <dd>
                <span
                  className={`po-badge ${
                    plan.status === "approved"
                      ? "po-badge--success"
                      : plan.status === "rejected" ||
                          plan.status === "changes_requested"
                        ? "po-badge--warning"
                        : plan.status === "submitted"
                          ? "po-badge--muted"
                          : "po-badge--success"
                  }`}
                >
                  {personnelPlanStatusLabel(plan.status)}
                </span>
              </dd>
            </div>
            <div>
              <dt>Versão</dt>
              <dd>{plan.version}</dd>
            </div>
            <div>
              <dt>Cargos ativos</dt>
              <dd>{plan.position_count}</dd>
            </div>
            <div>
              <dt>Linhas incompletas</dt>
              <dd>{plan.incomplete_line_count}</dd>
            </div>
            <div>
              <dt>Total Dez/2025</dt>
              <dd>{plan.totals?.headcount_dec_2025 ?? 0}</dd>
            </div>
            <div>
              <dt>Total Out/2026</dt>
              <dd>{plan.totals?.headcount_oct_2026 ?? 0}</dd>
            </div>
            <div>
              <dt>Total Previsto</dt>
              <dd>{plan.totals?.headcount_forecast ?? 0}</dd>
            </div>
            <div>
              <dt>Total Dez/2027</dt>
              <dd>{plan.totals?.headcount_dec_2027 ?? 0}</dd>
            </div>
            <div>
              <dt>Submissão</dt>
              <dd>
                {formatPersonnelDateTimeBr(plan.submitted_at)}
                {plan.submitted_by ? ` · ${plan.submitted_by}` : ""}
              </dd>
            </div>
            <div>
              <dt>Decisão</dt>
              <dd>
                {formatPersonnelDateTimeBr(plan.reviewed_at)}
                {plan.reviewed_by ? ` · ${plan.reviewed_by}` : ""}
              </dd>
            </div>
            <div>
              <dt>Comentário da decisão</dt>
              <dd>{plan.decision_comment?.trim() || "—"}</dd>
            </div>
          </dl>

          {incomplete.length > 0 ? (
            <StateBox variant="error" dismissible={false}>
              <strong>Linhas incompletas</strong>
              <ul className="po-link-list" style={{ marginTop: 8 }}>
                {incomplete.map((row) => (
                  <li key={String(row.id ?? row.position_name)}>
                    {row.id && onFocusLine ? (
                      <button
                        type="button"
                        className="po-btn po-btn--secondary"
                        style={{ padding: "2px 8px", fontSize: "0.9rem" }}
                        onClick={() => onFocusLine(row.id!)}
                      >
                        {row.position_name?.trim() || `Linha ${String(row.id).slice(0, 8)}…`}
                      </button>
                    ) : (
                      <span>
                        {row.position_name?.trim() || "Cargo sem identificação"}
                      </span>
                    )}
                    {row.missing_fields?.length ? (
                      <span className="po-muted">
                        {" "}
                        — pendências:{" "}
                        {row.missing_fields.map(headcountFieldLabel).join(", ")}
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
                disabled={submitting || hasPendingLineWork}
                onClick={() => void handleSubmit()}
              >
                <Send size={16} aria-hidden="true" />
                {submitting ? "Enviando…" : "Enviar para aprovação"}
              </button>
            ) : null}
            {hasPendingLineWork && canSubmitPersonnelPlanStatus(plan) ? (
              <p className="po-muted">
                Aguarde o salvamento das linhas antes de enviar.
              </p>
            ) : null}
            {!canSubmit && canSubmitPersonnelPlanStatus(plan) ? (
              <p className="po-muted">
                Você não possui permissão para submeter o Orçamento de Pessoal.
              </p>
            ) : null}
          </div>

          <div style={{ marginTop: 20 }}>
            <h3 style={{ margin: "0 0 12px", fontSize: "1rem" }}>Histórico do workflow</h3>
            {historyError ? (
              <StateBox variant="warning" dismissible={false}>
                Não foi possível carregar o histórico: {historyError}
              </StateBox>
            ) : (
              <PersonnelPlanHistoryTimeline items={history} />
            )}
          </div>
        </>
      ) : null}
    </SectionCard>
  );
}
