import { useCallback, useEffect, useMemo, useState } from "react";
import { ClipboardCheck, Search } from "lucide-react";

import {
  fetchBudgetContext,
  getCapexReviewDetail,
  listCapexReviewQueue,
} from "../api/budgetPlanningApi";
import { usePermissions } from "../hooks/usePermissions";
import type { BudgetExercise, CapexPlan } from "../types/budgetPlanning";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";
import { formatMoneyBr } from "../utils/capexInvestments";
import {
  activeInvestments,
  formatDateTimeBr,
  mapCapexPlanError,
  planStatusLabel,
  planSubmitterDisplayName,
  sumEstimatedAmounts,
  CAPEX_PLAN_STATUS_OPTIONS,
} from "../utils/capexPlans";
import { hasCapexApproveAccess } from "../utils/permissions";
import { capexReviewDetailHref, routeHref } from "../utils/routing";

type EnrichedPlan = CapexPlan & {
  investment_count?: number;
  total_amount?: string;
};

export function CapexReviewQueuePage() {
  const { profile, loading: permLoading, error: permError } = usePermissions();
  const canApprove = hasCapexApproveAccess(profile);

  const [exercise, setExercise] = useState<BudgetExercise | null>(null);
  const [items, setItems] = useState<EnrichedPlan[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const pageSize = 20;

  const [bootLoading, setBootLoading] = useState(true);
  const [listLoading, setListLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filterUnit, setFilterUnit] = useState("");
  const [filterArea, setFilterArea] = useState("");
  const [filterCc, setFilterCc] = useState("");
  const [filterStatus, setFilterStatus] = useState("submitted");
  const [filterResponsible, setFilterResponsible] = useState("");
  const [responsibleInput, setResponsibleInput] = useState("");

  useEffect(() => {
    if (permLoading || !canApprove) {
      setBootLoading(false);
      return;
    }
    const controller = new AbortController();
    setBootLoading(true);
    fetchBudgetContext(controller.signal)
      .then((ctx) => {
        setExercise(ctx.exercise);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(mapCapexPlanError(err));
      })
      .finally(() => {
        if (!controller.signal.aborted) setBootLoading(false);
      });
    return () => controller.abort();
  }, [canApprove, permLoading]);

  const loadQueue = useCallback(
    async (signal?: AbortSignal) => {
      if (!canApprove) return;
      setListLoading(true);
      setError(null);
      try {
        const result = await listCapexReviewQueue(
          {
            exercise_id: exercise?.id,
            unit_id: filterUnit || undefined,
            area_id: filterArea || undefined,
            cost_center_id: filterCc || undefined,
            status: filterStatus || undefined,
            submitted_by: filterResponsible || undefined,
            page,
            page_size: pageSize,
          },
          signal,
        );
        if (signal?.aborted) return;

        const enriched = await Promise.all(
          result.items.map(async (plan) => {
            try {
              const detail = await getCapexReviewDetail(plan.id, signal);
              const active = activeInvestments(detail.investments ?? []);
              return {
                ...plan,
                ...detail,
                investment_count: active.length,
                total_amount: sumEstimatedAmounts(active),
              } satisfies EnrichedPlan;
            } catch {
              return { ...plan, investment_count: undefined, total_amount: undefined };
            }
          }),
        );
        if (signal?.aborted) return;
        setItems(enriched);
        setTotal(result.pagination.total);
        setHasMore(result.pagination.has_more);
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setError(mapCapexPlanError(err));
        setItems([]);
      } finally {
        if (!signal?.aborted) setListLoading(false);
      }
    },
    [
      canApprove,
      exercise,
      filterArea,
      filterCc,
      filterResponsible,
      filterStatus,
      filterUnit,
      page,
    ],
  );

  useEffect(() => {
    if (permLoading || bootLoading || !canApprove) return;
    const controller = new AbortController();
    void loadQueue(controller.signal);
    return () => controller.abort();
  }, [bootLoading, canApprove, loadQueue, permLoading]);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(total / pageSize) || 1),
    [total],
  );

  if (permLoading || bootLoading) {
    return (
      <PageShell
        title="Aprovações CAPEX"
        subtitle="Fila de planejamentos enviados para análise."
        icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
        backRoute="home"
      >
        <LoadingActivityCard title="Carregando fila de aprovação…" variant="panel" />
      </PageShell>
    );
  }

  if (permError) {
    return (
      <PageShell title="Aprovações CAPEX" backRoute="home">
        <StateBox variant="error" dismissible={false}>
          {permError}
        </StateBox>
      </PageShell>
    );
  }

  if (!canApprove) {
    return (
      <PageShell title="Aprovações CAPEX" backRoute="home">
        <StateBox variant="error" dismissible={false}>
          Acesso negado. É necessária a permissão{" "}
          <code>planejamento-orcamentario.capex.approve</code> para acessar a fila.
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Aprovações CAPEX"
      subtitle="Analise cada investimento do centro — aprove ou reprove item a item."
      icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="home"
      actions={
        <a className="po-btn po-btn--secondary" href={routeHref("capex")}>
          Meus centros CAPEX
        </a>
      }
    >
      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
        </StateBox>
      ) : null}

      <SectionCard
        title="Fila de aprovação"
        hint={
          exercise
            ? `Exercício: ${exercise.year} — ${exercise.name}`
            : "Sem exercício ativo — a fila ainda pode listar planejamentos filtrados"
        }
      >
        <div className="po-filter-grid">
          <label>
            Unidade
            <input
              value={filterUnit}
              onChange={(e) => {
                setPage(1);
                setFilterUnit(e.target.value.trim());
              }}
              placeholder="Ex.: 01"
            />
          </label>
          <label>
            Área
            <input
              value={filterArea}
              onChange={(e) => {
                setPage(1);
                setFilterArea(e.target.value.trim());
              }}
              placeholder="Ex.: PROD"
            />
          </label>
          <label>
            Centro de custo
            <input
              value={filterCc}
              onChange={(e) => {
                setPage(1);
                setFilterCc(e.target.value.trim());
              }}
              placeholder="Ex.: 205"
            />
          </label>
          <label>
            Status
            <select
              value={filterStatus}
              onChange={(e) => {
                setPage(1);
                setFilterStatus(e.target.value);
              }}
            >
              <option value="submitted">Enviado para aprovação</option>
              {CAPEX_PLAN_STATUS_OPTIONS.filter((o) => o.value !== "submitted").map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
              <option value="">Todos</option>
            </select>
          </label>
          <label>
            Responsável (sub)
            <input
              value={responsibleInput}
              onChange={(e) => setResponsibleInput(e.target.value)}
              placeholder="Identificador do responsável"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  setPage(1);
                  setFilterResponsible(responsibleInput.trim());
                }
              }}
            />
          </label>
        </div>
        <div className="po-form-actions" style={{ marginTop: 12 }}>
          <button
            type="button"
            className="po-btn po-btn--secondary"
            onClick={() => {
              setPage(1);
              setFilterResponsible(responsibleInput.trim());
            }}
          >
            <Search size={14} aria-hidden="true" />
            Aplicar filtros
          </button>
        </div>

        {listLoading ? (
          <div
            className="po-skeleton-stack"
            aria-busy="true"
            aria-label="Carregando fila"
            style={{ marginTop: 16 }}
          >
            <div className="po-skeleton" />
            <div className="po-skeleton" />
          </div>
        ) : null}

        {!listLoading && items.length === 0 ? (
          <StateBox variant="default" dismissible={false}>
            Nenhum planejamento na fila com os filtros atuais.
          </StateBox>
        ) : null}

        {!listLoading && items.length > 0 ? (
          <ul className="po-resp-list" style={{ marginTop: 16 }}>
            {items.map((row) => (
              <li key={row.id} className="po-resp-card">
                <div className="po-resp-card__main">
                  <strong className="po-resp-card__title">
                    Filial {row.unit_id} · {row.cost_center_id}
                  </strong>
                  <span className="po-badge po-badge--muted">{planStatusLabel(row.status)}</span>
                  <dl className="po-detail-grid">
                    <div>
                      <dt>Filial</dt>
                      <dd>{row.unit_id}</dd>
                    </div>
                    <div>
                      <dt>Área</dt>
                      <dd>{row.area_id || "—"}</dd>
                    </div>
                    <div>
                      <dt>Responsável (envio)</dt>
                      <dd>{planSubmitterDisplayName(row)}</dd>
                    </div>
                    <div>
                      <dt>Investimentos</dt>
                      <dd>
                        {row.investment_count != null ? row.investment_count : "—"}
                      </dd>
                    </div>
                    <div>
                      <dt>Valor total</dt>
                      <dd>
                        {row.total_amount != null
                          ? formatMoneyBr(row.total_amount)
                          : "—"}
                      </dd>
                    </div>
                    <div>
                      <dt>Submissão</dt>
                      <dd>{formatDateTimeBr(row.submitted_at)}</dd>
                    </div>
                  </dl>
                </div>
                <div className="po-form-actions">
                  <a className="po-btn po-btn--primary" href={capexReviewDetailHref(row.id)}>
                    Analisar
                  </a>
                </div>
              </li>
            ))}
          </ul>
        ) : null}

        {!listLoading && total > 0 ? (
          <div className="po-pagination">
            <button
              type="button"
              className="po-btn po-btn--secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Anterior
            </button>
            <span className="po-muted">
              Página {page} de {totalPages}
              {hasMore ? " · há mais" : ""}
            </span>
            <button
              type="button"
              className="po-btn po-btn--secondary"
              disabled={!hasMore && page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Próxima
            </button>
          </div>
        ) : null}
      </SectionCard>
    </PageShell>
  );
}
