import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Building2,
  CheckCircle2,
  ClipboardCheck,
  Landmark,
  Layers,
  PieChart,
  ShieldCheck,
} from "lucide-react";

import {
  fetchBudgetContext,
  fetchCapexConsolidationByCostCenter,
  fetchCapexConsolidationByPlanStatus,
  fetchCapexConsolidationSummary,
} from "../api/budgetPlanningApi";
import { CapexApprovalWorkspace } from "../components/CapexApprovalWorkspace";
import { CapexConsolidationBarChart } from "../components/CapexConsolidationBarChart";
import { KpiCard } from "../components/KpiCard";
import { PageShell } from "../components/PageShell";
import { PersonnelApprovalWorkspace } from "../components/PersonnelApprovalWorkspace";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import type {
  BudgetExercise,
  CapexConsolidationGroupItem,
  CapexConsolidationSummaryMetrics,
} from "../types/budgetPlanning";
import { formatMoneyBr } from "../utils/capexInvestments";
import { topGroupItemsByAmount } from "../utils/capexConsolidation";
import { resolveCostCenterIcon } from "../utils/costCenterIcons";
import {
  amountFromPlanStatusGroups,
  applyConsolidationAmountsToPortfolio,
  approvalPlanStatusLabel,
  fetchApprovalPlansForCostCenter,
  fetchApprovalPortfolio,
  groupApprovalPortfolioByUnit,
  portfolioPendingCounts,
  portfolioToChartItems,
  type ApprovalPortfolioItem,
} from "../utils/approvalPortfolio";
import { formatCostCenterLabel } from "../utils/orgCostCenters";
import {
  hasCapexApproveAccess,
  hasCapexConsolidationViewAccess,
  hasPersonnelApproveAccess,
} from "../utils/permissions";
import {
  gestaoAprovacoesHref,
  readQueryParam,
  routeHref,
} from "../utils/routing";

function centerCardAccent(item: ApprovalPortfolioItem): string {
  if (item.capexPending || item.personnelPending) return "sky";
  if (item.capexInProgress || item.personnelInProgress) return "amber";
  if (
    item.capexPlan?.status === "changes_requested" ||
    item.personnelPlan?.status === "changes_requested"
  ) {
    return "amber";
  }
  if (item.capexPlan?.status === "approved" || item.personnelPlan?.status === "approved") {
    return "emerald";
  }
  return "slate";
}

function centerCardTitle(item: ApprovalPortfolioItem): string {
  const name = String(item.cost_center_name || "").trim();
  if (name) return name;
  return item.cost_center_id;
}

function centerCardStatus(item: ApprovalPortfolioItem): string {
  if (item.capexPending || item.personnelPending) return "Aguardando aprovação";
  if (item.capexInProgress || item.personnelInProgress) return "Em andamento";
  if (item.capexPlan?.status === "approved" || item.personnelPlan?.status === "approved") {
    return "Concluído";
  }
  if (item.capexPlan?.status === "rejected" || item.personnelPlan?.status === "rejected") {
    return "Reprovado";
  }
  if (
    item.capexPlan?.status === "changes_requested" ||
    item.personnelPlan?.status === "changes_requested"
  ) {
    return approvalPlanStatusLabel("changes_requested");
  }
  return "Não iniciado";
}

