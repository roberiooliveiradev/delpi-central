import { useCallback, useEffect, useState } from "react";
import { Check, ClipboardCheck, MessageSquareWarning, X } from "lucide-react";

import {
  approvePersonnelPlan,
  getPersonnelReviewDetail,
  listPersonnelPlanHistory,
  rejectPersonnelPlan,
  requestPersonnelPlanChanges,
} from "../api/budgetPlanningApi";
import { getHttpErrorCode } from "../api/httpClient";
import { PersonnelPlanHistoryTimeline } from "../components/PersonnelPlanHistoryTimeline";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import type {
  PersonnelPlan,
  PersonnelPlanHistoryEntry,
  PersonnelPlanLine,
} from "../types/budgetPlanning";
import { formatCostCenterLabel } from "../utils/orgCostCenters";
import {
  formatPersonnelDateTimeBr,
  HEADCOUNT_COLUMNS,
  isPersonnelPlanVersionConflictError,
  mapPersonnelError,
  personnelPlanStatusLabel,
} from "../utils/personnelPlans";
import { hasPersonnelApproveAccess } from "../utils/permissions";
import { pessoalApprovalsHref, resolvePersonnelPlanId } from "../utils/routing";

type PersonnelReviewDetailPageProps = {
  planId?: string | null;
  pathname?: string;
};

