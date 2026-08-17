import { useCallback, useEffect, useMemo, useState } from "react";

import {
  approveCapexInvestment,
  downloadCapexAttachment,
  getCapexReviewDetail,
  listActiveCapexCategories,
  listCapexInvestmentAttachments,
  listCapexPlanHistory,
  rejectCapexInvestment,
  requestCapexPlanChanges,
} from "../api/budgetPlanningApi";
import { getHttpErrorCode } from "../api/httpClient";
import type {
  CapexCategory,
  CapexInvestment,
  CapexInvestmentAttachment,
  CapexPlan,
  CapexPlanHistoryEntry,
} from "../types/budgetPlanning";
import { triggerBrowserDownload } from "../utils/capexAttachments";
import { formatMoneyBr, investmentReviewStatus } from "../utils/capexInvestments";
import {
  activeInvestments,
  formatDateTimeBr,
  isPlanVersionConflictError,
  mapCapexPlanError,
  planStatusLabel,
  planSubmitterDisplayName,
  sumEstimatedAmounts,
} from "../utils/capexPlans";
import { ApprovalDecisionPanel, type ApprovalDecisionKind } from "./ApprovalDecisionPanel";
import { CapexInvestmentReviewBoard } from "./CapexInvestmentReviewBoard";
import { CapexPlanHistoryTimeline } from "./CapexPlanHistoryTimeline";
import { LoadingActivityCard, SectionCard, StateBox } from "./uiKit";

type Props = {
  planId: string;
  embedded?: boolean;
  onDecided?: () => void;
};

