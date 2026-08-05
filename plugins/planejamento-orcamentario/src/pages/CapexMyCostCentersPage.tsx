import { useCallback, useEffect, useMemo, useState } from "react";
import { Building2, Landmark, Plus, Search } from "lucide-react";

import { HttpRequestError } from "../api/httpClient";
import {
  archiveCapexInvestment,
  fetchBudgetContext,
  fetchMyCapexResponsibilities,
  listActiveCapexCategories,
  listCapexInvestments,
} from "../api/budgetPlanningApi";
import type {
  BudgetContext,
  BudgetExercise,
  BudgetResponsibility,
  CapexCategory,
  CapexInvestment,
  CapexPlan,
} from "../types/budgetPlanning";
import { CapexPlanWorkflowPanel } from "../components/CapexPlanWorkflowPanel";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import {
  formatMoneyBr,
  investmentStatusLabel,
  missingFieldLabel,
  originLabel,
  priorityLabel,
} from "../utils/capexInvestments";
import { isPlanEditable, planLockReason } from "../utils/capexPlans";
import { hasCapexApproveAccess, hasCapexSubmitAccess } from "../utils/permissions";
import {
  costCenterKey,
  formatCostCenterLabel,
} from "../utils/orgCostCenters";
import { formatDateBr, responsibilityTypeLabel } from "../utils/responsibilities";
import {
  capexApprovalsHref,
  capexHref,
  capexInvestmentHref,
  capexNewInvestmentHref,
  readQueryParam,
  routeHref,
} from "../utils/routing";

function exerciseTitle(exercise: BudgetExercise | null | undefined, exerciseId: string): string {
  if (exercise && exercise.id === exerciseId) {
    return `${exercise.year} — ${exercise.name}`;
  }
  return exerciseId ? `Exercício ${exerciseId.slice(0, 8)}…` : "Exercício vigente";
}