function ReadOnlyLinesTable({ lines }: { lines: PersonnelPlanLine[] }) {
  const active = lines.filter((ln) => ln.is_active !== false);
  if (!active.length) {
    return <p className="po-muted">Nenhuma linha ativa neste orçamento.</p>;
  }
  return (
    <div className="po-table-wrap">
      <table className="po-table">
        <thead>
          <tr>
            <th>Cargo</th>
            {HEADCOUNT_COLUMNS.map((col) => (
              <th key={col.field}>{col.label}</th>
            ))}
            <th>Observações</th>
          </tr>
        </thead>
        <tbody>
          {active.map((line) => (
            <tr key={line.id}>
              <td>{line.position_name}</td>
              {HEADCOUNT_COLUMNS.map((col) => (
                <td key={col.field}>{line[col.field] ?? "—"}</td>
              ))}
              <td>{line.observations?.trim() || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PersonnelReviewDetailPage({
  planId,
  pathname,
}: PersonnelReviewDetailPageProps) {
  const resolvedId = planId ?? resolvePersonnelPlanId(pathname);
  const { profile, loading: permLoading, error: permError } = usePermissions();
  const canApprove = hasPersonnelApproveAccess(profile);

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
      if (!resolvedId || !canApprove) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      setVersionConflict(false);
      try {
        const [detail, hist] = await Promise.all([
          getPersonnelReviewDetail(resolvedId, signal),
          listPersonnelPlanHistory(resolvedId, signal),
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
    [canApprove, resolvedId],
  );

  useEffect(() => {
    if (permLoading) return;
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load, permLoading]);

  async function runDecision(kind: "approve" | "request_changes" | "reject") {
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
          `Exercício: ${plan.exercise_id}`,
          "",
          "Após a aprovação, o plano permanece somente leitura.",
        ].join("\n"),
      );
      if (!ok) return;
    } else if (kind === "reject") {
      const ok = window.confirm(
        "Confirmar reprovação? O orçamento ficará somente leitura (não é solicitação de ajustes).",
      );
      if (!ok) return;
    } else {
      const ok = window.confirm(
        "Solicitar ajustes? O responsável poderá editar e reenviar o orçamento.",
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
    } catch (err: unknown) {
      if (isPersonnelPlanVersionConflictError(err)) {
        setVersionConflict(true);
        setError(mapPersonnelError(err));
      } else if (getHttpErrorCode(err) === "budget_personnel_plan_comment_required") {
        setCommentError(mapPersonnelError(err));
      } else if (getHttpErrorCode(err) === "budget_personnel_approval_forbidden") {
        setError(mapPersonnelError(err));
      } else {
        setError(mapPersonnelError(err));
      }
    } finally {
      setDeciding(false);
    }
  }

  if (permLoading || loading) {
    return (
      <PageShell
        title="Análise de Pessoal"
        subtitle="Revisão somente leitura do orçamento."
        icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
        backHref={pessoalApprovalsHref()}
      >
        <LoadingActivityCard title="Carregando orçamento…" variant="panel" />
      </PageShell>
    );
  }

  if (permError) {
    return (
      <PageShell title="Análise de Pessoal" backHref={pessoalApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          {permError}
        </StateBox>
      </PageShell>
    );
  }

  if (!canApprove) {
    return (
      <PageShell title="Análise de Pessoal" backHref={pessoalApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          Acesso negado (403). Sem permissão de aprovação de Pessoal.
        </StateBox>
      </PageShell>
    );
  }

  if (!resolvedId) {
    return (
      <PageShell title="Análise de Pessoal" backHref={pessoalApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          Identificador do planejamento ausente na URL.
        </StateBox>
      </PageShell>
    );
  }

  if (!plan) {
    return (
      <PageShell title="Análise de Pessoal" backHref={pessoalApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          {error || "Orçamento de Pessoal não encontrado."}
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Análise de Pessoal"
      subtitle="Somente leitura — decisões sobre o conjunto do centro de custo."
      icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
      backHref={pessoalApprovalsHref()}
    >
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
                onClick={() => void load()}
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

      <SectionCard title="Identificação do plano">
        <dl className="po-detail-grid">
          <div>
            <dt>Filial</dt>
            <dd>{plan.unit_id}</dd>
          </div>
          <div>
            <dt>Centro de custo</dt>
            <dd>
              {formatCostCenterLabel({
                branch: plan.branch ?? plan.unit_id,
                code: plan.cost_center_id,
              })}
            </dd>
          </div>
          <div>
            <dt>Área</dt>
            <dd>{plan.area_id || "—"}</dd>
          </div>
          <div>
            <dt>Exercício</dt>
            <dd>{plan.exercise_id}</dd>
          </div>
          <div>
            <dt>Responsável (envio)</dt>
            <dd>{plan.submitted_by || "—"}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{personnelPlanStatusLabel(plan.status)}</dd>
          </div>
          <div>
            <dt>Versão</dt>
            <dd>{plan.version}</dd>
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

      <SectionCard title="Linhas de headcount" hint="Visualização somente leitura.">
        <ReadOnlyLinesTable lines={plan.lines ?? []} />
        <dl className="po-detail-grid" style={{ marginTop: 16 }}>
          {HEADCOUNT_COLUMNS.map((col) => (
            <div key={col.field}>
              <dt>Total {col.label}</dt>
              <dd>{plan.totals?.[col.field] ?? 0}</dd>
            </div>
          ))}
        </dl>
      </SectionCard>

      {plan.status === "submitted" ? (
        <SectionCard title="Decisão">
          <label>
            Comentário / justificativa
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={4}
              disabled={!canDecide}
              aria-invalid={Boolean(commentError)}
              placeholder="Obrigatório para solicitar ajustes ou reprovar"
            />
          </label>
          {commentError ? (
            <StateBox variant="error" dismissible={false}>
              {commentError}
            </StateBox>
          ) : null}
          <div className="po-form-actions" style={{ marginTop: 12 }}>
            <button
              type="button"
              className="po-btn po-btn--secondary"
              disabled={!canDecide}
              onClick={() => void runDecision("request_changes")}
            >
              <MessageSquareWarning size={16} aria-hidden="true" />
              Solicitar ajustes
            </button>
            <button
              type="button"
              className="po-btn po-btn--danger"
              disabled={!canDecide}
              onClick={() => void runDecision("reject")}
            >
              <X size={16} aria-hidden="true" />
              Reprovar
            </button>
            <button
              type="button"
              className="po-btn po-btn--primary"
              disabled={!canDecide}
              onClick={() => void runDecision("approve")}
            >
              <Check size={16} aria-hidden="true" />
              Aprovar orçamento
            </button>
          </div>
        </SectionCard>
      ) : (
        <StateBox variant="default" dismissible={false}>
          Este orçamento não está aguardando decisão (status:{" "}
          {personnelPlanStatusLabel(plan.status)}).
        </StateBox>
      )}

      <SectionCard title="Histórico">
        <PersonnelPlanHistoryTimeline items={history} />
      </SectionCard>
    </PageShell>
  );
}
