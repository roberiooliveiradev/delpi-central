import { useCallback, useEffect, useMemo, useState } from "react";
import { ClipboardCheck, Search, Users } from "lucide-react";

import {
  fetchBudgetContext,
  listPersonnelReviewQueue,
} from "../api/budgetPlanningApi";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import type { BudgetExercise, PersonnelPlan } from "../types/budgetPlanning";
import {
  formatPersonnelDateTimeBr,
  mapPersonnelError,
  PERSONNEL_PLAN_STATUS_OPTIONS,
  personnelPlanStatusLabel,
} from "../utils/personnelPlans";
import { hasPersonnelApproveAccess } from "../utils/permissions";
import {
  pessoalApprovalsHref,
  pessoalReviewDetailHref,
  readQueryParam,
  routeHref,
} from "../utils/routing";

function replaceQueueQuery(next: Record<string, string>) {
  if (typeof window === "undefined") return;
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(next)) {
    if (value) qs.set(key, value);
  }
  const query = qs.toString();
  const url = query ? `${pessoalApprovalsHref()}?${query}` : pessoalApprovalsHref();
  window.history.replaceState({}, "", url);
}

export function PersonnelReviewQueuePage() {
  const { profile, loading: permLoading, error: permError } = usePermissions();
  const canApprove = hasPersonnelApproveAccess(profile);

  const [exercise, setExercise] = useState<BudgetExercise | null>(null);
  const [items, setItems] = useState<PersonnelPlan[]>([]);
  const [page, setPage] = useState(() => {
    const raw = Number(readQueryParam("page") || "1");
    return Number.isFinite(raw) && raw >= 1 ? raw : 1;
  });
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const pageSize = 20;

  const [bootLoading, setBootLoading] = useState(true);
  const [listLoading, setListLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filterUnit, setFilterUnit] = useState(() => readQueryParam("unit_id"));
  const [filterArea, setFilterArea] = useState(() => readQueryParam("area_id"));
  const [filterCc, setFilterCc] = useState(() => readQueryParam("cost_center_id"));
  const [filterStatus, setFilterStatus] = useState(
    () => readQueryParam("status") || "submitted",
  );
  const [filterResponsible, setFilterResponsible] = useState(
    () => readQueryParam("submitted_by"),
  );
  const [responsibleInput, setResponsibleInput] = useState(
    () => readQueryParam("submitted_by"),
  );

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
        setError(mapPersonnelError(err));
      })
      .finally(() => {
        if (!controller.signal.aborted) setBootLoading(false);
      });
    return () => controller.abort();
  }, [canApprove, permLoading]);

  const syncUrl = useCallback(() => {
    replaceQueueQuery({
      unit_id: filterUnit,
      area_id: filterArea,
      cost_center_id: filterCc,
      status: filterStatus,
      submitted_by: filterResponsible,
      page: page > 1 ? String(page) : "",
    });
  }, [filterArea, filterCc, filterResponsible, filterStatus, filterUnit, page]);

  const loadQueue = useCallback(
    async (signal?: AbortSignal) => {
      if (!canApprove) return;
      setListLoading(true);
      setError(null);
      try {
        const result = await listPersonnelReviewQueue(
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
        setItems(result.items);
        setTotal(result.pagination.total);
        setHasMore(result.pagination.has_more);
        syncUrl();
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setError(mapPersonnelError(err));
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
      syncUrl,
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
        title="Aprovações de Pessoal"
        subtitle="Fila de orçamentos enviados para análise."
        icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
        backRoute="home"
      >
        <LoadingActivityCard title="Carregando fila de aprovação…" variant="panel" />
      </PageShell>
    );
  }

  if (permError) {
    return (
      <PageShell title="Aprovações de Pessoal" backRoute="home">
        <StateBox variant="error" dismissible={false}>
          {permError}
        </StateBox>
      </PageShell>
    );
  }

  if (!canApprove) {
    return (
      <PageShell title="Aprovações de Pessoal" backRoute="home">
        <StateBox variant="error" dismissible={false}>
          Acesso negado. É necessária a permissão{" "}
          <code>planejamento-orcamentario.personnel.approve</code> para acessar a
          fila.
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Aprovações de Pessoal"
      subtitle="Analise o orçamento por centro de custo — aprovação do conjunto, não linha a linha."
      icon={<ClipboardCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="home"
      actions={
        <a className="po-btn po-btn--secondary" href={routeHref("pessoal")}>
          <Users size={16} aria-hidden="true" />
          Orçamento de Pessoal
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
            Filial
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
              {PERSONNEL_PLAN_STATUS_OPTIONS.filter((o) => o.value !== "submitted").map(
                (o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ),
              )}
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
            Nenhum orçamento na fila com os filtros atuais.
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
                  <span className="po-badge po-badge--muted">
                    {personnelPlanStatusLabel(row.status)}
                  </span>
                  <dl className="po-detail-grid">
                    <div>
                      <dt>Exercício</dt>
                      <dd>{exercise?.year ?? "—"}</dd>
                    </div>
                    <div>
                      <dt>Área</dt>
                      <dd>{row.area_id || "—"}</dd>
                    </div>
                    <div>
                      <dt>Responsável (envio)</dt>
                      <dd>{row.submitted_by || "—"}</dd>
                    </div>
                    <div>
                      <dt>Cargos</dt>
                      <dd>{row.position_count ?? "—"}</dd>
                    </div>
                    <div>
                      <dt>Total Dez/2027</dt>
                      <dd>{row.totals?.headcount_dec_2027 ?? "—"}</dd>
                    </div>
                    <div>
                      <dt>Submissão</dt>
                      <dd>{formatPersonnelDateTimeBr(row.submitted_at)}</dd>
                    </div>
                  </dl>
                </div>
                <div className="po-form-actions">
                  <a
                    className="po-btn po-btn--primary"
                    href={pessoalReviewDetailHref(row.id)}
                  >
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