export function CapexMyCostCentersPage() {
  const selectedCc = readQueryParam("cost_center_id");
  const selectedUnit = readQueryParam("unit_id");
  const { profile } = usePermissions();
  const canSubmit = hasCapexSubmitAccess(profile);
  const canApprove = hasCapexApproveAccess(profile);

  const [context, setContext] = useState<BudgetContext | null>(null);
  const [responsibilities, setResponsibilities] = useState<BudgetResponsibility[]>([]);
  const [categories, setCategories] = useState<CapexCategory[]>([]);
  const [investments, setInvestments] = useState<CapexInvestment[]>([]);
  const [plan, setPlan] = useState<CapexPlan | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const pageSize = 20;

  const [bootLoading, setBootLoading] = useState(true);
  const [listLoading, setListLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [filterCategory, setFilterCategory] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [filterOrigin, setFilterOrigin] = useState("");
  const [filterStatus, setFilterStatus] = useState("draft");
  const [searchInput, setSearchInput] = useState("");
  const [filterQ, setFilterQ] = useState("");

  const exercise = context?.exercise ?? null;
  const modulesUnlocked = Boolean(context?.modules_unlocked);
  const guidancePending = Boolean(context && !context.modules_unlocked);

  const categoryMap = useMemo(() => {
    const map = new Map<string, CapexCategory>();
    for (const c of categories) map.set(c.id, c);
    return map;
  }, [categories]);

  const selectedResponsibility = useMemo(() => {
    if (!selectedCc) return null;
    return (
      responsibilities.find((r) => {
        if (r.cost_center_id !== selectedCc) return false;
        if (selectedUnit) return r.unit_id === selectedUnit;
        return true;
      }) ?? null
    );
  }, [responsibilities, selectedCc, selectedUnit]);

  const planEditable = isPlanEditable(plan);
  const lockReason = planLockReason(plan);

  useEffect(() => {
    const controller = new AbortController();
    setBootLoading(true);
    setError(null);

    fetchBudgetContext(controller.signal)
      .then(async (ctx) => {
        setContext(ctx);
        if (!ctx.exercise) {
          setResponsibilities([]);
          return;
        }
        if (!ctx.modules_unlocked) {
          setResponsibilities([]);
          return;
        }
        const [mine, cats] = await Promise.all([
          fetchMyCapexResponsibilities(ctx.exercise.id, controller.signal),
          listActiveCapexCategories(controller.signal),
        ]);
        if (!controller.signal.aborted) {
          setResponsibilities(mine.items ?? []);
          setCategories(cats.items ?? []);
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof HttpRequestError && err.status === 401) {
          setError("Sessão expirada (401). Faça login novamente.");
        } else if (err instanceof HttpRequestError && err.status === 403) {
          setError("Acesso negado (403) ao módulo CAPEX.");
        } else {
          setError(err instanceof Error ? err.message : "Erro ao carregar o módulo CAPEX.");
        }
        setResponsibilities([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setBootLoading(false);
      });

    return () => controller.abort();
  }, []);

  const loadInvestments = useCallback(
    async (signal?: AbortSignal) => {
      if (!selectedCc || !exercise?.id || !modulesUnlocked) {
        setInvestments([]);
        return;
      }
      setListLoading(true);
      setListError(null);
      try {
        const result = await listCapexInvestments(
          {
            exercise_id: exercise.id,
            unit_id: selectedUnit || selectedResponsibility?.unit_id || undefined,
            cost_center_id: selectedCc,
            category_id: filterCategory || undefined,
            priority: filterPriority || undefined,
            origin: filterOrigin || undefined,
            status: filterStatus || undefined,
            q: filterQ || undefined,
            page,
            page_size: pageSize,
          },
          signal,
        );
        if (signal?.aborted) return;
        setInvestments(result.items);
        setTotal(result.pagination.total);
        setHasMore(result.pagination.has_more);
      } catch (err: unknown) {
        if (signal?.aborted) return;
        if (err instanceof HttpRequestError && err.status === 401) {
          setListError("Sessão expirada (401). Faça login novamente.");
        } else if (err instanceof HttpRequestError && err.status === 403) {
          setListError("Acesso negado (403) aos investimentos deste centro.");
        } else {
          setListError(err instanceof Error ? err.message : "Erro ao listar investimentos.");
        }
        setInvestments([]);
      } finally {
        if (!signal?.aborted) setListLoading(false);
      }
    },
    [
      exercise,
      filterCategory,
      filterOrigin,
      filterPriority,
      filterQ,
      filterStatus,
      modulesUnlocked,
      page,
      selectedCc,
      selectedResponsibility,
      selectedUnit,
    ],
  );

  useEffect(() => {
    if (bootLoading || !selectedCc) return;
    const controller = new AbortController();
    void loadInvestments(controller.signal);
    return () => controller.abort();
  }, [bootLoading, loadInvestments, selectedCc]);

  async function handleArchive(row: CapexInvestment) {
    if (!planEditable) {
      setListError(lockReason || "Planejamento bloqueado para edição.");
      return;
    }
    if (
      !window.confirm(
        `Arquivar o investimento "${row.description || row.id.slice(0, 8)}"? Esta ação não poderá ser desfeita nesta etapa.`,
      )
    ) {
      return;
    }
    try {
      await archiveCapexInvestment(row.id);
      setSuccessMsg("Investimento arquivado.");
      await loadInvestments();
    } catch (err: unknown) {
      setListError(err instanceof Error ? err.message : "Falha ao arquivar.");
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1);

  return (
    <PageShell
      title="CAPEX — Investimentos"
      subtitle="Selecione um centro de custo autorizado e gerencie os rascunhos de investimento."
      icon={<Landmark size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="home"
      actions={
        <>
          {canApprove ? (
            <a className="po-btn po-btn--secondary" href={capexApprovalsHref()}>
              Aprovações
            </a>
          ) : null}
          {selectedCc && planEditable ? (
            <a
              className="po-btn po-btn--primary"
              href={capexNewInvestmentHref({
                costCenterId: selectedCc,
                unitId: selectedUnit || selectedResponsibility?.unit_id,
              })}
            >
              <Plus size={16} aria-hidden="true" />
              Novo investimento
            </a>
          ) : null}
        </>
      }
    >
      {bootLoading ? (
        <LoadingActivityCard title="Carregando módulo CAPEX…" variant="panel" />
      ) : null}

      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
        </StateBox>
      ) : null}

      {successMsg ? (
        <StateBox variant="success" dismissible={false}>
          {successMsg}
        </StateBox>
      ) : null}

      {!bootLoading && !error && !exercise ? (
        <StateBox variant="warning" dismissible={false}>
          Não há exercício orçamentário ativo. Aguarde a abertura do ciclo pela administração.
        </StateBox>
      ) : null}

      {!bootLoading && !error && exercise && guidancePending ? (
        <StateBox variant="warning" dismissible={false}>
          Confirme a leitura das orientações vigentes antes de elaborar investimentos CAPEX.{" "}
          <a href={routeHref("orientacoes")}>Ir para Orientações</a>
        </StateBox>
      ) : null}

      {!bootLoading && !error && modulesUnlocked && responsibilities.length === 0 ? (
        <SectionCard title="Sem centros atribuídos">
          <StateBox variant="default" dismissible={false}>
            Você ainda não foi vinculado como responsável por nenhum centro de custo neste
            exercício. Solicite a amarração à administração do planejamento.
          </StateBox>
        </SectionCard>
      ) : null}

      {!bootLoading && !error && modulesUnlocked && responsibilities.length > 0 ? (
        <SectionCard
          title="Meus centros de custo"
          hint={exercise ? `Exercício: ${exercise.year} — ${exercise.name}` : undefined}
        >
          <StateBox variant="success" dismissible={false}>
            Você está autorizado a elaborar o orçamento de investimentos dos centros abaixo.
            Selecione um centro para listar os rascunhos.
          </StateBox>
          <ul className="po-resp-list">
            {responsibilities.map((row) => {
              const active =
                row.cost_center_id === selectedCc &&
                (!selectedUnit || row.unit_id === selectedUnit);
              return (
                <li
                  key={costCenterKey({
                    id: row.id,
                    branch: row.branch ?? row.unit_id,
                    code: row.cost_center_id,
                  })}
                  className={`po-resp-card ${active ? "po-resp-card--selected" : ""}`}
                >
                  <div className="po-resp-card__main">
                    <strong className="po-resp-card__title">
                      <Building2 size={16} aria-hidden="true" />{" "}
                      {formatCostCenterLabel({
                        branch: row.branch ?? row.unit_id,
                        code: row.cost_center_id,
                      })}
                    </strong>
                    <dl className="po-detail-grid">
                      <div>
                        <dt>Exercício</dt>
                        <dd>{exerciseTitle(exercise, row.exercise_id)}</dd>
                      </div>
                      <div>
                        <dt>Filial</dt>
                        <dd>{row.unit_id}</dd>
                      </div>
                      <div>
                        <dt>Área</dt>
                        <dd>{row.area_id || "—"}</dd>
                      </div>
                      <div>
                        <dt>Tipo</dt>
                        <dd>{responsibilityTypeLabel(row.responsibility_type)}</dd>
                      </div>
                    </dl>
                  </div>
                  <div className="po-form-actions">
                    <a
                      className={`po-btn ${active ? "po-btn--primary" : "po-btn--secondary"}`}
                      href={capexHref({
                        costCenterId: row.cost_center_id,
                        unitId: row.unit_id,
                      })}
                    >
                      {active ? "Centro selecionado" : "Ver investimentos"}
                    </a>
                  </div>
                </li>
              );
            })}
          </ul>
        </SectionCard>
      ) : null}

      {selectedCc && modulesUnlocked && selectedResponsibility && exercise ? (
        <CapexPlanWorkflowPanel
          exercise={exercise}
          costCenterId={selectedCc}
          unitId={selectedResponsibility.unit_id}
          areaId={selectedResponsibility.area_id}
          canSubmit={canSubmit}
          onPlanChange={setPlan}
          onSubmitted={() => void loadInvestments()}
        />
      ) : null}

      {selectedCc && modulesUnlocked ? (
        <SectionCard
          title={`Investimentos — ${formatCostCenterLabel({
            branch: selectedUnit || selectedResponsibility?.unit_id,
            code: selectedCc,
          })}`}
          hint={
            selectedResponsibility
              ? `Filial ${selectedResponsibility.unit_id}${
                  selectedResponsibility.area_id
                    ? ` · Área ${selectedResponsibility.area_id}`
                    : ""
                }`
              : "Filtros enviados ao backend"
          }
        >
          {!selectedResponsibility ? (
            <StateBox variant="error" dismissible={false}>
              O centro{" "}
              {formatCostCenterLabel({
                branch: selectedUnit,
                code: selectedCc,
              })}{" "}
              não está entre as suas responsabilidades. Escolha um centro autorizado acima.
            </StateBox>
          ) : (
            <>
              {lockReason ? (
                <StateBox variant="warning" dismissible={false}>
                  {lockReason} Os investimentos abaixo estão em modo somente leitura.
                </StateBox>
              ) : null}
              <div className="po-filter-grid">
                <label>
                  Categoria
                  <select
                    value={filterCategory}
                    onChange={(e) => {
                      setPage(1);
                      setFilterCategory(e.target.value);
                    }}
                  >
                    <option value="">Todas</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Prioridade
                  <select
                    value={filterPriority}
                    onChange={(e) => {
                      setPage(1);
                      setFilterPriority(e.target.value);
                    }}
                  >
                    <option value="">Todas</option>
                    <option value="1">1 — Compra aprovada/em andamento</option>
                    <option value="2">2 — Maior necessidade</option>
                    <option value="3">3 — Média</option>
                    <option value="4">4 — Menor</option>
                  </select>
                </label>
                <label>
                  Origem
                  <select
                    value={filterOrigin}
                    onChange={(e) => {
                      setPage(1);
                      setFilterOrigin(e.target.value);
                    }}
                  >
                    <option value="">Todas</option>
                    <option value="national">Nacional</option>
                    <option value="imported">Importado</option>
                  </select>
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
                    <option value="">Todos</option>
                    <option value="draft">Rascunho</option>
                    <option value="archived">Arquivado</option>
                  </select>
                </label>
                <label>
                  Pesquisar
                  <input
                    type="search"
                    value={searchInput}
                    placeholder="Descrição, fornecedor…"
                    onChange={(e) => setSearchInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        setPage(1);
                        setFilterQ(searchInput.trim());
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
                    setFilterQ(searchInput.trim());
                  }}
                >
                  <Search size={14} aria-hidden="true" />
                  Aplicar pesquisa
                </button>
              </div>

              {listError ? (
                <StateBox variant="error" dismissible={false}>
                  {listError}
                </StateBox>
              ) : null}

              {listLoading ? (
                <div
                  className="po-skeleton-stack"
                  aria-busy="true"
                  aria-label="Carregando investimentos"
                  style={{ marginTop: 16 }}
                >
                  <div className="po-skeleton" />
                  <div className="po-skeleton" />
                </div>
              ) : null}

              {!listLoading && investments.length === 0 ? (
                <StateBox variant="default" dismissible={false}>
                  Nenhum investimento encontrado para este centro e filtros. Use “Novo
                  investimento” para criar um rascunho.
                </StateBox>
              ) : null}

              {!listLoading && investments.length > 0 ? (
                <ul className="po-resp-list" style={{ marginTop: 16 }}>
                  {investments.map((row) => {
                    const cat = row.category_id ? categoryMap.get(row.category_id) : null;
                    return (
                      <li key={row.id} className="po-resp-card">
                        <div className="po-resp-card__main">
                          <strong className="po-resp-card__title">
                            {row.description?.trim() || "(Sem descrição)"}
                          </strong>
                          {!row.is_complete ? (
                            <span className="po-badge po-badge--warning">Rascunho incompleto</span>
                          ) : (
                            <span className="po-badge po-badge--success">Completo</span>
                          )}
                          <dl className="po-detail-grid">
                            <div>
                              <dt>Categoria</dt>
                              <dd>{cat ? cat.name : row.category_id || "—"}</dd>
                            </div>
                            <div>
                              <dt>Centro de custo</dt>
                              <dd>{row.cost_center_id}</dd>
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
                              <dt>Valor previsto</dt>
                              <dd>{formatMoneyBr(row.estimated_amount, row.currency)}</dd>
                            </div>
                            <div>
                              <dt>Data Rcbto</dt>
                              <dd>{formatDateBr(row.required_date)}</dd>
                            </div>
                            <div>
                              <dt>Fornecedor</dt>
                              <dd>{row.probable_supplier_name || "—"}</dd>
                            </div>
                            <div>
                              <dt>Status</dt>
                              <dd>{investmentStatusLabel(row.status)}</dd>
                            </div>
                            <div>
                              <dt>Última alteração</dt>
                              <dd>
                                {formatDateBr(row.updated_at?.slice(0, 10) ?? null)}
                              </dd>
                            </div>
                          </dl>
                          {!row.is_complete && row.missing_fields?.length ? (
                            <p className="po-muted">
                              Pendências:{" "}
                              {row.missing_fields.map(missingFieldLabel).join(", ")}
                            </p>
                          ) : null}
                        </div>
                        <div className="po-form-actions">
                          <a className="po-btn po-btn--secondary" href={capexInvestmentHref(row.id)}>
                            {row.status === "archived" || !planEditable
                              ? "Visualizar"
                              : "Editar"}
                          </a>
                          {row.status === "draft" && planEditable ? (
                            <button
                              type="button"
                              className="po-btn po-btn--secondary"
                              onClick={() => void handleArchive(row)}
                            >
                              Arquivar
                            </button>
                          ) : null}
                        </div>
                      </li>
                    );
                  })}
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
            </>
          )}
        </SectionCard>
      ) : null}
    </PageShell>
  );
}
