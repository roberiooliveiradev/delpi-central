import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Download,
  Filter,
  Layers,
  PieChart,
  RefreshCw,
} from "lucide-react";

import {
  exportCapexConsolidationXlsx,
  fetchBudgetContext,
  fetchCapexConsolidationByArea,
  fetchCapexConsolidationByCategory,
  fetchCapexConsolidationByCostCenter,
  fetchCapexConsolidationByMonth,
  fetchCapexConsolidationByOrigin,
  fetchCapexConsolidationByPlanStatus,
  fetchCapexConsolidationByPriority,
  fetchCapexConsolidationByUnit,
  fetchCapexConsolidationSummary,
  listActiveCapexCategories,
  listAdminExercises,
  listAdminScopes,
  listCapexConsolidationDetails,
} from "../api/budgetPlanningApi";
import { CapexConsolidationBarChart } from "../components/CapexConsolidationBarChart";
import { KpiCard } from "../components/KpiCard";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import type {
  BudgetExercise,
  CapexCategory,
  CapexConsolidationDetailItem,
  CapexConsolidationGroupItem,
  CapexConsolidationSummaryMetrics,
  OrgCatalog,
} from "../types/budgetPlanning";
import {
  CAPEX_ORIGIN_OPTIONS,
  CAPEX_PRIORITY_OPTIONS,
  formatMoneyBr,
} from "../utils/capexInvestments";
import {
  consolidationPlanStatusOptions,
  draftToFilters,
  emptyConsolidationDraft,
  isCurrencyConflictError,
  mapCapexConsolidationError,
  readConsolidationDraftFromUrl,
  topGroupItemsByAmount,
  triggerBrowserDownload,
  writeConsolidationDraftToUrl,
  type ConsolidationDraft,
} from "../utils/capexConsolidation";
import {
  hasCapexConsolidationViewAccess,
  hasCapexExportAccess,
  hasAdminAccess,
  hasScopesManageAccess,
} from "../utils/permissions";
import { filterAreasForUnit, filterCostCenters } from "../utils/responsibilities";
import {
  capexHref,
  capexInvestmentHref,
  capexReviewDetailHref,
  routeHref,
} from "../utils/routing";

const CC_CHART_LIMIT = 12;
const PAGE_SIZE = 20;

type GroupKey =
  | "unit"
  | "area"
  | "costCenter"
  | "category"
  | "priority"
  | "origin"
  | "month"
  | "planStatus";

type GroupState = Partial<Record<GroupKey, CapexConsolidationGroupItem[]>>;
type GroupErrors = Partial<Record<GroupKey, string>>;

