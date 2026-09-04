import { ListChecks, RefreshCw, Users } from "lucide-react";
import { useEffect, useState } from "react";

import { getSlaPolicies } from "../../api/slaPoliciesApi";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialSectionCard,
  CommercialSectionHintLabel,
  CommercialSegmentToggle,
  CommercialSelectField,
  CommercialTextField,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import { CM_HELP } from "../../content/helpTooltips";
import type { CommercialProposal } from "../../types/analytics";
import {
  getCommercialProposals,
  getOpportunityCollaboratorSummary,
  type OpportunityCollaboratorSummaryRow,
} from "../../api/analyticsApi";
import { nextTableSortState, type TableSortDirection } from "../../utils/sortTableRows";
import { AnalyticsFilters } from "./components/AnalyticsFilters";
import { AnalyticsDeepPagePath } from "./components/AnalyticsDeepPagePath";
import { CommercialProposalsTable } from "./components/CommercialProposalsTable";
import { OpportunityCollaboratorSummaryTable } from "./components/OpportunityCollaboratorSummaryTable";
import { useAnalyticsFilters } from "./hooks/useAnalyticsFilters";
import {
  buildAnalyticsOpportunityBackSearch,
  readAnalyticsOpportunitySearch,
  subscribeAnalyticsFilterRouteSync,
  writeAnalyticsOpportunitySearchToUrl,
} from "./utils/analyticsFilterUrl";
import {
  DEFAULT_PROPOSAL_SORT_DIR,
  DEFAULT_PROPOSAL_SORT_KEY,
  proposalApiSortParams,
} from "./utils/proposalListSort";
import {
  parseOpportunitiesView,
  writeOpportunitiesViewToUrl,
  type OpportunitiesView,
} from "./utils/opportunitiesViewDeepLink";

type AnalyticsOpportunitiesPageProps = {
  basePath: string;
};