export function ApprovalManagementPage() {
  const { profile, loading: permLoading, error: permError } = usePermissions();
  const canCapex = hasCapexApproveAccess(profile);
  const canPersonnel = hasPersonnelApproveAccess(profile);
  const canConsolidate = hasCapexConsolidationViewAccess(profile);
  const canAccess = canCapex || canPersonnel;

  const selectedCc = readQueryParam("cost_center_id");
  const selectedUnit = readQueryParam("unit_id");

  const [exercise, setExercise] = useState<BudgetExercise | null>(null);
  const [portfolio, setPortfolio] = useState<ApprovalPortfolioItem[]>([]);
  const [summary, setSummary] = useState<CapexConsolidationSummaryMetrics | null>(null);
  const [chartItems, setChartItems] = useState<CapexConsolidationGroupItem[]>([]);
  const [draftAmount, setDraftAmount] = useState<number | null>(null);
  const [limitedKpis, setLimitedKpis] = useState(false);
  const [bootLoading, setBootLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const [workspaceItem, setWorkspaceItem] = useState<ApprovalPortfolioItem | null>(null);
  const [workspaceLoading, setWorkspaceLoading] = useState(false);

  const refresh = useCallback(() => setReloadToken((n) => n + 1), []);

  const loadOverview = useCallback(
    async (signal?: AbortSignal) => {
      if (!canAccess) {
        setBootLoading(false);
        return;
      }
      setBootLoading(true);
      setError(null);
      try {
        const ctx = await fetchBudgetContext(signal);
        if (signal?.aborted) return;
        setExercise(ctx.exercise);
        if (!ctx.exercise) {
          setPortfolio([]);
          setSummary(null);
          setChartItems([]);
          setDraftAmount(null);
          setWorkspaceItem(null);
          return;
        }

        let items = await fetchApprovalPortfolio({
          exerciseId: ctx.exercise.id,
          includeCapex: canCapex,
          includePersonnel: canPersonnel,
          signal,
        });
        if (signal?.aborted) return;

        if (selectedCc && selectedUnit) {
          setWorkspaceLoading(true);
          const ws = await fetchApprovalPlansForCostCenter({
            exerciseId: ctx.exercise.id,
            unitId: selectedUnit,
            costCenterId: selectedCc,
            includeCapex: canCapex,
            includePersonnel: canPersonnel,
            signal,
          });
          if (!signal?.aborted) {
            setWorkspaceItem(ws);
            setWorkspaceLoading(false);
          }
        } else {
          setWorkspaceItem(null);
        }

        if (canCapex && canConsolidate) {
          try {
            const [sumRes, byCcAll, byCcPending, byStatus] = await Promise.all([
              fetchCapexConsolidationSummary(
                { exercise_id: ctx.exercise.id },
                signal,
              ),
              fetchCapexConsolidationByCostCenter(
                { exercise_id: ctx.exercise.id },
                signal,
              ),
              fetchCapexConsolidationByCostCenter(
                { exercise_id: ctx.exercise.id, plan_status: "submitted" },
                signal,
              ),
              fetchCapexConsolidationByPlanStatus(
                { exercise_id: ctx.exercise.id },
                signal,
              ),
            ]);
            if (signal?.aborted) return;
            items = applyConsolidationAmountsToPortfolio(
              items,
              byCcAll.items ?? [],
            );
            setSummary(sumRes.summary);
            setDraftAmount(amountFromPlanStatusGroups(byStatus.items ?? [], "draft"));
            setChartItems(topGroupItemsByAmount(byCcPending.items ?? [], 12));
            setLimitedKpis(false);
          } catch {
            if (signal?.aborted) return;
            setSummary(null);
            setDraftAmount(null);
            setChartItems(portfolioToChartItems(items));
            setLimitedKpis(true);
          }
        } else if (canCapex) {
          setSummary(null);
          setDraftAmount(null);
          setChartItems(portfolioToChartItems(items));
          setLimitedKpis(true);
        } else {
          setSummary(null);
          setDraftAmount(null);
          setChartItems([]);
          setLimitedKpis(false);
        }

        if (!signal?.aborted) setPortfolio(items);
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar gestão de aprovações.");
        setPortfolio([]);
      } finally {
        if (!signal?.aborted) setBootLoading(false);
      }
    },
    [
      canAccess,
      canCapex,
      canConsolidate,
      canPersonnel,
      selectedCc,
      selectedUnit,
    ],
  );

  useEffect(() => {
    if (permLoading) return;
    const controller = new AbortController();
    void loadOverview(controller.signal);
    return () => controller.abort();
  }, [loadOverview, permLoading, reloadToken]);

  const counts = useMemo(() => portfolioPendingCounts(portfolio), [portfolio]);
  const portfolioByUnit = useMemo(
    () => groupApprovalPortfolioByUnit(portfolio),
    [portfolio],
  );
  const selectedItem = workspaceItem;

  if (permLoading || (canAccess && bootLoading && !selectedCc)) {
    return (
      <PageShell
        title="Gestão de aprovações"
        subtitle="Cockpit da diretoria — insights e decisões por centro."
        icon={<ShieldCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
      >
        <LoadingActivityCard title="Preparando gestão de aprovações…" variant="panel" />
      </PageShell>
    );
  }

  if (permError) {
    return (
      <PageShell title="Gestão de aprovações" icon={<ShieldCheck size={28} />}>
        <StateBox variant="error" dismissible={false}>
          {permError}
        </StateBox>
      </PageShell>
    );
  }

  if (!canAccess) {
    return (
      <PageShell title="Gestão de aprovações" icon={<ShieldCheck size={28} />}>
        <StateBox variant="error" dismissible={false}>
          Acesso negado. É necessária permissão de aprovação CAPEX ou Pessoal.
        </StateBox>
      </PageShell>
    );
  }

  if (selectedCc && selectedUnit) {
    const capexPlanId = selectedItem?.capexPlan?.id;
    const personnelPlanId = selectedItem?.personnelPlan?.id;
    const showCapex = canCapex && Boolean(capexPlanId);
    const showPersonnel = canPersonnel && Boolean(personnelPlanId);

    return (
      <PageShell
        title="Gestão do centro"
        subtitle={`${formatCostCenterLabel({
          branch: selectedItem?.branch ?? selectedUnit,
          code: selectedCc,
        })} — analise e decida CAPEX e Pessoal.`}
        icon={<Landmark size={28} strokeWidth={1.75} aria-hidden="true" />}
        backHref={gestaoAprovacoesHref()}
      >
        {error ? (
          <StateBox variant="error" dismissible={false}>
            {error}
          </StateBox>
        ) : null}

        <aside className="po-approval-mgmt__sticky" aria-label="Resumo do centro">
          <div className="po-approval-mgmt__sticky-row">
            <div>
              <p className="po-approval-mgmt__sticky-label">CAPEX</p>
              <p className="po-approval-mgmt__sticky-value">
                {selectedItem?.capexPending
                  ? formatMoneyBr(String(selectedItem.capexAmount))
                  : selectedItem?.capexPlan
                    ? approvalPlanStatusLabel(selectedItem.capexPlan.status)
                    : "—"}
              </p>
            </div>
            <div>
              <p className="po-approval-mgmt__sticky-label">Pessoal</p>
              <p className="po-approval-mgmt__sticky-value">
                {selectedItem?.personnelPending
                  ? `${selectedItem.personnelHeadcount} HC`
                  : selectedItem?.personnelPlan
                    ? approvalPlanStatusLabel(selectedItem.personnelPlan.status)
                    : "—"}
              </p>
            </div>
            <div>
              <p className="po-approval-mgmt__sticky-label">Decisões</p>
              <p className="po-approval-mgmt__sticky-value">
                {(selectedItem?.capexPending ? 1 : 0) +
                  (selectedItem?.personnelPending ? 1 : 0)}
              </p>
            </div>
          </div>
        </aside>

        {!selectedItem && !bootLoading && !workspaceLoading ? (
          <StateBox variant="warning" dismissible={false}>
            Nenhum plano encontrado para este centro na fila.{" "}
            <a href={gestaoAprovacoesHref()}>Voltar ao overview</a>
          </StateBox>
        ) : null}

        {bootLoading || workspaceLoading ? (
          <LoadingActivityCard title="Carregando centro…" variant="panel" />
        ) : null}

        <div className="po-approval-mgmt__workspace">
          {showCapex && capexPlanId ? (
            <section className="po-approval-mgmt__module" aria-label="Seção CAPEX">
              <header className="po-workspace-section__head">
                <Building2 size={20} aria-hidden="true" />
                <div>
                  <h3>CAPEX — Investimentos</h3>
                  <p className="po-muted">Aprove ou reprove cada investimento. Abra os detalhes para ver observações.</p>
                </div>
              </header>
              <CapexApprovalWorkspace
                planId={capexPlanId}
                embedded
                onDecided={refresh}
              />
            </section>
          ) : canCapex ? (
            <StateBox variant="default" dismissible={false}>
              Sem plano CAPEX enviado para este centro neste momento.
            </StateBox>
          ) : null}

          {showPersonnel && personnelPlanId ? (
            <section className="po-approval-mgmt__module" aria-label="Seção Pessoal">
              <header className="po-workspace-section__head">
                <ClipboardCheck size={20} aria-hidden="true" />
                <div>
                  <h3>Pessoal — Headcount</h3>
                  <p className="po-muted">Grade de cargos e totais do plano enviado.</p>
                </div>
              </header>
              <PersonnelApprovalWorkspace
                planId={personnelPlanId}
                embedded
                onDecided={refresh}
              />
            </section>
          ) : canPersonnel ? (
            <StateBox variant="default" dismissible={false}>
              Sem plano de Pessoal enviado para este centro neste momento.
            </StateBox>
          ) : null}
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Gestão de aprovações"
      subtitle="Visão da diretoria: pendências, valores e decisão por centro de custo."
      icon={<ShieldCheck size={28} strokeWidth={1.75} aria-hidden="true" />}
    >
      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
        </StateBox>
      ) : null}

      <section className="po-approval-mgmt" aria-label="Overview de aprovações">
        <div className="po-approval-mgmt__hero">
          <div className="po-approval-mgmt__hero-copy">
            <p className="po-approval-mgmt__eyebrow">Diretoria · Aprovações</p>
            <h2 className="po-approval-mgmt__year">{exercise?.year ?? "—"}</h2>
            <p className="po-approval-mgmt__name">
              {exercise?.name ?? "Nenhum exercício ativo"}
            </p>
            <p className="po-approval-mgmt__lead">
              Acompanhe todos os centros com plano CAPEX ou Pessoal — em elaboração ou
              aguardando sua decisão. Abra o centro para analisar e decidir por módulo.
            </p>
          </div>
        </div>

        {limitedKpis ? (
          <StateBox variant="warning" dismissible={false}>
            Valores do ciclo incompletos — totais derivados da fila. Para o painel completo,
            peça a permissão de consolidação CAPEX.
          </StateBox>
        ) : null}

        <div className="po-approval-mgmt__kpis">
          <KpiCard
            title="Aguardando aprovação"
            subtitle="Planos enviados (CAPEX)"
            value={
              summary
                ? formatMoneyBr(summary.in_review_amount, summary.currency)
                : formatMoneyBr(String(counts.capexPendingAmount))
            }
            icon={<PieChart size={20} aria-hidden="true" />}
          />
          <KpiCard
            title="Em elaboração"
            subtitle="Ainda em rascunho"
            value={
              draftAmount != null
                ? formatMoneyBr(String(draftAmount), summary?.currency ?? "BRL")
                : "—"
            }
            icon={<Layers size={20} aria-hidden="true" />}
          />
          <KpiCard
            title="Já aprovado"
            subtitle="Decisão concluída"
            value={
              summary ? formatMoneyBr(summary.approved_amount, summary.currency) : "—"
            }
            icon={<CheckCircle2 size={20} aria-hidden="true" />}
          />
          <KpiCard
            title="Total do ciclo"
            subtitle="Soma de todos os status"
            value={
              summary
                ? formatMoneyBr(summary.total_estimated_amount, summary.currency)
                : "—"
            }
            icon={<Landmark size={20} aria-hidden="true" />}
          />
          <KpiCard
            title="Centros no radar"
            subtitle={`${counts.centersWithPending} p/ decidir · ${counts.centersInProgress} andamento`}
            value={String(counts.centersTracked)}
            icon={<Building2 size={20} aria-hidden="true" />}
          />
        </div>

        {canCapex ? (
          <SectionCard
            title="Maiores valores aguardando aprovação"
            hint="Ranking CAPEX dos centros que já enviaram o plano — do maior valor para o menor."
          >
            <CapexConsolidationBarChart
              title="Valor CAPEX por centro (enviados)"
              items={chartItems}
              currency={summary?.currency ?? "BRL"}
            />
          </SectionCard>
        ) : null}

        <div className="po-approval-mgmt__list-head">
          <h3 className="po-approval-mgmt__list-title">Centros de custo</h3>
          <p className="po-approval-mgmt__list-subtitle">
            Abra um centro para analisar. Enviados pedem decisão; rascunhos ficam em andamento.
          </p>
        </div>

        {portfolio.length === 0 ? (
          <StateBox variant="default" dismissible={false}>
            Nenhum centro com plano CAPEX ou Pessoal neste ciclo ainda.
          </StateBox>
        ) : (
          <div className="po-approval-mgmt__unit-stack">
            {portfolioByUnit.map((group) => (
              <section
                key={group.unit_id}
                className="po-approval-mgmt__unit-block"
                aria-labelledby={`po-approval-unit-${group.unit_id}`}
              >
                <header className="po-approval-mgmt__unit-head">
                  <h4
                    id={`po-approval-unit-${group.unit_id}`}
                    className="po-approval-mgmt__unit-title"
                  >
                    {group.title}
                  </h4>
                  <p className="po-approval-mgmt__unit-count">
                    {group.items.length} centro
                    {group.items.length === 1 ? "" : "s"}
                  </p>
                </header>
                <ul
                  className="po-approval-mgmt__launchpad"
                  aria-label={group.title}
                >
                  {group.items.map((item) => {
                    const title = centerCardTitle(item);
                    const status = centerCardStatus(item);
                    const needsAction = item.capexPending || item.personnelPending;
                    const accent = centerCardAccent(item);
                    const CcIcon = resolveCostCenterIcon(item.icon_key);
                    const amountLabel =
                      canCapex && item.capexAmount > 0
                        ? formatMoneyBr(String(item.capexAmount))
                        : canPersonnel && item.personnelPlan
                          ? `${item.personnelHeadcount || 0} HC`
                          : null;
                    const href = gestaoAprovacoesHref({
                      unitId: item.unit_id,
                      costCenterId: item.cost_center_id,
                    });
                    return (
                      <li key={item.key} className="po-approval-mgmt__launch-item">
                        <a
                          className={`po-approval-mgmt__launch-card po-approval-mgmt__launch-card--${accent}${
                            needsAction ? " is-action" : ""
                          }`}
                          href={href}
                          aria-label={`${title}, filial ${item.unit_id}, ${status}${
                            item.owner_name ? `, responsável ${item.owner_name}` : ""
                          }${needsAction ? ", decidir" : ""}`}
                        >
                          <span
                            className="po-approval-mgmt__launch-icon-wrap"
                            aria-hidden="true"
                          >
                            <span className="po-approval-mgmt__launch-icon">
                              <CcIcon size={20} strokeWidth={1.75} />
                            </span>
                            {needsAction ? (
                              <span className="po-approval-mgmt__launch-dot" />
                            ) : null}
                          </span>
                          <span className="po-approval-mgmt__launch-body">
                            <span className="po-approval-mgmt__launch-code">
                              {item.unit_id} · {item.cost_center_id}
                            </span>
                            <span className="po-approval-mgmt__launch-title">{title}</span>
                            {item.owner_name ? (
                              <span className="po-approval-mgmt__launch-owner">
                                {item.owner_name}
                              </span>
                            ) : null}
                            <span className="po-approval-mgmt__launch-foot">
                              <span className="po-approval-mgmt__launch-status">
                                {status}
                              </span>
                              {amountLabel ? (
                                <span className="po-approval-mgmt__launch-meta">
                                  {amountLabel}
                                </span>
                              ) : null}
                              {needsAction ? (
                                <span className="po-approval-mgmt__launch-cta">Decidir</span>
                              ) : null}
                            </span>
                          </span>
                        </a>
                      </li>
                    );
                  })}
                </ul>
              </section>
            ))}
          </div>
        )}

        <p className="po-muted po-approval-mgmt__footer-links">
          Visões avançadas:{" "}
          {canCapex ? (
            <a href={routeHref("capex-approvals")}>Fila CAPEX</a>
          ) : null}
          {canCapex && canPersonnel ? " · " : null}
          {canPersonnel ? (
            <a href={routeHref("pessoal-approvals")}>Fila Pessoal</a>
          ) : null}
          {canConsolidate ? (
            <>
              {" · "}
              <a href={routeHref("capex-consolidation")}>Consolidação</a>
            </>
          ) : null}
        </p>
      </section>
    </PageShell>
  );
}
