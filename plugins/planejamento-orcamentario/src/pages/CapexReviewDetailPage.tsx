import { useCallback, useEffect, useMemo, useState } from "react";
import { Check, ClipboardCheck, MessageSquareWarning, X } from "lucide-react";

import {
  approveCapexPlan,
  getCapexReviewDetail,
  listActiveCapexCategories,
  listCapexInvestmentAttachments,
  listCapexPlanHistory,
  rejectCapexPlan,
  requestCapexPlanChanges,
  downloadCapexAttachment,
} from "../api/budgetPlanningApi";
import { CapexPlanHistoryTimeline } from "../components/CapexPlanHistoryTimeline";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import type {
  CapexCategory,
  CapexInvestment,
  CapexInvestmentAttachment,
  CapexPlan,
  CapexPlanHistoryEntry,
} from "../types/budgetPlanning";
import {
  formatMoneyBr,
  originLabel,
  priorityLabel,
} from "../utils/capexInvestments";
import { attachmentTypeLabel, triggerBrowserDownload } from "../utils/capexAttachments";
import {
  activeInvestments,
  formatDateTimeBr,
  isPlanVersionConflictError,
  mapCapexPlanError,
  planStatusLabel,
  sumEstimatedAmounts,
} from "../utils/capexPlans";
import { formatDateBr } from "../utils/responsibilities";
import { hasCapexApproveAccess } from "../utils/permissions";
import { capexApprovalsHref, resolveCapexPlanId } from "../utils/routing";
import { getHttpErrorCode } from "../api/httpClient";

type CapexReviewDetailPageProps = {
  planId?: string | null;
  pathname?: string;
};