export function CapexApprovalWorkspace({ planId, embedded = false, onDecided }: Props) {
  const [plan, setPlan] = useState<CapexPlan | null>(null);
  const [history, setHistory] = useState<CapexPlanHistoryEntry[]>([]);
  const [categories, setCategories] = useState<CapexCategory[]>([]);
  const [attachmentsByInv, setAttachmentsByInv] = useState<
    Record<string, CapexInvestmentAttachment[]>
  >({});
  const [loading, setLoading] = useState(true);
  const [deciding, setDeciding] = useState(false);
  const [decidingId, setDecidingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [versionConflict, setVersionConflict] = useState(false);
  const [comment, setComment] = useState("");
  const [commentError, setCommentError] = useState<string | null>(null);

  const investments = useMemo(
    () => activeInvestments(plan?.investments ?? []),
    [plan],
  );
  const totalAmount = useMemo(() => sumEstimatedAmounts(investments), [investments]);
  const pendingItems = investments.filter((row) => investmentReviewStatus(row) === "pending");
  const approvedItems = investments.filter((row) => investmentReviewStatus(row) === "approved");
  const rejectedItems = investments.filter((row) => investmentReviewStatus(row) === "rejected");
  const pendingCount = pendingItems.length;
  const approvedCount = approvedItems.length;
  const rejectedCount = rejectedItems.length;
  const pendingAmount = sumEstimatedAmounts(pendingItems);
  const approvedAmount = sumEstimatedAmounts(approvedItems);
  const categoryMap = useMemo(() => {
    const map = new Map<string, CapexCategory>();
    for (const c of categories) map.set(c.id, c);
    return map;
  }, [categories]);

  const canDecide = plan?.status === "submitted" && !versionConflict && !deciding;

  const load = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      setVersionConflict(false);
      try {
        const [detail, hist, cats] = await Promise.all([
          getCapexReviewDetail(planId, signal),
          listCapexPlanHistory(planId, signal),
          listActiveCapexCategories(signal),
        ]);
        if (signal?.aborted) return;
        setPlan(detail);
        setHistory(hist.items);
        setCategories(cats.items ?? []);
        const active = activeInvestments(detail.investments ?? []);
        const entries = await Promise.all(
          active.map(async (inv) => {
            try {
              const rows = await listCapexInvestmentAttachments(inv.id, signal);
              return [inv.id, rows] as const;
            } catch {
              return [inv.id, []] as const;
            }
          }),
        );
        if (signal?.aborted) return;
        setAttachmentsByInv(Object.fromEntries(entries));
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setError(mapCapexPlanError(err));
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

  function applyUpdatedPlan(updated: CapexPlan, message: string) {
    setPlan(updated);
    setSuccessMsg(message);
    onDecided?.();
  }

  async function refreshHistory(id: string) {
    const hist = await listCapexPlanHistory(id);
    setHistory(hist.items);
  }

  async function handleApproveInvestment(row: CapexInvestment) {
    if (!plan) return;
    setError(null);
    setSuccessMsg(null);
    setDeciding(true);
    setDecidingId(row.id);
    try {
      const updated = await approveCapexInvestment(plan.id, row.id, {
        version: plan.version,
      });
      const closed = updated.status !== "submitted";
      applyUpdatedPlan(
        updated,
        closed
          ? "Investimento aprovado. O planejamento foi encerrado com as decisões registradas."
          : "Investimento aprovado.",
      );
      await refreshHistory(plan.id);
    } catch (err: unknown) {
      if (isPlanVersionConflictError(err)) {
        setVersionConflict(true);
        setError(mapCapexPlanError(err));
      } else {
        setError(mapCapexPlanError(err));
      }
    } finally {
      setDeciding(false);
      setDecidingId(null);
    }
  }

  async function handleRejectInvestment(row: CapexInvestment, reviewComment: string) {
    if (!plan) return;
    setError(null);
    setSuccessMsg(null);
    setDeciding(true);
    setDecidingId(row.id);
    try {
      const updated = await rejectCapexInvestment(plan.id, row.id, {
        version: plan.version,
        comment: reviewComment,
      });
      const closed = updated.status !== "submitted";
      applyUpdatedPlan(
        updated,
        closed
          ? "Investimento reprovado. O planejamento foi encerrado com as decisões registradas."
          : "Investimento reprovado.",
      );
      await refreshHistory(plan.id);
    } catch (err: unknown) {
      if (isPlanVersionConflictError(err)) {
        setVersionConflict(true);
        setError(mapCapexPlanError(err));
      } else if (getHttpErrorCode(err) === "budget_capex_plan_comment_required") {
        setError(mapCapexPlanError(err));
      } else {
        setError(mapCapexPlanError(err));
      }
    } finally {
      setDeciding(false);
      setDecidingId(null);
    }
  }

  async function runDecision(kind: ApprovalDecisionKind) {
    if (!plan || kind !== "request_changes") return;
    setCommentError(null);
    setError(null);
    setSuccessMsg(null);
    if (!comment.trim()) {
      setCommentError("Comentário obrigatório para solicitar ajustes.");
      return;
    }
    setDeciding(true);
    try {
      const updated = await requestCapexPlanChanges(plan.id, {
        version: plan.version,
        comment: comment.trim(),
      });
      applyUpdatedPlan(updated, "Ajustes solicitados. O responsável poderá editar e reenviar.");
      setComment("");
      await refreshHistory(plan.id);
    } catch (err: unknown) {
      if (isPlanVersionConflictError(err)) {
        setVersionConflict(true);
        setError(mapCapexPlanError(err));
      } else if (getHttpErrorCode(err) === "budget_capex_plan_comment_required") {
        setCommentError(mapCapexPlanError(err));
      } else {
        setError(mapCapexPlanError(err));
      }
    } finally {
      setDeciding(false);
    }
  }

  async function handleDownload(attachment: CapexInvestmentAttachment) {
    try {
      const blob = await downloadCapexAttachment(attachment.id);
      triggerBrowserDownload(blob, attachment.original_filename || attachment.display_name);
    } catch (err: unknown) {
      setError(mapCapexPlanError(err));
    }
  }

  if (loading) {
    return <LoadingActivityCard title="Carregando CAPEX…" variant="panel" />;
  }

  if (!plan) {
    return (
      <StateBox variant="error" dismissible={false}>
        {error || "Planejamento CAPEX não encontrado."}
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

      <SectionCard title="Resumo CAPEX">
        <dl className="po-detail-grid">
          <div>
            <dt>Status do plano</dt>
            <dd>
              <span className="po-badge po-badge--muted">{planStatusLabel(plan.status)}</span>
            </dd>
          </div>
          <div>
            <dt>Responsável pelo envio</dt>
            <dd>{planSubmitterDisplayName(plan, history)}</dd>
          </div>
          <div>
            <dt>Submissão</dt>
            <dd>{formatDateTimeBr(plan.submitted_at)}</dd>
          </div>
          <div>
            <dt>Itens</dt>
            <dd>
              {approvedCount} aprovados · {pendingCount} pendentes · {rejectedCount} reprovados
            </dd>
          </div>
          <div>
            <dt>Valor solicitado</dt>
            <dd>{formatMoneyBr(totalAmount)}</dd>
          </div>
          <div>
            <dt>Já aprovado</dt>
            <dd>{formatMoneyBr(approvedAmount)}</dd>
          </div>
          <div>
            <dt>Ainda pendente</dt>
            <dd>{formatMoneyBr(pendingAmount)}</dd>
          </div>
          <div>
            <dt>Versão</dt>
            <dd>{plan.version}</dd>
          </div>
        </dl>
      </SectionCard>

      <CapexInvestmentReviewBoard
        investments={investments}
        categoryMap={categoryMap}
        attachmentsByInv={attachmentsByInv}
        canDecide={Boolean(canDecide)}
        decidingId={decidingId}
        onApprove={(row) => void handleApproveInvestment(row)}
        onReject={(row, reviewComment) => void handleRejectInvestment(row, reviewComment)}
        onDownload={(att) => void handleDownload(att)}
      />

      <ApprovalDecisionPanel
        title="Devolver o conjunto"
        hintWhenOpen="Use só se o centro inteiro precisa ser refeito. Aprovar e reprovar acontece em cada investimento acima."
        canDecide={Boolean(canDecide)}
        deciding={deciding}
        statusAllowsDecision={plan.status === "submitted"}
        statusLabel={planStatusLabel(plan.status)}
        comment={comment}
        commentError={commentError}
        onCommentChange={setComment}
        onDecide={(kind) => void runDecision(kind)}
        kinds={["request_changes"]}
      />

      <SectionCard title="Histórico CAPEX">
        <CapexPlanHistoryTimeline items={history} />
      </SectionCard>
    </>
  );

  if (embedded) {
    return <div className="po-workspace-section po-approval-module">{body}</div>;
  }
  return body;
}