function formatDateBr(value?: string | null): string {
  if (!value) return "—";
  const d = new Date(value.length <= 10 ? `${value}T00:00:00` : value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("pt-BR");
}

export function CapexConsolidationPage() {
  const { profile, loading: permLoading, error: permError } = usePermissions();
  const canView = hasCapexConsolidationViewAccess(profile);
  const canExport = hasCapexExportAccess(profile);
  const canLoadCatalog = hasAdminAccess(profile) || hasScopesManageAccess(profile);

  const [draft, setDraft] = useState<ConsolidationDraft>(() => readConsolidationDraftFromUrl());
  const [applied, setApplied] = useState<ConsolidationDraft | null>(null);

  const [exercises, setExercises] = useState<BudgetExercise[]>([]);
  const [defaultExercise, setDefaultExercise] = useState<BudgetExercise | null>(null);
  const [categories, setCategories] = useState<CapexCategory[]>([]);
  const [catalog, setCatalog] = useState<OrgCatalog | null>(null);

  const [bootLoading, setBootLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportFeedback, setExportFeedback] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [currencyConflict, setCurrencyConflict] = useState(false);
  const [groupErrors, setGroupErrors] = useState<GroupErrors>({});

  const [summary, setSummary] = useState<CapexConsolidationSummaryMetrics | null>(null);
  const [exerciseMeta, setExerciseMeta] = useState<{
    id: string;
    year?: number;
    name?: string;
  } | null>(null);
  const [groups, setGroups] = useState<GroupState>({});
  const [showAllCostCenters, setShowAllCostCenters] = useState(false);

  const [details, setDetails] = useState<CapexConsolidationDetailItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [sortBy, setSortBy] = useState("updated_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [detailsLoading, setDetailsLoading] = useState(false);

  const areasForUnit = useMemo(() => {
    if (!catalog) return [];
    if (!draft.unit_id) return catalog.areas ?? [];
    return filterAreasForUnit(catalog, draft.unit_id);
  }, [catalog, draft.unit_id]);
  const ccsForFilters = useMemo(() => {
    if (!catalog || !draft.unit_id) return [];
    return filterCostCenters(catalog, draft.unit_id, draft.area_id);
  }, [catalog, draft.unit_id, draft.area_id]);

  const costCenterChartItems = useMemo(() => {
    const items = groups.costCenter ?? [];
    if (showAllCostCenters || items.length <= CC_CHART_LIMIT) return items;
    return topGroupItemsByAmount(items, CC_CHART_LIMIT);
  }, [groups.costCenter, showAllCostCenters]);

  useEffect(() => {
    if (permLoading || !canView) {
      setBootLoading(false);
      return;
    }
    const controller = new AbortController();
    setBootLoading(true);
    Promise.all([
      fetchBudgetContext(controller.signal),
      listActiveCapexCategories(controller.signal).catch(() => ({ items: [] as CapexCategory[] })),
      canLoadCatalog
        ? listAdminScopes(controller.signal).catch(() => null)
        : Promise.resolve(null),
      hasAdminAccess(profile)
        ? listAdminExercises(controller.signal).catch(() => [] as BudgetExercise[])
        : Promise.resolve([] as BudgetExercise[]),
    ])
      .then(([ctx, cats, scopes, adminExercises]) => {
        if (controller.signal.aborted) return;
        setDefaultExercise(ctx.exercise);
        setCategories(cats.items ?? []);
        if (scopes?.catalog) setCatalog(scopes.catalog);
        const list = adminExercises.length
          ? adminExercises
          : ctx.exercise
            ? [ctx.exercise]
            : [];
        setExercises(list);

        setDraft((prev) => {
          if (prev.exercise_id) return prev;
          if (ctx.exercise?.id) {
            return { ...prev, exercise_id: ctx.exercise.id };
          }
          return prev;
        });
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(mapCapexConsolidationError(err));
      })
      .finally(() => {
        if (!controller.signal.aborted) setBootLoading(false);
      });
    return () => controller.abort();
  }, [canLoadCatalog, canView, permLoading, profile]);

  const loadPanel = useCallback(
    async (filtersDraft: ConsolidationDraft, signal?: AbortSignal) => {
      if (!filtersDraft.exercise_id) {
        setError("Selecione um exercício para consolidar.");
        return;
      }
      const filters = draftToFilters(filtersDraft);
      setLoading(true);
      setError(null);
      setCurrencyConflict(false);
      setGroupErrors({});
      setExportFeedback(null);

      try {
        const summaryResult = await fetchCapexConsolidationSummary(filters, signal);
        if (signal?.aborted) return;
        setSummary(summaryResult.summary);
        setExerciseMeta(summaryResult.exercise);

        const groupLoaders: Array<{
          key: GroupKey;
          run: () => Promise<{ items: CapexConsolidationGroupItem[] }>;
        }> = [
          { key: "unit", run: () => fetchCapexConsolidationByUnit(filters, signal) },
          { key: "area", run: () => fetchCapexConsolidationByArea(filters, signal) },
          {
            key: "costCenter",
            run: () => fetchCapexConsolidationByCostCenter(filters, signal),
          },
          { key: "category", run: () => fetchCapexConsolidationByCategory(filters, signal) },
          { key: "priority", run: () => fetchCapexConsolidationByPriority(filters, signal) },
          { key: "origin", run: () => fetchCapexConsolidationByOrigin(filters, signal) },
          { key: "month", run: () => fetchCapexConsolidationByMonth(filters, signal) },
          {
            key: "planStatus",
            run: () => fetchCapexConsolidationByPlanStatus(filters, signal),
          },
        ];

        const settled = await Promise.allSettled(groupLoaders.map((g) => g.run()));
        if (signal?.aborted) return;

        const nextGroups: GroupState = {};
        const nextErrors: GroupErrors = {};
        settled.forEach((result, index) => {
          const key = groupLoaders[index].key;
          if (result.status === "fulfilled") {
            nextGroups[key] = result.value.items ?? [];
          } else {
            nextErrors[key] = mapCapexConsolidationError(result.reason);
            if (isCurrencyConflictError(result.reason)) {
              setCurrencyConflict(true);
            }
          }
        });
        setGroups(nextGroups);
        setGroupErrors(nextErrors);

        // Catálogo org derivado dos CCs quando admin scopes não está disponível
        if (!catalog && nextGroups.costCenter?.length) {
          const units = new Map<string, { code: string; name: string }>();
          const areas = new Map<string, { code: string; name: string; unit_code?: string }>();
          const ccs: OrgCatalog["cost_centers"] = [];
          nextGroups.costCenter.forEach((item) => {
            const unit = String(item.unit_id || "");
            const area = String(item.area_id || "");
            const cc = String(item.cost_center_id || item.code || "");
            if (unit) units.set(unit, { code: unit, name: unit });
            if (area) areas.set(area, { code: area, name: area, unit_code: unit || undefined });
            if (cc) {
              ccs.push({
                code: cc,
                name: item.description || cc,
                unit_code: unit || null,
                area_code: area || null,
                active: true,
              });
            }
          });
          setCatalog({
            units: [...units.values()],
            areas: [...areas.values()],
            cost_centers: ccs,
          });
        }
      } catch (err: unknown) {
        if (signal?.aborted) return;
        if (isCurrencyConflictError(err)) setCurrencyConflict(true);
        setError(mapCapexConsolidationError(err));
        setSummary(null);
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [catalog],
  );

  const loadDetails = useCallback(
    async (
      filtersDraft: ConsolidationDraft,
      pageNum: number,
      sort: string,
      dir: "asc" | "desc",
      signal?: AbortSignal,
    ) => {
      if (!filtersDraft.exercise_id) return;
      setDetailsLoading(true);
      try {
        const result = await listCapexConsolidationDetails(
          {
            ...draftToFilters(filtersDraft),
            page: pageNum,
            page_size: PAGE_SIZE,
            sort_by: sort,
            sort_dir: dir,
          },
          signal,
        );
        if (signal?.aborted) return;
        setDetails(result.items ?? []);
        setTotal(result.pagination.total);
        setTotalPages(result.pagination.total_pages);
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setDetails([]);
        setGroupErrors((prev) => ({
          ...prev,
          // reusa slot de erro parcial
          planStatus: prev.planStatus,
        }));
        setError((prev) => prev ?? mapCapexConsolidationError(err));
      } finally {
        if (!signal?.aborted) setDetailsLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    if (!canView || bootLoading || !applied?.exercise_id) return;
    const controller = new AbortController();
    void loadPanel(applied, controller.signal);
    void loadDetails(applied, page, sortBy, sortDir, controller.signal);
    return () => controller.abort();
  }, [applied, bootLoading, canView, loadDetails, loadPanel, page, sortBy, sortDir]);

  // Auto-aplicar no boot quando exercício default estiver pronto
  useEffect(() => {
    if (!canView || bootLoading || applied) return;
    if (draft.exercise_id || defaultExercise?.id) {
      const next = {
        ...draft,
        exercise_id: draft.exercise_id || defaultExercise?.id || "",
      };
      setDraft(next);
      writeConsolidationDraftToUrl(next);
      setApplied(next);
    }
  }, [applied, bootLoading, canView, defaultExercise, draft]);

  function updateDraft(patch: Partial<ConsolidationDraft>) {
    setDraft((prev) => {
      const next = { ...prev, ...patch };
      if (patch.unit_id !== undefined && patch.unit_id !== prev.unit_id) {
        next.area_id = "";
        next.cost_center_id = "";
      }
      if (patch.area_id !== undefined && patch.area_id !== prev.area_id) {
        next.cost_center_id = "";
      }
      return next;
    });
  }

  function applyFilters() {
    const next = { ...draft };
    if (!next.exercise_id && defaultExercise?.id) {
      next.exercise_id = defaultExercise.id;
    }
    writeConsolidationDraftToUrl(next);
    setPage(1);
    setShowAllCostCenters(false);
    setApplied(next);
  }

  function clearFilters() {
    const next: ConsolidationDraft = {
      ...emptyConsolidationDraft,
      exercise_id: defaultExercise?.id || draft.exercise_id || "",
    };
    setDraft(next);
    writeConsolidationDraftToUrl(next);
    setPage(1);
    setShowAllCostCenters(false);
    setApplied(next);
  }

  async function handleExport() {
    if (!canExport || !applied?.exercise_id || exporting) return;
    setExporting(true);
    setExportFeedback("Gerando planilha Excel…");
    try {
      const result = await exportCapexConsolidationXlsx(draftToFilters(applied));
      triggerBrowserDownload(result.blob, result.filename);
      setExportFeedback(`Download concluído: ${result.filename}`);
    } catch (err: unknown) {
      setExportFeedback(mapCapexConsolidationError(err));
      if (isCurrencyConflictError(err)) setCurrencyConflict(true);
    } finally {
      setExporting(false);
    }
  }

  function toggleSort(field: string) {
    if (sortBy === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(field);
      setSortDir("desc");
    }
    setPage(1);
  }

  if (permLoading || bootLoading) {
    return (
      <PageShell
        title="Consolidação de Investimentos"
        subtitle="Painel gerencial CAPEX"
        backRoute="home"
      >
        <LoadingActivityCard title="Carregando consolidação CAPEX…" />
        <div className="po-kpi-grid po-kpi-grid--skeleton" aria-hidden="true">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="po-skeleton-card" />
          ))}
        </div>
      </PageShell>
    );
  }

  if (permError) {
    return (
      <PageShell title="Consolidação de Investimentos" backRoute="home">
        <StateBox>
          {permError.includes("401") || permError.toLowerCase().includes("sessão")
            ? "Sessão expirada. Faça login novamente."
            : permError}
        </StateBox>
      </PageShell>
    );
  }

  if (!canView) {
    return (
      <PageShell title="Consolidação de Investimentos" backRoute="home">
        <StateBox>
          Acesso negado. É necessária a permissão de consolidação gerencial CAPEX.
        </StateBox>
      </PageShell>
    );
  }

  if (!defaultExercise && !draft.exercise_id && exercises.length === 0) {
    return (
      <PageShell title="Consolidação de Investimentos" backRoute="home">
        <StateBox>Não há exercício orçamentário disponível para consolidação.</StateBox>
      </PageShell>
    );
  }

  const currency = summary?.currency || "BRL";
  const emptyData = summary != null && summary.investment_count === 0;

  return (
    <PageShell
      title="Consolidação de Investimentos"
      subtitle="Indicadores, agrupamentos e exportação Excel do CAPEX"
      backRoute="home"
      actions={
        canExport ? (
          <button
            type="button"
            className="po-btn po-btn--primary"
            onClick={() => void handleExport()}
            disabled={exporting || !applied?.exercise_id}
            aria-busy={exporting}
          >
            <Download size={16} aria-hidden="true" />
            {exporting ? "Exportando…" : "Exportar Excel"}
          </button>
        ) : null
      }
    >
      {currencyConflict ? (
        <StateBox>
          <strong>Conflito de moedas.</strong> Há investimentos com moedas diferentes no filtro.
          Os valores não podem ser somados automaticamente.
        </StateBox>
      ) : null}
      {error ? <StateBox>{error}</StateBox> : null}
      {exportFeedback ? (
        <p className="po-status-banner" role="status">
          {exportFeedback}
        </p>
      ) : null}

      <SectionCard title="Filtros" hint="Os filtros são aplicados no backend.">
        <div className="po-filter-grid">
          <label>
            Exercício
            <select
              value={draft.exercise_id}
              onChange={(e) => updateDraft({ exercise_id: e.target.value })}
            >
              <option value="">Selecione…</option>
              {exercises.map((ex) => (
                <option key={ex.id} value={ex.id}>
                  {ex.year} — {ex.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Filial
            <select
              value={draft.unit_id}
              onChange={(e) => updateDraft({ unit_id: e.target.value })}
            >
              <option value="">Todas</option>
              {(catalog?.units ?? []).map((u) => (
                <option key={u.code} value={u.code}>
                  {u.code} — {u.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Área
            <select
              value={draft.area_id}
              onChange={(e) => updateDraft({ area_id: e.target.value })}
              disabled={!draft.unit_id && areasForUnit.length === 0}
            >
              <option value="">Todas</option>
              {areasForUnit.map((a) => (
                <option key={a.code} value={a.code}>
                  {a.code} — {a.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Centro de custo
            <select
              value={draft.cost_center_id}
              onChange={(e) => updateDraft({ cost_center_id: e.target.value })}
            >
              <option value="">Todos</option>
              {ccsForFilters.map((cc) => (
                <option
                  key={`${cc.branch || cc.unit_code || ""}:${cc.code}`}
                  value={cc.code}
                >
                  Filial {cc.branch || cc.unit_code || "—"} · {cc.code}
                  {cc.name ? ` — ${cc.name}` : ""}
                </option>
              ))}
            </select>
          </label>
          <label>
            Categoria
            <select
              value={draft.category_id}
              onChange={(e) => updateDraft({ category_id: e.target.value })}
            >
              <option value="">Todas</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.code} — {c.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Prioridade
            <select
              value={draft.priority}
              onChange={(e) => updateDraft({ priority: e.target.value })}
            >
              <option value="">Todas</option>
              {CAPEX_PRIORITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Origem
            <select
              value={draft.origin}
              onChange={(e) => updateDraft({ origin: e.target.value })}
            >
              <option value="">Todas</option>
              {CAPEX_ORIGIN_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Status do planejamento
            <select
              value={draft.plan_status}
              onChange={(e) => updateDraft({ plan_status: e.target.value })}
            >
              {consolidationPlanStatusOptions().map((o) => (
                <option key={o.value || "all"} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Data Rcbto inicial
            <input
              type="date"
              value={draft.required_date_from}
              onChange={(e) => updateDraft({ required_date_from: e.target.value })}
            />
          </label>
          <label>
            Data Rcbto final
            <input
              type="date"
              value={draft.required_date_to}
              onChange={(e) => updateDraft({ required_date_to: e.target.value })}
            />
          </label>
        </div>
        <div className="po-inline-actions">
          <button type="button" className="po-btn po-btn--primary" onClick={applyFilters}>
            <Filter size={16} aria-hidden="true" />
            Aplicar filtros
          </button>
          <button type="button" className="po-btn" onClick={clearFilters}>
            <RefreshCw size={16} aria-hidden="true" />
            Limpar filtros
          </button>
        </div>
      </SectionCard>

      {loading && !summary ? (
        <LoadingActivityCard title="Atualizando indicadores…" />
      ) : null}

      {summary ? (
        <SectionCard
          title="Indicadores"
          hint={
            exerciseMeta
              ? `${exerciseMeta.year ?? ""} — ${exerciseMeta.name ?? ""}`.trim()
              : undefined
          }
        >
          <div className="po-kpi-grid">
            <KpiCard
              title="Valor total previsto"
              value={formatMoneyBr(summary.total_estimated_amount, currency)}
              icon={<PieChart size={20} aria-hidden="true" />}
              loading={loading}
            />
            <KpiCard
              title="Investimentos"
              value={String(summary.investment_count)}
              icon={<Layers size={20} aria-hidden="true" />}
              loading={loading}
            />
            <KpiCard
              title="Centros de custo"
              value={String(summary.cost_center_count)}
              icon={<ClipboardList size={20} aria-hidden="true" />}
              loading={loading}
            />
            <KpiCard
              title="Valor aprovado"
              value={formatMoneyBr(summary.approved_amount, currency)}
              icon={<CheckCircle2 size={20} aria-hidden="true" />}
              loading={loading}
            />
            <KpiCard
              title="Valor em análise"
              value={formatMoneyBr(summary.in_review_amount, currency)}
              icon={<AlertTriangle size={20} aria-hidden="true" />}
              loading={loading}
            />
            <KpiCard
              title="Investimentos incompletos"
              value={String(summary.incomplete_investment_count)}
              icon={<AlertTriangle size={20} aria-hidden="true" />}
              valueTone={summary.incomplete_investment_count > 0 ? "danger" : "default"}
              loading={loading}
            />
            <KpiCard
              title="Planos em rascunho"
              value={String(summary.plans_draft_count)}
              icon={<ClipboardList size={20} aria-hidden="true" />}
              loading={loading}
            />
            <KpiCard
              title="Planos enviados"
              value={String(summary.plans_submitted_count)}
              icon={<ClipboardList size={20} aria-hidden="true" />}
              loading={loading}
            />
            <KpiCard
              title="Ajustes solicitados"
              value={String(summary.plans_changes_requested_count)}
              icon={<ClipboardList size={20} aria-hidden="true" />}
              loading={loading}
            />
            <KpiCard
              title="Planos reprovados"
              value={String(summary.plans_rejected_count)}
              icon={<ClipboardList size={20} aria-hidden="true" />}
              loading={loading}
            />
            <KpiCard
              title="Planos aprovados"
              value={String(summary.plans_approved_count)}
              icon={<CheckCircle2 size={20} aria-hidden="true" />}
              loading={loading}
            />
          </div>
        </SectionCard>
      ) : null}

      {emptyData ? (
        <StateBox>Nenhum investimento encontrado para os filtros aplicados.</StateBox>
      ) : null}

      {!emptyData && summary ? (
        <div className="po-chart-grid">
          {(
            [
              ["unit", "Valor por unidade", groups.unit],
              ["area", "Valor por área", groups.area],
              ["category", "Valor por categoria", groups.category],
              ["priority", "Valor por prioridade", groups.priority],
              ["origin", "Valor por origem", groups.origin],
            ] as const
          ).map(([key, title, items]) => (
            <SectionCard key={key} title={title}>
              {groupErrors[key] ? (
                <p className="po-muted" role="alert">
                  {groupErrors[key]}
                </p>
              ) : (
                <CapexConsolidationBarChart
                  title={title}
                  items={items ?? []}
                  currency={currency}
                />
              )}
            </SectionCard>
          ))}

          <SectionCard title="Valor por centro de custo">
            {groupErrors.costCenter ? (
              <p className="po-muted" role="alert">
                {groupErrors.costCenter}
              </p>
            ) : (
              <>
                <CapexConsolidationBarChart
                  title="Valor por centro de custo"
                  items={costCenterChartItems}
                  currency={currency}
                />
                {(groups.costCenter?.length ?? 0) > CC_CHART_LIMIT ? (
                  <button
                    type="button"
                    className="po-btn"
                    onClick={() => setShowAllCostCenters((v) => !v)}
                  >
                    {showAllCostCenters
                      ? "Mostrar apenas os maiores"
                      : `Ver todos (${groups.costCenter?.length}) no gráfico`}
                  </button>
                ) : null}
              </>
            )}
          </SectionCard>

          <SectionCard title="Valor por mês (Data Rcbto)">
            {groupErrors.month ? (
              <p className="po-muted" role="alert">
                {groupErrors.month}
              </p>
            ) : (
              <CapexConsolidationBarChart
                title="Valor por mês"
                items={groups.month ?? []}
                orientation="vertical"
                currency={currency}
              />
            )}
          </SectionCard>

          <SectionCard title="Distribuição por status do planejamento">
            {groupErrors.planStatus ? (
              <p className="po-muted" role="alert">
                {groupErrors.planStatus}
              </p>
            ) : (
              <CapexConsolidationBarChart
                title="Status do planejamento"
                items={groups.planStatus ?? []}
                currency={currency}
              />
            )}
          </SectionCard>
        </div>
      ) : null}

      <SectionCard title="Detalhamento" hint="Ordenação e paginação no servidor.">
        {detailsLoading ? <LoadingActivityCard title="Carregando detalhamento…" /> : null}
        <div className="po-table-wrap">
          <table className="po-table">
            <thead>
              <tr>
                <th>
                  <button type="button" className="po-linkish" onClick={() => toggleSort("unit_id")}>
                    Filial
                  </button>
                </th>
                <th>
                  <button type="button" className="po-linkish" onClick={() => toggleSort("area_id")}>
                    Área
                  </button>
                </th>
                <th>
                  <button
                    type="button"
                    className="po-linkish"
                    onClick={() => toggleSort("cost_center_id")}
                  >
                    Centro de custo
                  </button>
                </th>
                <th>Responsável</th>
                <th>
                  <button
                    type="button"
                    className="po-linkish"
                    onClick={() => toggleSort("description")}
                  >
                    Descrição
                  </button>
                </th>
                <th>Categoria</th>
                <th>
                  <button
                    type="button"
                    className="po-linkish"
                    onClick={() => toggleSort("priority")}
                  >
                    Prioridade
                  </button>
                </th>
                <th>
                  <button type="button" className="po-linkish" onClick={() => toggleSort("origin")}>
                    Origem
                  </button>
                </th>
                <th>Fornecedor</th>
                <th>
                  <button
                    type="button"
                    className="po-linkish"
                    onClick={() => toggleSort("estimated_amount")}
                  >
                    Valor
                  </button>
                </th>
                <th>
                  <button
                    type="button"
                    className="po-linkish"
                    onClick={() => toggleSort("required_date")}
                  >
                    Data Rcbto
                  </button>
                </th>
                <th>Completo</th>
                <th>
                  <button
                    type="button"
                    className="po-linkish"
                    onClick={() => toggleSort("plan_status")}
                  >
                    Status
                  </button>
                </th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {details.map((row) => (
                <tr key={row.id}>
                  <td data-label="Filial">{row.unit_id || "—"}</td>
                  <td data-label="Área">{row.area_id || "—"}</td>
                  <td data-label="Centro de custo">
                    {row.cost_center_id
                      ? `Filial ${row.unit_id || "—"} · ${row.cost_center_id}`
                      : "—"}
                  </td>
                  <td data-label="Responsável">{row.responsible || "—"}</td>
                  <td data-label="Descrição">{row.description || "—"}</td>
                  <td data-label="Categoria">
                    {row.category_name || row.category_code || "—"}
                  </td>
                  <td data-label="Prioridade">{row.priority_label || row.priority || "—"}</td>
                  <td data-label="Origem">{row.origin_label || row.origin || "—"}</td>
                  <td data-label="Fornecedor">{row.probable_supplier_name || "—"}</td>
                  <td data-label="Valor">
                    {formatMoneyBr(row.estimated_amount, row.currency || currency)}
                  </td>
                  <td data-label="Data Rcbto">{formatDateBr(row.required_date)}</td>
                  <td data-label="Completo">
                    <span
                      className={
                        row.is_complete ? "po-badge po-badge--success" : "po-badge po-badge--warning"
                      }
                    >
                      {row.is_complete ? "Sim" : "Não"}
                    </span>
                  </td>
                  <td data-label="Status">{row.plan_status_label || row.plan_status || "—"}</td>
                  <td data-label="Ações">
                    <div className="po-inline-actions">
                      {row.cost_center_id ? (
                        <a
                          href={capexHref({
                            costCenterId: row.cost_center_id,
                            unitId: row.unit_id || undefined,
                          })}
                        >
                          Planejamento
                        </a>
                      ) : null}
                      {row.id ? <a href={capexInvestmentHref(row.id)}>Investimento</a> : null}
                      {row.plan_id && row.plan_status === "submitted" ? (
                        <a href={capexReviewDetailHref(row.plan_id)}>Aprovação</a>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
              {!details.length && !detailsLoading ? (
                <tr>
                  <td colSpan={14}>
                    <span className="po-muted">Sem linhas para os filtros atuais.</span>
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
        <div className="po-inline-actions">
          <button
            type="button"
            className="po-btn"
            disabled={page <= 1 || detailsLoading}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Anterior
          </button>
          <span className="po-muted">
            Página {page} de {Math.max(totalPages, 1)} · {total} registro(s)
          </span>
          <button
            type="button"
            className="po-btn"
            disabled={page >= totalPages || detailsLoading}
            onClick={() => setPage((p) => p + 1)}
          >
            Próxima
          </button>
        </div>
        <p className="po-muted">
          <a href={routeHref("capex")}>Ir para meus centros de custo</a>
        </p>
      </SectionCard>
    </PageShell>
  );
}