export function AnalyticsOpportunitiesPage({ basePath }: AnalyticsOpportunitiesPageProps) {
  const { canViewProposals } = usePortfolioScope();
  const filters = useAnalyticsFilters();
  const [view, setView] = useState<OpportunitiesView>(() => parseOpportunitiesView());
  const [items, setItems] = useState<CommercialProposal[]>([]);
  const [collab, setCollab] = useState<OpportunityCollaboratorSummaryRow[]>([]);
  const [slaConfigured, setSlaConfigured] = useState(false);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState(() => readAnalyticsOpportunitySearch());
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState(DEFAULT_PROPOSAL_SORT_KEY);
  const [sortDirection, setSortDirection] =
    useState<TableSortDirection>(DEFAULT_PROPOSAL_SORT_DIR);
  const [loading, setLoading] = useState(true);
  const [collabLoading, setCollabLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    writeOpportunitiesViewToUrl(view);
  }, [view]);

  useEffect(() => {
    writeAnalyticsOpportunitySearchToUrl(search);
  }, [search]);

  useEffect(
    () =>
      subscribeAnalyticsFilterRouteSync(() => {
        setSearch(readAnalyticsOpportunitySearch());
        setView(parseOpportunitiesView());
      }),
    [],
  );

  useEffect(() => {
    if (view !== "opportunity") return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    const apiSort = proposalApiSortParams(sortKey, sortDirection);
    void getCommercialProposals(
      {
        ...filters.apiParams,
        page: 1,
        page_size: 50,
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        sort_by: apiSort.sort_by,
        sort_dir: apiSort.sort_dir,
      },
      controller.signal,
    )
      .then((page) => {
        if (controller.signal.aborted) return;
        setItems(page.items ?? []);
        setTotal(page.total ?? 0);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar oportunidades.");
        setItems([]);
        setTotal(0);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    view,
    filters.apiParams.start_date,
    filters.apiParams.end_date,
    filters.apiParams.branch,
    filters.apiParams.customer_segment,
    filters.apiParams.seller_id,
    filters.apiParams.customer_codes,
    search,
    statusFilter,
    sortKey,
    sortDirection,
    reloadKey,
  ]);

  useEffect(() => {
    if (view !== "collaborator") return;
    const controller = new AbortController();
    setCollabLoading(true);
    void Promise.all([
      getOpportunityCollaboratorSummary(
        { ...filters.apiParams },
        controller.signal,
      ).catch(() => null),
      getSlaPolicies(controller.signal).catch(() => ({ items: [], configured: false })),
    ]).then(([summary, sla]) => {
      if (controller.signal.aborted) return;
      if (summary) {
        setCollab(summary.items ?? []);
      } else {
        setCollab([]);
      }
      setSlaConfigured(Boolean(sla?.configured));
      setCollabLoading(false);
    });
    return () => controller.abort();
  }, [
    view,
    filters.apiParams.start_date,
    filters.apiParams.end_date,
    filters.apiParams.branch,
    filters.apiParams.customer_segment,
    filters.apiParams.seller_id,
    filters.apiParams.customer_codes,
    reloadKey,
  ]);

  // SLA banner: load once for opportunity view too (lightweight)
  useEffect(() => {
    if (view !== "opportunity") return;
    const controller = new AbortController();
    void getSlaPolicies(controller.signal)
      .then((sla) => {
        if (!controller.signal.aborted) setSlaConfigured(Boolean(sla?.configured));
      })
      .catch(() => {
        if (!controller.signal.aborted) setSlaConfigured(false);
      });
    return () => controller.abort();
  }, [view, reloadKey]);

  return (
    <section className="cm-page-stack">
      <AnalyticsDeepPagePath
        basePath={basePath}
        current={ANALYTICS_CONTENT.oportunidades.title}
        backTo="home"
        viewId="analytics_opportunities"
      />
      <CommercialPageHero
        aria-label={ANALYTICS_CONTENT.oportunidades.title}
        title={
          <CommercialSectionHintLabel
            label={ANALYTICS_CONTENT.oportunidades.title}
            hint={CM_HELP.analytics.opportunitiesPage}
          />
        }
        description={ANALYTICS_CONTENT.oportunidades.subtitle}
        actions={
          <CommercialActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
            <RefreshCw size={16} aria-hidden="true" /> Atualizar
          </CommercialActionButton>
        }
      >
        <div className="cm-customers-page__panel-toolbar">
          <div className="cm-customers-page__vision">
            <CommercialSectionHintLabel
              label="Visão"
              hint={CM_HELP.analytics.opportunitiesView}
            />
            <CommercialSegmentToggle
              ariaLabel={CM_HELP.analytics.opportunitiesView}
              idPrefix="analytics-opportunities-view"
              value={view}
              widthMode="content"
              onChange={(value) => {
                if (value === "collaborator" || value === "opportunity") {
                  setView(value);
                }
              }}
              options={[
                {
                  value: "collaborator",
                  ariaLabel: "Por colaborador",
                  label: (
                    <span className="cm-customers-page__vision-option">
                      <Users size={16} aria-hidden="true" />
                      Por colaborador
                    </span>
                  ),
                },
                {
                  value: "opportunity",
                  ariaLabel: "Por oportunidade",
                  label: (
                    <span className="cm-customers-page__vision-option">
                      <ListChecks size={16} aria-hidden="true" />
                      Por oportunidade
                    </span>
                  ),
                },
              ]}
            />
          </div>
        </div>
        <AnalyticsFilters
          dateStart={filters.dateStart}
          dateEnd={filters.dateEnd}
          competence={filters.competence}
          periodPreset={filters.periodPreset}
          branches={filters.branches}
          customerSegment={filters.customerSegment}
          sellerIds={filters.sellerIds}
          customerCodes={filters.customerCodes}
          canFilterPortfolios={filters.canFilterPortfolios}
          canUseTeamScope={filters.canUseTeamScope}
          filterablePortfolios={filters.filterablePortfolios}
          onDateStart={filters.setDateStart}
          onDateEnd={filters.setDateEnd}
          onCompetence={filters.setCompetence}
          onPeriodPreset={filters.setPeriodPreset}
          onBranches={filters.setBranches}
          onCustomerSegment={filters.setCustomerSegment}
          onCustomerCodes={filters.setCustomerCodes}
          onSellerIds={filters.setSellerIds}
        />
      </CommercialPageHero>

      {!slaConfigured ? (
        <CommercialEmptyState defaultMessage="SLA de etapa não configurado. Cadastre políticas em settings quando o Comercial homologar prazos." />
      ) : null}

      {view === "collaborator" ? (
        <CommercialSectionCard
          title="Por colaborador"
          hint={CM_HELP.analytics.collaboratorSummary}
        >
          <OpportunityCollaboratorSummaryTable
            rows={collab}
            loading={collabLoading}
            onSellerClick={(sellerCode) => {
              filters.setSellerIds([sellerCode]);
              setView("opportunity");
            }}
          />
        </CommercialSectionCard>
      ) : null}

      {view === "opportunity" ? (
        <>
          <CommercialTextField
            label="Busca"
            hint={CM_HELP.analytics.searchOpportunities}
            value={search}
            onChange={setSearch}
            placeholder="Número da OV, cliente…"
          />
          <CommercialSelectField
            label="Status"
            hint={CM_HELP.analytics.opportunityStatus}
            value={statusFilter || "all"}
            onChange={(value) => setStatusFilter(value === "all" ? "" : value)}
            options={[
              { value: "all", label: "Todos" },
              { value: "open", label: "Abertas" },
              { value: "won", label: "Ganhas" },
              { value: "lost", label: "Perdidas" },
            ]}
          />

          <CommercialSectionCard
            title={`Oportunidades (${total.toLocaleString("pt-BR")})`}
            hint={CM_HELP.analytics.opportunitiesList}
          >
            {loading ? <CommercialLoadingCard title="Carregando…" variant="panel" /> : null}
            {error ? <CommercialEmptyState defaultMessage={error} /> : null}
            {!loading && !error ? (
              <CommercialProposalsTable
                rows={items}
                basePath={basePath}
                detailSearch={buildAnalyticsOpportunityBackSearch()}
                showOpenProposal={canViewProposals}
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSortChange={(columnKey) => {
                  const next = nextTableSortState(sortKey, sortDirection, columnKey);
                  setSortKey(next.sortKey);
                  setSortDirection(next.sortDirection);
                }}
              />
            ) : null}
          </CommercialSectionCard>
        </>
      ) : null}
    </section>
  );
}
