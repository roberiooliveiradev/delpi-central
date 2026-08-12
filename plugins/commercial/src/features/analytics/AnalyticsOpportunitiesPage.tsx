import { EmptyState, SectionCard } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { getCommercialProposals } from "../../api/analyticsApi";
import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActionButton,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialTextField,
} from "../../app/commercialUi";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
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
    filters.apiParams.customer_codes,
    search,
    reloadKey,
  ]);

  return (
    <section className="cm-page-stack">
      <AnalyticsDeepPagePath
        basePath={basePath}
        current={ANALYTICS_CONTENT.oportunidades.title}
      />
      <CommercialPageHero
        aria-label={ANALYTICS_CONTENT.oportunidades.title}
        title={ANALYTICS_CONTENT.oportunidades.title}
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
        sellerId={filters.sellerId}
        canFilterPortfolios={filters.canFilterPortfolios}
        canUseTeamScope={filters.canUseTeamScope}
        filterablePortfolios={filters.filterablePortfolios}
        onDateStart={filters.setDateStart}
        onDateEnd={filters.setDateEnd}
        onCompetence={filters.setCompetence}
        onBranches={filters.setBranches}
        onCustomerSegment={filters.setCustomerSegment}
        onSellerId={filters.setSellerId}
      />
      </CommercialPageHero>

      <CommercialTextField
        label="Busca"
        value={search}
        onChange={setSearch}
        placeholder="Número da OV, cliente…"
      />

      <SectionCard
        title={`Oportunidades (${total.toLocaleString("pt-BR")})`}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {loading ? <CommercialLoadingCard title="Carregando…" variant="panel" /> : null}
        {error ? (
          <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
        ) : null}
        {!loading && !error ? (
          <CommercialProposalsTable
            rows={items}
            basePath={basePath}
            detailSearch={buildAnalyticsOpportunityBackSearch()}
          />
        ) : null}
      </SectionCard>
    </section>
  );
}
