import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { getCommercialProposals } from "../../api/analyticsApi";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialSectionCard,
  CommercialSectionHintLabel,
  CommercialTextField,
} from "../../app/commercialUi";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import { CM_HELP } from "../../content/helpTooltips";
import type { CommercialProposal } from "../../types/analytics";
import { AnalyticsFilters } from "./components/AnalyticsFilters";
import { AnalyticsDeepPagePath } from "./components/AnalyticsDeepPagePath";
import { CommercialProposalsTable } from "./components/CommercialProposalsTable";
import { useAnalyticsFilters } from "./hooks/useAnalyticsFilters";
import {
  buildAnalyticsOpportunityBackSearch,
  readAnalyticsOpportunitySearch,
  subscribeAnalyticsFilterRouteSync,
  writeAnalyticsOpportunitySearchToUrl,
} from "./utils/analyticsFilterUrl";

type AnalyticsOpportunitiesPageProps = {
  basePath: string;
};

export function AnalyticsOpportunitiesPage({ basePath }: AnalyticsOpportunitiesPageProps) {
  const filters = useAnalyticsFilters();
  const [items, setItems] = useState<CommercialProposal[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState(() => readAnalyticsOpportunitySearch());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    writeAnalyticsOpportunitySearchToUrl(search);
  }, [search]);

  useEffect(
    () =>
      subscribeAnalyticsFilterRouteSync(() => {
        setSearch(readAnalyticsOpportunitySearch());
      }),
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void getCommercialProposals(
      {
        ...filters.apiParams,
        page: 1,
        page_size: 50,
        search: search.trim() || undefined,
        sort_by: "proposal_date",
        sort_dir: "desc",
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
    filters.apiParams.start_date,
    filters.apiParams.end_date,
    filters.apiParams.branch,
    filters.apiParams.customer_segment,
    filters.apiParams.seller_id,
    search,
    reloadKey,
  ]);

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
      <AnalyticsFilters
        dateStart={filters.dateStart}
        dateEnd={filters.dateEnd}
        competence={filters.competence}
        branches={filters.branches}
        customerSegment={filters.customerSegment}
        sellerIds={filters.sellerIds}
        canFilterPortfolios={filters.canFilterPortfolios}
        canUseTeamScope={filters.canUseTeamScope}
        filterablePortfolios={filters.filterablePortfolios}
        onDateStart={filters.setDateStart}
        onDateEnd={filters.setDateEnd}
        onCompetence={filters.setCompetence}
        onBranches={filters.setBranches}
        onCustomerSegment={filters.setCustomerSegment}
        onSellerIds={filters.setSellerIds}
      />
      </CommercialPageHero>

      <CommercialTextField
        label="Busca"
        value={search}
        onChange={setSearch}
        placeholder="Número da OV, cliente…"
      />

      <CommercialSectionCard
        title={`Oportunidades (${total.toLocaleString("pt-BR")})`}
        hint={CM_HELP.analytics.opportunitiesList}
      >
        {loading ? <CommercialLoadingCard title="Carregando…" variant="panel" /> : null}
        {error ? (
          <CommercialEmptyState defaultMessage={error} />
        ) : null}
        {!loading && !error ? (
          <CommercialProposalsTable
            rows={items}
            basePath={basePath}
            detailSearch={buildAnalyticsOpportunityBackSearch()}
          />
        ) : null}
      </CommercialSectionCard>
    </section>
  );
}