export function CapexReviewDetailPage({ planId, pathname }: CapexReviewDetailPageProps) {
  const resolvedId = planId ?? resolveCapexPlanId(pathname);
  const { profile, loading: permLoading, error: permError } = usePermissions();
  const canApprove = hasCapexApproveAccess(profile);

  const [plan, setPlan] = useState<CapexPlan | null>(null);
  const [history, setHistory] = useState<CapexPlanHistoryEntry[]>([]);
  const [categories, setCategories] = useState<CapexCategory[]>([]);
  const [attachmentsByInv, setAttachmentsByInv] = useState<
    Record<string, CapexInvestmentAttachment[]>
  >({});
  const [loading, setLoading] = useState(true);
  const [deciding, setDeciding] = useState(false);
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
  const categoryMap = useMemo(() => {
    const map = new Map<string, CapexCategory>();
    for (const c of categories) map.set(c.id, c);
    return map;
  }, [categories]);

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
        const [detail, hist, cats] = await Promise.all([
          getCapexReviewDetail(resolvedId, signal),
          listCapexPlanHistory(resolvedId, signal),
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
    [canApprove, resolvedId],
  );

  useEffect(() => {
    if (permLoading) return;
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load, permLoading]);

  async function runDecision(
    kind: "approve" | "request_changes" | "reject",
  ) {
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
        `Aprovar o planejamento do centro ${plan.cost_center_id}? Após a aprovação, o conjunto fica bloqueado.`,
      );
      if (!ok) return;
    }

    setDeciding(true);
    try {
      let updated: CapexPlan;
      if (kind === "approve") {
        updated = await approveCapexPlan(plan.id, {
          version: plan.version,
          comment: comment.trim() || null,
        });
        setSuccessMsg("Planejamento aprovado.");
      } else if (kind === "request_changes") {
        updated = await requestCapexPlanChanges(plan.id, {
          version: plan.version,
          comment: comment.trim(),
        });
        setSuccessMsg("Ajustes solicitados. O responsável poderá editar e reenviar.");
      } else {
        updated = await rejectCapexPlan(plan.id, {
          version: plan.version,
          comment: comment.trim(),
        });
        setSuccessMsg("Planejamento reprovado. O registro permanece somente leitura.");
      }
      setPlan((prev) => ({ ...updated, investments: prev?.investments }));
      setComment("");
      const hist = await listCapexPlanHistory(plan.id);
      setHistory(hist.items);
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

  if (permLoading || loading) {
    return (
      <PageShell
        title="Análise CAPEX"
        subtitle="Revisão somente leitura do planejamento."
        icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
        backHref={capexApprovalsHref()}
      >
        <LoadingActivityCard title="Carregando planejamento…" variant="panel" />
      </PageShell>
    );
  }

  if (permError) {
    return (
      <PageShell title="Análise CAPEX" backHref={capexApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          {permError}
        </StateBox>
      </PageShell>
    );
  }

  if (!canApprove) {
    return (
      <PageShell title="Análise CAPEX" backHref={capexApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          Acesso negado (403). Sem permissão de aprovação CAPEX.
        </StateBox>
      </PageShell>
    );
  }

  if (!resolvedId) {
    return (
      <PageShell title="Análise CAPEX" backHref={capexApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          Identificador do planejamento ausente na URL.
        </StateBox>
      </PageShell>
    );
  }

  if (!plan) {
    return (
      <PageShell title="Análise CAPEX" backHref={capexApprovalsHref()}>
        <StateBox variant="error" dismissible={false}>
          {error || "Planejamento CAPEX não encontrado."}
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title={`Análise — Filial ${plan.unit_id} · ${plan.cost_center_id}`}
      subtitle="Somente leitura. Decisões aplicam-se ao conjunto do centro de custo."
      icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
      backHref={capexApprovalsHref()}
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

      <SectionCard title="Resumo do planejamento">
        <dl className="po-detail-grid">
          <div>
            <dt>Status</dt>
            <dd>
              <span className="po-badge po-badge--muted">{planStatusLabel(plan.status)}</span>
            </dd>
          </div>
          <div>
            <dt>Filial</dt>
            <dd>{plan.unit_id}</dd>
          </div>
          <div>
            <dt>Área</dt>
            <dd>{plan.area_id || "—"}</dd>
          </div>
          <div>
            <dt>Centro de custo</dt>
            <dd>
              Filial {plan.unit_id} · {plan.cost_center_id}
            </dd>
          </div>
          <div>
            <dt>Responsável pelo envio</dt>
            <dd>{plan.submitted_by || "—"}</dd>
          </div>
          <div>
            <dt>Data de submissão</dt>
            <dd>{formatDateTimeBr(plan.submitted_at)}</dd>
          </div>
          <div>
            <dt>Investimentos ativos</dt>
            <dd>{investments.length}</dd>
          </div>
          <div>
            <dt>Valor total</dt>
            <dd>{formatMoneyBr(totalAmount)}</dd>
          </div>
          <div>
            <dt>Versão</dt>
            <dd>{plan.version}</dd>
          </div>
          <div>
            <dt>Última decisão</dt>
            <dd>{plan.decision_comment?.trim() || "—"}</dd>
          </div>
        </dl>
      </SectionCard>

      <SectionCard title="Investimentos" hint="Conjunto sujeito à decisão — somente leitura.">
        {investments.length === 0 ? (
          <StateBox variant="default" dismissible={false}>
            Nenhum investimento ativo neste planejamento.
          </StateBox>
        ) : (
          <ul className="po-resp-list">
            {investments.map((row: CapexInvestment) => {
              const cat = row.category_id ? categoryMap.get(row.category_id) : null;
              const attachments = attachmentsByInv[row.id] ?? [];
              return (
                <li key={row.id} className="po-resp-card">
                  <div className="po-resp-card__main">
                    <strong className="po-resp-card__title">
                      {row.description?.trim() || "(Sem descrição)"}
                    </strong>
                    <dl className="po-detail-grid">
                      <div>
                        <dt>Categoria</dt>
                        <dd>{cat?.name || row.category_id || "—"}</dd>
                      </div>
                      <div>
                        <dt>Prioridade</dt>
                        <dd>{priorityLabel(row.priority)}</dd>
                      </div>
                      <div>
                        <dt>Origem</dt>
                        <dd>{originLabel(row.origin)}</dd>
                      </div>
                      <div>
                        <dt>Valor</dt>
                        <dd>{formatMoneyBr(row.estimated_amount, row.currency)}</dd>
                      </div>
                      <div>
                        <dt>Data necessária</dt>
                        <dd>{formatDateBr(row.required_date)}</dd>
                      </div>
                      <div>
                        <dt>Fornecedor provável</dt>
                        <dd>
                          {row.probable_supplier_name || "—"}
                          {row.probable_supplier_code
                            ? ` (${row.probable_supplier_code})`
                            : ""}
                        </dd>
                      </div>
                    </dl>
                    {attachments.length > 0 ? (
                      <div style={{ marginTop: 12 }}>
                        <strong>Anexos</strong>
                        <ul className="po-link-list">
                          {attachments.map((att) => (
                            <li key={att.id}>
                              <button
                                type="button"
                                className="po-btn po-btn--secondary"
                                onClick={() => void handleDownload(att)}
                              >
                                {att.display_name} · {attachmentTypeLabel(att.attachment_type)}
                              </button>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      <p className="po-muted" style={{ marginTop: 8 }}>
                        Sem anexos ativos.
                      </p>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </SectionCard>

      <SectionCard title="Histórico">
        <CapexPlanHistoryTimeline items={history} />
      </SectionCard>

      <SectionCard
        title="Decisão"
        hint={
          plan.status === "submitted"
            ? "Envie sempre a versão atual do planejamento."
            : "Este planejamento já não está aguardando decisão."
        }
      >
        {plan.status !== "submitted" ? (
          <StateBox variant="default" dismissible={false}>
            Status atual: {planStatusLabel(plan.status)}. Novas decisões só são aceitas em
            “Enviado para aprovação”.
          </StateBox>
        ) : (
          <>
            <label>
              Comentário / justificativa
              <textarea
                rows={4}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Obrigatório para solicitar ajustes ou reprovar"
                disabled={deciding || versionConflict}
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
                className="po-btn po-btn--primary"
                disabled={!canDecide}
                onClick={() => void runDecision("approve")}
              >
                <Check size={16} aria-hidden="true" />
                {deciding ? "Processando…" : "Aprovar"}
              </button>
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
                className="po-btn po-btn--secondary"
                disabled={!canDecide}
                onClick={() => void runDecision("reject")}
              >
                <X size={16} aria-hidden="true" />
                Reprovar
              </button>
            </div>
          </>
        )}
      </SectionCard>
    </PageShell>
  );
}
