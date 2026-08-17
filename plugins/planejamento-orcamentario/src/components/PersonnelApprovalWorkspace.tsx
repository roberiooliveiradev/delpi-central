import { useCallback, useEffect, useState } from "react";

import {
  approvePersonnelPlan,
  getPersonnelReviewDetail,
  listPersonnelPlanHistory,
  rejectPersonnelPlan,
  requestPersonnelPlanChanges,
} from "../api/budgetPlanningApi";
import { getHttpErrorCode } from "../api/httpClient";
import type {
  PersonnelPlan,
  PersonnelPlanHistoryEntry,
} from "../types/budgetPlanning";
import { formatCostCenterLabel } from "../utils/orgCostCenters";
import { planSubmitterDisplayName } from "../utils/capexPlans";
import {
  formatPersonnelDateTimeBr,
  isPersonnelPlanVersionConflictError,
  mapPersonnelError,
  personnelPlanStatusLabel,
} from "../utils/personnelPlans";
import { ApprovalDecisionPanel, type ApprovalDecisionKind } from "./ApprovalDecisionPanel";
import { PersonnelLinesReadOnly } from "./PersonnelLinesReadOnly";
import { PersonnelPlanHistoryTimeline } from "./PersonnelPlanHistoryTimeline";
import { LoadingActivityCard, SectionCard, StateBox } from "./uiKit";

type Props = {
  planId: string;
  embedded?: boolean;
  onDecided?: () => void;
};

export function PersonnelApprovalWorkspace({
  planId,
  embedded = false,
  onDecided,
}: Props) {
  const [plan, setPlan] = useState<PersonnelPlan | null>(null);
  const [history, setHistory] = useState<PersonnelPlanHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [deciding, setDeciding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [versionConflict, setVersionConflict] = useState(false);
  const [comment, setComment] = useState("");
  const [commentError, setCommentError] = useState<string | null>(null);

  const canDecide = plan?.status === "submitted" && !versionConflict && !deciding;

  const load = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      setVersionConflict(false);
      try {
        const [detail, hist] = await Promise.all([
          getPersonnelReviewDetail(planId, signal),
          listPersonnelPlanHistory(planId, signal),
        ]);
        if (signal?.aborted) return;
        setPlan(detail);
        setHistory(hist.items);
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setError(mapPersonnelError(err));
        setPlan(null);
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [planId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  async function runDecision(kind: ApprovalDecisionKind) {
    if (!plan) return;
    setCommentError(null);
    setError(null);
    setSuccessMsg(null);

    if (kind === "request_changes" || kind === "reject") {
      if (!comment.trim()) {
        setCommentError(
          kind === "reject"
            ? "Justificativa obrigatória para reprovar."
            : "Comentário obrigatório para solicitar ajustes.",
        );
        return;
      }
    }

    if (kind === "approve") {
      const ok = window.confirm(
        [
          "Aprovar este Orçamento de Pessoal?",
          "",
          `Filial: ${plan.unit_id}`,
          `Centro de custo: ${plan.cost_center_id}`,
          "",
          "Após a aprovação, o plano permanece somente leitura.",
        ].join("\n"),
      );
      if (!ok) return;
    } else if (kind === "reject") {
      const ok = window.confirm(
        "Confirmar reprovação? O orçamento ficará somente leitura.",
      );
      if (!ok) return;
    } else {
      const ok = window.confirm(
        "Solicitar ajustes? O responsável poderá editar e reenviar.",
      );
      if (!ok) return;
    }

    setDeciding(true);
    try {
      let updated: PersonnelPlan;
      if (kind === "approve") {
        updated = await approvePersonnelPlan(plan.id, {
          version: plan.version,
          comment: comment.trim() || null,
        });
        setSuccessMsg("Orçamento de Pessoal aprovado.");
      } else if (kind === "request_changes") {
        updated = await requestPersonnelPlanChanges(plan.id, {
          version: plan.version,
          comment: comment.trim(),
        });
        setSuccessMsg(
          "Ajustes solicitados. O responsável poderá editar e reenviar.",
        );
      } else {
        updated = await rejectPersonnelPlan(plan.id, {
          version: plan.version,
          comment: comment.trim(),
        });
        setSuccessMsg(
          "Orçamento reprovado. O registro permanece somente leitura.",
        );
      }
      setPlan(updated);
      setComment("");
      const hist = await listPersonnelPlanHistory(plan.id);
      setHistory(hist.items);
      onDecided?.();
    } catch (err: unknown) {
      if (isPersonnelPlanVersionConflictError(err)) {
        setVersionConflict(true);
        setError(mapPersonnelError(err));
      } else if (getHttpErrorCode(err) === "budget_personnel_plan_comment_required") {
        setCommentError(mapPersonnelError(err));
      } else {
        setError(mapPersonnelError(err));
      }
    } finally {
      setDeciding(false);
    }
  }

  if (loading) {
    return <LoadingActivityCard title="Carregando Pessoal…" variant="panel" />;
  }

  if (!plan) {
    return (
      <StateBox variant="error" dismissible={false}>
        {error || "Orçamento de Pessoal não encontrado."}
      </StateBox>
    );
  }

  const body = (
    <>
      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
          {versionConflict ? (
            <>
              {" "}
              <button type="button" className="po-btn po-btn--secondary" onClick={() => void load()}>
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

      <SectionCard title="Resumo Pessoal">
        <dl className="po-detail-grid">
          <div>
            <dt>Status</dt>
            <dd>
              <span className="po-badge po-badge--muted">
                {personnelPlanStatusLabel(plan.status)}
              </span>
            </dd>
          </div>
          <div>
            <dt>Centro</dt>
            <dd>
              {formatCostCenterLabel({
                branch: plan.branch ?? plan.unit_id,
                code: plan.cost_center_id,
              })}
            </dd>
          </div>
          <div>
            <dt>Responsável (envio)</dt>
            <dd>{planSubmitterDisplayName(plan, history)}</dd>
          </div>
          <div>
            <dt>Submissão</dt>
            <dd>{formatPersonnelDateTimeBr(plan.submitted_at)}</dd>
          </div>
          <div>
            <dt>Cargos</dt>
            <dd>{plan.position_count}</dd>
          </div>
          <div>
            <dt>Total Dez/2027</dt>
            <dd>{plan.totals?.headcount_dec_2027 ?? 0}</dd>
          </div>
        </dl>
      </SectionCard>

      <PersonnelLinesReadOnly lines={plan.lines ?? []} totals={plan.totals} />

      <ApprovalDecisionPanel
        title="Decisão Pessoal"
        canDecide={Boolean(canDecide)}
        deciding={deciding}
        statusAllowsDecision={plan.status === "submitted"}
        statusLabel={personnelPlanStatusLabel(plan.status)}
        comment={comment}
        commentError={commentError}
        onCommentChange={setComment}
        onDecide={(kind) => void runDecision(kind)}
        approveLabel="Aprovar orçamento"
      />

      <SectionCard title="Histórico Pessoal">
        <PersonnelPlanHistoryTimeline items={history} />
      </SectionCard>
    </>
  );

  if (embedded) {
    return <div className="po-workspace-section po-approval-module">{body}</div>;
  }
  return body;
}
